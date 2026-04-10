import os
import json
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

def process_with_gemini(api_key: str, inspection_text: str, thermal_text: str, image_paths: List[str]) -> dict:
    """This function is kept named 'process_with_gemini' for backward compatibility in app.py, but now calls Groq."""
    
    client = Groq(api_key=api_key)
    
    available_images_list = [os.path.basename(p) for p in image_paths if os.path.exists(p)]
    images_str = ", ".join(available_images_list)
    
    prompt = f"""
You are an expert Civil Engineer, Master Thermographer, and Technical Diagnostic Report Generator.
You are given the extracted text from two documents: an Inspection Report and a Thermal Report.
Crucially, during text extraction, we inserted markers such as [IMAGE_REFERENCE: filename] exactly where images appeared in the original documents.

Your objective is to assimilate both sources of data, logically link the text observations with their nearby image references, and generate a complete Detailed Diagnostic Report (DDR) in valid JSON format.

Important Rules for Processing:
1. COMBINE DATA: Intelligently cross-reference the defects described in the text with the nearest [IMAGE_REFERENCE: filename]. 
2. If the text mentions a defect (e.g. "massive crack") and an [IMAGE_REFERENCE: insp_crack.jpg] appears near it, you MUST assign that filename to the relevant_image_filenames list for that exact observation.
3. Treat the [IMAGE_REFERENCE: filename] markers as contextual visual evidence locations.
4. Avoid duplicate points.
5. If information conflicts -> mention the conflict explicitly. 
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
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_completion_tokens=2048,
        response_format={"type": "json_object"}
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": f"Failed to parse Groq JSON: {str(e)}", "raw": response.choices[0].message.content}
