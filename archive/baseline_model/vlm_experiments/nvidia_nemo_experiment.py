#!/usr/bin/env python3
"""
NVIDIA NeMo Retriever Parse Experiment Script

This script tests the NVIDIA NeMo Retriever Parse API for document processing.
NeMo offers multiple processing modes for different use cases.

NVIDIA NeMo Retriever Parse provides:
- Image-based document analysis (requires PDF-to-image conversion)
- Three processing modes: markdown_bbox, markdown_no_bbox, detection_only
- Context limit: 3584 tokens
- API-based processing

Author: Generated for VLM experiments
Date: October 2024
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
import time
import base64
import io
from PIL import Image
import fitz  # PyMuPDF

# Add the src directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

def pdf_to_images(pdf_path, output_dir, dpi=150, format='JPEG'):
    """
    Convert PDF pages to images
    
    Args:
        pdf_path (str): Path to PDF file
        output_dir (str): Directory to save images
        dpi (int): Resolution for conversion
        format (str): Image format (JPEG or PNG)
    
    Returns:
        list: List of image file paths
    """
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    pdf_document = fitz.open(pdf_path)
    image_paths = []
    
    print(f"Converting PDF to images ({dpi} DPI, {format})...")
    
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        
        # Create matrix for higher resolution
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        
        # Save as JPEG or PNG
        image_path = output_dir / f"page_{page_num + 1:03d}.{format.lower()}"
        
        if format.upper() == 'JPEG':
            img = img.convert('RGB')  # Remove alpha channel for JPEG
            img.save(image_path, format='JPEG', quality=95)
        else:
            img.save(image_path, format=format)
        
        image_paths.append(str(image_path))
        print(f"Saved page {page_num + 1} as {image_path}")
    
    pdf_document.close()
    return image_paths

def test_nvidia_nemo_api(image_path, api_key, mode="markdown_bbox"):
    """
    Test NVIDIA NeMo Retriever Parse API with an image
    
    Args:
        image_path (str): Path to the image file
        api_key (str): NVIDIA API key
        mode (str): Processing mode (markdown_bbox, markdown_no_bbox, detection_only)
    
    Returns:
        dict: API response data
    """
    
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable not set")
    
    # API endpoint
    url = "https://ai.api.nvidia.com/v1/vision/nvidia/nemo-retriever-parsing"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    # Read and encode the image
    with open(image_path, 'rb') as f:
        image_content = f.read()
    
    image_base64 = base64.b64encode(image_content).decode('utf-8')
    
    # Determine MIME type
    if image_path.lower().endswith('.png'):
        mime_type = "image/png"
    elif image_path.lower().endswith(('.jpg', '.jpeg')):
        mime_type = "image/jpeg"
    else:
        mime_type = "image/jpeg"  # Default
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": f'<img src="data:{mime_type};base64,{image_base64}" />'
            }
        ],
        "max_tokens": 2048,  # Reduced to stay under 3584 token limit
        "temperature": 0.0,
        "top_p": 1.0,
        "stream": False,
        "model": f"nvidia/nemo-retriever-parsing:{mode}"
    }
    
    print(f"Sending request to NVIDIA NeMo (mode: {mode})...")
    print(f"Image: {Path(image_path).name}")
    print(f"Image size: {len(image_content)} bytes")
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
        response.raise_for_status()

def test_nvidia_nemo_document(pdf_path, api_key, modes=None):
    """
    Test NVIDIA NeMo with full document across multiple modes
    
    Args:
        pdf_path (str): Path to PDF file
        api_key (str): NVIDIA API key
        modes (list): List of modes to test
    
    Returns:
        dict: Combined results from all modes
    """
    
    if modes is None:
        modes = ["markdown_bbox", "markdown_no_bbox", "detection_only"]
    
    # Create temporary directory for images
    temp_dir = Path(pdf_path).parent / "temp_images"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Convert PDF to images
        image_paths = pdf_to_images(pdf_path, temp_dir, dpi=150, format='JPEG')
        
        results = {
            "document_info": {
                "pdf_path": str(pdf_path),
                "total_pages": len(image_paths),
                "processing_timestamp": datetime.now().isoformat()
            },
            "modes": {}
        }
        
        # Test each mode
        for mode in modes:
            print(f"\n--- Testing mode: {mode} ---")
            mode_results = {
                "mode": mode,
                "pages": [],
                "total_content": "",
                "processing_time": 0
            }
            
            start_time = time.time()
            
            # Process each page
            for i, image_path in enumerate(image_paths):
                try:
                    page_result = test_nvidia_nemo_api(image_path, api_key, mode)
                    
                    # Extract content from response
                    if 'choices' in page_result and len(page_result['choices']) > 0:
                        content = page_result['choices'][0].get('message', {}).get('content', '')
                    else:
                        content = str(page_result)
                    
                    page_data = {
                        "page_number": i + 1,
                        "content": content,
                        "image_path": image_path,
                        "response": page_result
                    }
                    
                    mode_results["pages"].append(page_data)
                    mode_results["total_content"] += content + "\n\n"
                    
                    print(f"Page {i + 1}: {len(content)} characters extracted")
                    
                    # Small delay to avoid rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error processing page {i + 1} with mode {mode}: {e}")
                    continue
            
            end_time = time.time()
            mode_results["processing_time"] = end_time - start_time
            
            results["modes"][mode] = mode_results
            
            print(f"Mode {mode} completed: {len(mode_results['total_content'])} total characters")
    
    finally:
        # Clean up temporary images
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")
    
    return results

def analyze_nvidia_nemo_response(response_data, output_file):
    """
    Analyze the NVIDIA NeMo response and generate metrics
    
    Args:
        response_data (dict): API response
        output_file (str): Path to save analysis
    """
    
    doc_info = response_data.get('document_info', {})
    modes_data = response_data.get('modes', {})
    
    total_pages = doc_info.get('total_pages', 0)
    
    analysis = f"""# NVIDIA NeMo Retriever Parse Analysis Report

