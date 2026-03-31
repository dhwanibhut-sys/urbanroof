# Applied AI Builder - DDR Generation System

A Streamlit-based web application that converts technical inspection data (Inspection Reports and Thermal Reports) into structured, client-ready Detailed Diagnostic Reports (DDR).

## Features
- **Multimodal Data Extraction**: Extracts BOTH text and embedded images from PDF/DOCX reports.
- **AI Processing via Gemini 1.5 Pro**: Effectively comprehends and links thermal signatures and inspection textual points logically.
- **DDR Structure Adherence**: Avoids duplicates, properly notes conflicting findings, explicitly tags missing data ("Not Available").
- **Image Referencing Engine**: Naturally places relevant images exactly underneath their corresponding area-wise observations.

## Prerequisites
- Python 3.9 or higher
- A Google Gemini API Key (`genai.GenerativeModel('models/gemini-1.5-pro')` or similar generation API key)

## Setup and Installation

1. Create a Python Virtual Environment (recommended):
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the Streamlit server:
```bash
streamlit run app.py
```

2. Access the application at `http://localhost:8501`.
3. Enter your **Gemini API Key** in the sidebar.
4. Upload your two documents (`Inspection Report` and `Thermal Report`).
5. Click **Generate DDR**.

## Limitations & Improvements
- *Processing Time*: Depending on document sizes, the multi-modal LLM reasoning might take up to 30 seconds to accurately process and infer links across both documents.
- *LLM Reliability*: Since "gemini-1.5-pro" structured output aims for highest format fidelity, overly large reports might require chunking to remain within exact JSON schema validation.

## Author 
Completed for the AI Generalist Assignment.
