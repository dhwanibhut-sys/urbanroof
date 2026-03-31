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
    
    # We will pass the filenames of available images so Llama knows they exist.
    available_images_list = [os.path.basename(p) for p in image_paths if os.path.exists(p)]
    images_str = ", ".join(available_images_list)
    
    prompt = f"""
You are an expert Applied AI Builder and Technical Diagnostic Report Generator.
You are given the extracted text from two documents: an Inspection Report and a Thermal Report.
We have also extracted images with markers in the text (e.g. [IMAGE_REFERENCE: filename]).

Your objective is to assimilate both sources of data to generate a complete Detailed Diagnostic Report (DDR) in valid JSON format.

Important Rules:
- Extract relevant observations intelligently. Combine information logically.
- Avoid duplicate points.
- Do NOT invent facts not present in the documents.
- If information conflicts -> mention the conflict.
- If expected information is missing -> write "Not Available".
- Use simple, client-friendly language. Avoid unnecessary technical jargon.
- Accurately assign relevant image filenames to the specific observation they belong to. Do NOT attach images to unrelated observations. 
- Ensure you output ONLY valid JSON matching the schema below.

--- DATA ---
AVAILABLE IMAGE FILENAMES EXTRACTED:
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
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.1,
        max_completion_tokens=2048,
        response_format={"type": "json_object"}
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": f"Failed to parse Groq JSON: {str(e)}", "raw": response.choices[0].message.content}
