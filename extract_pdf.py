
import os
import sys

# Try to import pymupdf, if not, try to install it user permitting, or fall back
try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF (fitz) not found. Please install it using: pip install pymupdf")
    sys.exit(1)

def extract_pdf_content(pdf_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    doc = fitz.open(pdf_path)
    output_md_path = os.path.join(output_dir, "content.md")
    images_dir = os.path.join(output_dir, "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    md_content = f"# Extracted Content from {os.path.basename(pdf_path)}\n\n"
    html_content = "<html><body>"

    for page_index, page in enumerate(doc):
        md_content += f"## Page {page_index + 1}\n\n"
        html_content += f"<!-- Page {page_index + 1} -->\n"
        
        # HTML Extraction for Richer Structure
        try:
            page_html = page.get_text("html")
            html_content += page_html + "\n<hr>\n"
        except Exception:
            html_content += f"<p>Error extracting HTML for page {page_index+1}</p>"

        # Text/Block Extraction for readable Markdown
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0])) # Sort by vertical then horizontal

        for b in blocks:
            # b format: (x0, y0, x1, y1, "lines\n", block_no, block_type)
            # block_type: 0 = text, 1 = image
            if b[6] == 0:
                text = b[4]
                md_content += text + "\n\n"
            elif b[6] == 1:
                md_content += f"[Image/Block found at {b[0:4]}]\n\n"
        
        # Extract images (same as before)
        image_list = page.get_images(full=True)
        if image_list:
            md_content += "**Images on this page:**\n\n"
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"page{page_index + 1}_img{img_index + 1}.{image_ext}"
            image_filepath = os.path.join(images_dir, image_filename)
            
            # Save image
            if not os.path.exists(image_filepath): # Avoid re-saving if exists/overwrite
                with open(image_filepath, "wb") as f:
                    f.write(image_bytes)
            
            md_content += f"![{image_filename}](images/{image_filename})\n\n"
            
    html_content += "</body></html>"
    
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    output_html_path = os.path.join(output_dir, "content.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Extraction complete. Content saved to {output_md_path} and {output_html_path}")

if __name__ == "__main__":
    pdf_file = "2025___AI_Universe_25_Shutdown_ARXIV (5).pdf"
    if not os.path.exists(pdf_file):
        print(f"Error: {pdf_file} not found.")
    else:
        extract_pdf_content(pdf_file, "extracted_content")
