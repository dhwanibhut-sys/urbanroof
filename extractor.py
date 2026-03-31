import fitz  # PyMuPDF
import os
from PIL import Image
import io

def extract_pdf_data(pdf_path, output_dir, doc_id="doc"):
    text_content = ""
    image_paths = []

    os.makedirs(output_dir, exist_ok=True)
    
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_content += f"\n--- Page {page_num + 1} ---\n"
            text_content += page.get_text("text")
            
            # Extract images
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Conversion to PNG if needed for consistency
                if image_ext.lower() not in ["png", "jpeg", "jpg"]:
                    try:
                        im = Image.open(io.BytesIO(image_bytes))
                        out_bytes = io.BytesIO()
                        if im.mode in ("RGBA", "P"):
                            im = im.convert("RGB")
                        im.save(out_bytes, format="PNG")
                        image_bytes = out_bytes.getvalue()
                        image_ext = "png"
                    except Exception as e:
                        print(f"Failed to convert image {xref}: {e}")
                        pass

                image_name = f"{doc_id}_p{page_num+1}_img{img_index}.{image_ext}"
                image_path = os.path.join(output_dir, image_name)
                
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                image_paths.append(image_path)
                
                # Add a marker in text to give LLM context of where the image originates
                text_content += f"\n[IMAGE_REFERENCE: {image_name}]\n"
                
    except Exception as e:
        text_content += f"\nError reading PDF {pdf_path}: {str(e)}\n"
        
    return text_content, image_paths

def extract_docx_data(docx_path, output_dir, doc_id="doc"):
    import docx
    text_content = ""
    image_paths = []
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        doc = docx.Document(docx_path)
        img_index = 0
        
        for para in doc.paragraphs:
            text_content += para.text + "\n"
        
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                image_bytes = rel.target_part.blob
                image_name = f"{doc_id}_docx_img{img_index}.png"
                image_path = os.path.join(output_dir, image_name)
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                image_paths.append(image_path)
                
                # Append reference
                text_content += f"\n[IMAGE_REFERENCE: {image_name}]\n"
                img_index += 1
                
    except Exception as e:
        text_content += f"\nError reading DOCX {docx_path}: {str(e)}\n"
        
    return text_content, image_paths

def extract_document(file_path, output_dir, doc_id):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_pdf_data(file_path, output_dir, doc_id)
    elif ext in [".docx", ".doc"]:
        return extract_docx_data(file_path, output_dir, doc_id)
    else:
        return f"\nUnsupported format {ext} for document {doc_id}\n", []