## Document Overview
- **PDF Path**: {doc_info.get('pdf_path', 'Unknown')}
- **Total Pages**: {total_pages}
- **Processing Date**: {doc_info.get('processing_timestamp', 'Unknown')}
- **Modes Tested**: {len(modes_data)}

## Mode Comparison
"""
    
    # Analyze each mode
    for mode_name, mode_data in modes_data.items():
        content = mode_data.get('total_content', '')
        char_count = len(content)
        word_count = len(content.split()) if content else 0
        processing_time = mode_data.get('processing_time', 0)
        pages_processed = len(mode_data.get('pages', []))
        
        # Estimate chunks
        estimated_chunks = char_count // 400 if char_count > 0 else 0
        
        analysis += f"""
### Mode: {mode_name}
- **Characters Extracted**: {char_count:,}
- **Words Extracted**: {word_count:,}
- **Estimated Chunks**: {estimated_chunks}
- **Pages Processed**: {pages_processed}/{total_pages}
- **Processing Time**: {processing_time:.2f} seconds
- **Characters per Second**: {char_count / processing_time if processing_time > 0 else 0:,.0f}
"""
    
    # Overall analysis
    best_mode = max(modes_data.keys(), 
                   key=lambda m: len(modes_data[m].get('total_content', ''))) if modes_data else None
    
    analysis += f"""
## Key Features
- Image-based document analysis
- Multiple processing modes available
- API-based processing
- Context limit: 3584 tokens

## Technical Details
- **Input**: PDF converted to images (150 DPI JPEG)
- **API**: NVIDIA NeMo Retriever Parse
- **Max Tokens**: 2048 (to stay under 3584 limit)
- **Processing**: Page-by-page image analysis

## Mode Descriptions
- **markdown_bbox**: Markdown with bounding box information
- **markdown_no_bbox**: Clean markdown without coordinates  
- **detection_only**: Element detection without full text

## Performance Summary
- **Best Mode (by content)**: {best_mode or 'N/A'}
- **Total Processing Time**: {sum(m.get('processing_time', 0) for m in modes_data.values()):.2f} seconds
- **Average Time per Page**: {sum(m.get('processing_time', 0) for m in modes_data.values()) / total_pages if total_pages > 0 else 0:.2f} seconds
"""
    
    # Sample content from best mode
    if best_mode and modes_data[best_mode].get('total_content'):
        sample_content = modes_data[best_mode]['total_content'][:500]
        analysis += f"""
## Sample Content (from {best_mode})
```
{sample_content}...
```
"""
    
    with open(output_file, 'w') as f:
        f.write(analysis)
    
    print(f"Analysis saved to: {output_file}")
    if best_mode:
        best_content = modes_data[best_mode].get('total_content', '')
        print(f"Best mode ({best_mode}): {len(best_content):,} characters")

def main():
    """Main function to run the NVIDIA NeMo experiment"""
    
    # Get API key from environment
    api_key = os.getenv('NVIDIA_API_KEY')
    
    if not api_key:
        print("Error: NVIDIA_API_KEY environment variable not set")
        print("Please set your NVIDIA API key:")
        print("export NVIDIA_API_KEY='your_api_key_here'")
        return
    
    # Define paths
    script_dir = Path(__file__).parent
    pdf_path = script_dir / "papers" / "Baldo et al. 2024.pdf"
    
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return
    
    # Generate timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_name = pdf_path.stem
    
    output_json = script_dir / f"nvidia_nemo_output_{pdf_name}_{timestamp}.json"
    analysis_file = script_dir / f"nvidia_nemo_output_{pdf_name}_{timestamp}_analysis.md"
    
    try:
        print(f"Starting NVIDIA NeMo Retriever Parse experiment...")
        print(f"Processing: {pdf_path}")
        
        # Test NVIDIA NeMo with all modes
        modes = ["markdown_bbox", "markdown_no_bbox", "detection_only"]
        response_data = test_nvidia_nemo_document(pdf_path, api_key, modes)
        
        # Save response
        with open(output_json, 'w') as f:
            json.dump(response_data, f, indent=2)
        
        print(f"Response saved to: {output_json}")
        
        # Analyze response
        analyze_nvidia_nemo_response(response_data, analysis_file)
        
        print("\nNVIDIA NeMo experiment completed successfully!")
        print("Check the generated files for detailed results.")
        
    except Exception as e:
        print(f"Error during experiment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()