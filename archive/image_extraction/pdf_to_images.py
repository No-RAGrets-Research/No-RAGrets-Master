from pdf2image import convert_from_path
from pathlib import Path
import sys

def convert_pdf_to_images(pdf_path: str, out_dir: str, dpi: int = 300, format: str = "PNG") -> list:
    """
    Convert PDF pages to individual image files for OCR processing.
    
    Args:
        pdf_path: Path to PDF file
        out_dir: Output directory for images
        dpi: Resolution for conversion (higher = better quality)
        format: Image format (PNG, JPEG, etc.)
    
    Returns:
        List of image file paths
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Converting PDF to images...")
    print(f"Input: {pdf_path}")
    print(f"Output: {out_dir}")
    print(f"DPI: {dpi}")
    print(f"Format: {format}")
    print("=" * 50)
    
    # Convert PDF to images
    try:
        pages = convert_from_path(pdf_path, dpi=dpi)
        print(f"Successfully converted {len(pages)} pages")
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return []
    
    image_files = []
    
    # Save each page as an image
    for page_num, page_image in enumerate(pages):
        # Create filename: page_001.png, page_002.png, etc.
        filename = f"page_{page_num+1:03d}.{format.lower()}"
        image_path = Path(out_dir, filename)
        
        try:
            # Save image
            if format.upper() == "JPEG" or format.upper() == "JPG":
                # JPEG doesn't support transparency, so convert RGBA to RGB
                if page_image.mode == "RGBA":
                    page_image = page_image.convert("RGB")
                page_image.save(image_path, format, quality=95)
            else:
                page_image.save(image_path, format)
            
            image_files.append(str(image_path))
            print(f"  Saved: {filename}")
            
        except Exception as e:
            print(f"  Error saving page {page_num+1}: {e}")
    
    print("=" * 50)
    print(f"Conversion complete!")
    print(f"Created {len(image_files)} image files in {out_dir}")
    
    return image_files

def print_usage():
    """Print usage instructions."""
    print("PDF to Images Converter")
    print("=" * 50)
    print("Usage: python pdf_to_images.py <pdf_path> [output_dir] [dpi] [format]")
    print()
    print("Parameters:")
    print("  pdf_path    : Path to PDF file (required)")
    print("  output_dir  : Output directory (default: 'pdf_images')")
    print("  dpi         : Image resolution 150-600 (default: 300)")
    print("  format      : Image format PNG/JPEG (default: PNG)")
    print()
    print("Examples:")
    print("  python pdf_to_images.py 'paper.pdf'")
    print("  python pdf_to_images.py 'paper.pdf' my_images")
    print("  python pdf_to_images.py 'paper.pdf' my_images 400 JPEG")
    print()
    print("Output:")
    print("  Creates numbered image files: page_001.png, page_002.png, etc.")
    print("  Higher DPI = better quality but larger files")
    print("  PNG = lossless, JPEG = smaller files")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "pdf_images"
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    format = sys.argv[4] if len(sys.argv) > 4 else "PNG"
    
    # Validate inputs
    if not Path(pdf_path).exists():
        print(f"Error: PDF file '{pdf_path}' not found")
        sys.exit(1)
    
    if dpi < 150 or dpi > 600:
        print(f"Warning: DPI {dpi} is outside recommended range 150-600")
    
    if format.upper() not in ["PNG", "JPEG", "JPG"]:
        print(f"Warning: Format '{format}' may not be supported. Recommended: PNG or JPEG")
    
    # Convert PDF to images
    image_files = convert_pdf_to_images(pdf_path, out_dir, dpi, format)
    
    if image_files:
        print()
        print("Next steps for DeepSeek OCR:")
        print("=" * 50)
        print("1. Use the individual image files with DeepSeek OCR:")
        print(f"   Image files are in: {out_dir}/")
        print("   Files: page_001.png, page_002.png, etc.")
        print()
        print("2. Example DeepSeek OCR usage for each image:")
        print("   from transformers import AutoModel, AutoTokenizer")
        print("   # ... load model ...")
        print(f"   image_file = '{out_dir}/page_001.png'")
        print("   prompt = '<image>\\n<|grounding|>Convert the document to markdown.'")
        print("   res = model.infer(tokenizer, prompt=prompt, image_file=image_file, ...)")
        print()
        print("3. Process each image file individually with DeepSeek OCR")
    else:
        print("No images were created. Check the error messages above.")
        sys.exit(1)