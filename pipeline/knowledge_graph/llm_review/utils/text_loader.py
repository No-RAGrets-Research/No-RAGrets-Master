from docling.document_converter import DocumentConverter
import os
import json

def load_paper(pdf_path, export_dir="outputs"):
    """
    Load and convert a PDF paper to markdown format.
    
    Args:
        pdf_path: Path to PDF file
        export_dir: Directory to save exported markdown and JSON
    
    Returns:
        str: Markdown text of the paper
    """
    converter = DocumentConverter()
    result = converter.convert(pdf_path)

    # Ensure output directory exists
    os.makedirs(export_dir, exist_ok=True)

    # Extract filename
    name = pdf_path.split("/")[-1].rsplit(".", 1)[0]
    md_path = f"{export_dir}/{name}.md"
    json_path = f"{export_dir}/{name}.json"

    # Export Markdown
    with open(md_path, "w", encoding="utf-8") as f_md:
        f_md.write(result.document.export_to_markdown())

    # Export JSON
    doc_dict = result.document.export_to_dict()
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(doc_dict, f_json, ensure_ascii=False, indent=2)

    # Return extracted text for LLM use
    return result.document.export_to_markdown()

def load_paper_text(pdf_filename, papers_dir="papers"):
    """
    Load paper text from PDF file for LLM review.
    
    Args:
        pdf_filename: Name of PDF file (looks in papers_dir)
        papers_dir: Directory containing PDF files
    
    Returns:
        str: Markdown text of the paper
    """
    # Construct full path
    pdf_path = os.path.join(papers_dir, pdf_filename)
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Convert and return text
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    
    return result.document.export_to_markdown()

