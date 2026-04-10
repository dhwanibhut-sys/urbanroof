import os
import json
import base64
from pydantic import BaseModel, Field
from typing import List
from groq import Groq

class Observation(BaseModel):
    area: str = Field(description="The specific area or room where the observation was made (e.g., Living Room Roof, Southwest Corner, etc.)")
    observation_text: str = Field(description="Detailed text describing the observation.")
    relevant_image_filenames: List[str] = Field(
        description="List of exact image filenames that support this observation based on the inputted files (e.g., ['insp_p1_img0.png'])."
    )

class DDRResult(BaseModel):
    property_issue_summary: str = Field(description="A high level summary of the overall condition and main issues found.")
    area_wise_observations: List[Observation] = Field(description="List of all observations categorized by area.")
    probable_root_cause: str = Field(description="The probable root cause(s) for the main issues.")
    severity_assessment: str = Field(description="Severity Assessment with reasoning (e.g., High, Medium, Low).")
    recommended_actions: str = Field(description="List of recommended actions to resolve the issues.")
    additional_notes: str = Field(description="Any additional notes or factors.")
    missing_information: str = Field(description="Explicitly detail missing or unclear information, specify 'Not Available' if something expected is missing.")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_with_gemini(api_key: str, inspection_text: str, thermal_text: str, image_paths: List[str]) -> dict:
    """This function is kept named 'process_with_gemini' for backward compatibility in app.py, but now calls Groq."""
    
    client = Groq(api_key=api_key)
    
    available_images_list = [os.path.basename(p) for p in image_paths if os.path.exists(p)]
    images_str = ", ".join(available_images_list)
    
    prompt = f"""
You are an expert Civil Engineer, Master Thermographer, and Technical Diagnostic Report Generator.
You are given the extracted text from two documents: an Inspection Report and a Thermal Report.
We have also extracted images with markers in the text (e.g. [IMAGE_REFERENCE: filename]).
You HAVE access to the high-resolution visual contents of the actual images themselves.

Your objective is to assimilate both sources of data, perform deep visual analysis on the real-world images over text, and generate a complete Detailed Diagnostic Report (DDR) in valid JSON format.

Important Rules for Image Processing:
1. DEEP VISUAL ANALYSIS: Assume the images are real-world site evidence. Look VERY closely for visual nuances:
   - Identify water damage, pooling, peeling paint, blockages, rust, or structural cracks in visual images.
   - Look for sharp temperature gradients, thermal bridging, and suspected heat loss or subsurface water in thermal (IR) scans.
2. COMBINE DATA: Intelligently cross-reference the visual defects you see with the extracted text. If an image clearly shows an issue (like a massive crack), state it confidently and use it to clarify vague text.
3. Treat the images as primary sources of truth! If the text says "looks okay visually" but the image shows a defect, prioritize the visual evidence and note the discrepancy.
4. Avoid duplicate points.
5. If information conflicts between text and images -> mention the conflict explicitly. 
6. If expected information is missing -> write "Not Available".
7. Use simple, client-friendly language. Avoid unnecessary technical jargon.
8. Accurately map relevant image filenames to their exact observations. Do NOT attach images to unrelated observations.
9. Ensure you output ONLY valid JSON matching the schema below.

--- DATA ---
AVAILABLE IMAGE FILENAMES EXTRACTED (In order):
{images_str}

INSPECTION REPORT TEXT:
{inspection_text}

THERMAL REPORT TEXT:
{thermal_text}

--- SCHEMA REQUIREMENTS ---
Output the data strictly adhering to the following JSON structure exactly:
{{
  "property_issue_summary": "string",
  "area_wise_observations": [
    {{
      "area": "string",
      "observation_text": "string",
      "relevant_image_filenames": ["string1", "string2"]
    }}
  ],
  "probable_root_cause": "string",
  "severity_assessment": "string",
  "recommended_actions": "string",
  "additional_notes": "string",
  "missing_information": "string"
}}
    """
    
    # Construct Multimodal Messages
    content_list = [{"type": "text", "text": prompt}]
    
    mapping_text = "\n\n--- IMAGE ATTACHMENT MAPPING ---\n"
    for idx, img_path in enumerate(image_paths):
        if os.path.exists(img_path):
            base64_image = encode_image(img_path)
            
            # Determine extension
            ext = os.path.splitext(img_path)[1].lower().replace(".", "")
            if ext == "jpg": ext = "jpeg"
            if ext not in ["jpeg", "png", "gif", "webp"]:
                ext = "png" # fallback default
            
            img_filename = os.path.basename(img_path)
            mapping_text += f"- Visual Attachment #{idx + 1} corresponds to filename: {img_filename}\n"
            
            content_list.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{ext};base64,{base64_image}"
                }
            })
    
    content_list[0]["text"] += mapping_text

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": content_list,
            }
        ],
        model="llama-3.2-90b-vision-preview",
        temperature=0.1,
        max_completion_tokens=2048,
    )
    
    response_content = response.choices[0].message.content
    try:
        # Llama 3.2 vision might wrap output in ```json ... ``` since response_format JSON obj is unsupported currently for multimodal on groq in some edges cases
        if "```json" in response_content:
            response_content = response_content.split("```json")[1].split("```")[0].strip()
        elif "```" in response_content:
            response_content = response_content.split("```")[1].strip()
            
        return json.loads(response_content)
    except Exception as e:
        return {"error": f"Failed to parse Groq JSON: {str(e)}", "raw": response.choices[0].message.content}
