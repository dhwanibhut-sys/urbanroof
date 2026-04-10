import streamlit as st
import os
import shutil
from extractor import extract_document
from llm_processor import process_with_gemini

st.set_page_config(page_title="DDR Generation System", layout="wide")

# Inject custom CSS to make buttons look more standard/enterprise and less "Streamlit default"
st.markdown("""
    <style>
    .stButton > button {
        border-radius: 4px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Detailed Diagnostic Report System")
st.markdown("Upload Inspection and Thermal data to synthesize a standardized diagnostic report.")

import os
try:
    with open(os.path.join(os.path.dirname(__file__), 'config.py'), 'r') as f:
        API_KEY = f.read().split('=')[1].strip().strip('\"').strip('\'')
except Exception as e:
    API_KEY = ""

# API Key input
api_key = API_KEY
if not api_key:
    api_key = st.sidebar.text_input("Enter your Groq API Key", type="password")
else:
    st.sidebar.success("✅ Secure Groq API Key Loaded Internally")
st.sidebar.markdown("Core Processing Engine: `llama-3.3-70b-versatile`")

col1, col2 = st.columns(2)
with col1:
    inspection_file = st.file_uploader("Upload Inspection Report (PDF/DOCX)", type=['pdf', 'docx', 'doc'])
with col2:
    thermal_file = st.file_uploader("Upload Thermal Report (PDF/DOCX)", type=['pdf', 'docx', 'doc'])

if st.button("Generate Report", type="primary"):
    if not api_key:
        st.error("Please enter your Groq API Key in the sidebar.")
    elif not inspection_file or not thermal_file:
        st.error("Please upload both the Inspection Report and the Thermal Report.")
    else:
        with st.spinner("Processing Documents..."):
            temp_dir = "temp_processing"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            insp_path = os.path.join(temp_dir, "inspection" + os.path.splitext(inspection_file.name)[1])
            with open(insp_path, "wb") as f:
                f.write(inspection_file.getbuffer())
                
            therm_path = os.path.join(temp_dir, "thermal" + os.path.splitext(thermal_file.name)[1])
            with open(therm_path, "wb") as f:
                f.write(thermal_file.getbuffer())
                
            st.info("Extracting textual content and images from Inspection Report...")
            insp_text, insp_images = extract_document(insp_path, temp_dir, "insp")
            
            st.info("Extracting textual content and images from Thermal Report...")
            therm_text, therm_images = extract_document(therm_path, temp_dir, "therm")
            
            all_images = insp_images + therm_images
            if not isinstance(all_images, list): all_images = []
            
            st.info("Synthesizing Report...")
            start_time = st.session_state.get('start_time', 0)
            try:
                result = process_with_gemini(api_key, insp_text, therm_text, all_images)
            except Exception as e:
                st.error(f"Error communicating with Groq API: {str(e)}")
                result = None
                
            if result:
                if "error" in result:
                    st.error("AI Error: " + result["error"])
                    st.json(result)
                else:
                    st.success("Report Generated Successfully")
                    
                    # Render final report nicely
                    st.markdown("---")
                    st.header("Detailed Diagnostic Report")
                    
                    st.subheader("1. Property Issue Summary")
                    st.write(result.get("property_issue_summary", "Not Available"))
                    
                    st.subheader("2. Area-wise Observations")
                    observations = result.get("area_wise_observations", [])
                    if not observations:
                        st.write("Not Available")
                    for obs in observations:
                        with st.container():
                            st.markdown(f"#### {obs.get('area', 'Not Available')}")
                            st.write(obs.get('observation_text', ''))
                            
                            images = obs.get("relevant_image_filenames", [])
                            if images:
                                # cap images per row
                                cols = st.columns(min(len(images), 4))
                                col_idx = 0
                                for img_name in images:
                                    img_path = os.path.join(temp_dir, img_name)
                                    if os.path.exists(img_path):
                                        cols[col_idx % 4].image(img_path, caption=img_name, use_container_width=True)
                                    else:
                                        cols[col_idx % 4].warning(f"Image Not Available: {img_name}")
                                    col_idx += 1
                            else:
                                st.caption("*Image Not Available*")
                            st.markdown("---")
                    
                    st.subheader("3. Probable Root Cause")
                    st.write(result.get("probable_root_cause", "Not Available"))
                    
                    st.subheader("4. Severity Assessment")
                    st.write(result.get("severity_assessment", "Not Available"))
                    
                    st.subheader("5. Recommended Actions")
                    st.write(result.get("recommended_actions", "Not Available"))
                    
                    st.subheader("6. Additional Notes")
                    st.write(result.get("additional_notes", "Not Available"))
                    
                    st.subheader("7. Missing or Unclear Information")
                    st.write(result.get("missing_information", "Not Available"))
