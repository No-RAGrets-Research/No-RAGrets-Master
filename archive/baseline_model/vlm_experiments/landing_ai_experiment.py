#!/usr/bin/env python3import os

"""import json

Landing AI ADE Experiment Scriptimport requests

from dotenv import load_dotenv

This script tests the Landing AI Application Development Engine (ADE)from pathlib import Path

for document processing and analysis, specifically focusing on scientific papers.from datetime import datetime



Landing AI ADE provides:# Load environment variables from .env file

- API-based multimodal document analysisload_dotenv()

- Detailed figure and image descriptions

- Text extraction with contextual understanding# Access the Landing AI API key

- First 1000 API calls are freeLANDING_AI_API_KEY = os.getenv('LANDING_AI_API_KEY')



Author: Generated for VLM experiments# to debug access issues

Date: October 2024#print(f"Loaded LANDING_AI_API_KEY: {LANDING_AI_API_KEY}")

"""

# Find the first PDF in papers directory

import ospapers_dir = Path("papers")

import syspdf_files = list(papers_dir.glob("*.pdf"))

import json

import requestsif not pdf_files:

from datetime import datetime    print("No PDF files found in vlm_experiments/papers/")

from pathlib import Path    exit()

import time

pdf_path = pdf_files[0]

# Add the src directory to Python path for importsprint(f"Using PDF: {pdf_path.name}")

sys.path.append(str(Path(__file__).parent.parent / "src"))

# Test the API call

def test_landing_ai_ade(pdf_path, api_key):headers = {"Authorization": f"Bearer {LANDING_AI_API_KEY}"}

    """with open(pdf_path, "rb") as pdf_file:

    Test Landing AI ADE API with a PDF document    files = {"document": pdf_file}

        response = requests.post("https://api.va.landing.ai/v1/ade/parse", headers=headers, files=files)

    Args:

        pdf_path (str): Path to the PDF fileprint(f"Status code: {response.status_code}")

        api_key (str): Landing AI API key

    if response.status_code == 200:

    Returns:    response_data = response.json()

        dict: API response data    

    """    # Print what we got back

        print(f"Response keys: {list(response_data.keys())}")

    if not api_key:    

        raise ValueError("LANDING_AI_API_KEY environment variable not set")    # Save the full response to JSON

        output_file = f"landing_ai_output_{pdf_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # API endpoint    with open(output_file, 'w', encoding='utf-8') as f:

    url = "https://preview.landing.ai/api/v1/vision/document-analysis"        json.dump(response_data, f, indent=2, ensure_ascii=False)

        

    headers = {    print(f"Full response saved to: {output_file}")

        "Authorization": f"Bearer {api_key}",    

        "Content-Type": "application/json"    # Show brief preview of each data type

    }    for key in response_data.keys():

            value = response_data[key]

    # Read and encode the PDF        if isinstance(value, str):

    with open(pdf_path, 'rb') as f:            preview = value[:200] + "..." if len(value) > 200 else value

        pdf_content = f.read()            print(f"\n{key} (string, {len(value)} chars): {preview}")

            elif isinstance(value, list):

    import base64            print(f"\n{key} (list, {len(value)} items): {value[:2] if len(value) > 2 else value}")

    pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')        elif isinstance(value, dict):

                print(f"\n{key} (dict): {list(value.keys())}")

    payload = {        else:

        "image": f"data:application/pdf;base64,{pdf_base64}",            print(f"\n{key}: {value}")

        "task": "document_analysis",            

        "format": "json"else:

    }    print(f"Error: {response.text}")
    
    print(f"Sending request to Landing AI ADE...")
    print(f"PDF size: {len(pdf_content)} bytes")
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
        response.raise_for_status()

def analyze_landing_ai_response(response_data, output_file):
    """
    Analyze the Landing AI response and generate metrics
    
    Args:
        response_data (dict): API response
        output_file (str): Path to save analysis
    """
    
    # Extract content
    if 'data' in response_data and 'content' in response_data['data']:
        content = response_data['data']['content']
    else:
        content = str(response_data)
    
    # Basic metrics
    char_count = len(content)
    word_count = len(content.split())
    
    # Count different types of content
    figures_mentioned = content.lower().count('figure')
    tables_mentioned = content.lower().count('table')
    images_mentioned = content.lower().count('image')
    
    # Estimate chunks (assuming average of 400 chars per chunk)
    estimated_chunks = char_count // 400
    
    analysis = f"""# Landing AI ADE Analysis Report

## Overview
- **Total Characters**: {char_count:,}
- **Total Words**: {word_count:,}
- **Estimated Chunks**: {estimated_chunks}

## Content Analysis
- **Figures Mentioned**: {figures_mentioned}
- **Tables Mentioned**: {tables_mentioned}
- **Images Mentioned**: {images_mentioned}

## Key Features
- Detailed multimodal analysis
- Figure and image descriptions
- Contextual understanding
- API-based processing

## Cost Information
- First 1000 API calls are free
- Detailed pricing available from Landing AI

## Sample Content Preview
```
{content[:500]}...
```

## Full Response Structure
```json
{json.dumps(response_data, indent=2)[:1000]}...
```
"""
    
    with open(output_file, 'w') as f:
        f.write(analysis)
    
    print(f"Analysis saved to: {output_file}")
    print(f"Content length: {char_count:,} characters")
    print(f"Estimated chunks: {estimated_chunks}")

def main():
    """Main function to run the Landing AI experiment"""
    
    # Get API key from environment
    api_key = os.getenv('LANDING_AI_API_KEY')
    
    if not api_key:
        print("Error: LANDING_AI_API_KEY environment variable not set")
        print("Please set your Landing AI API key:")
        print("export LANDING_AI_API_KEY='your_api_key_here'")
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
    
    output_json = script_dir / f"landing_ai_output_{pdf_name}_{timestamp}.json"
    analysis_file = script_dir / f"landing_ai_output_{pdf_name}_{timestamp}_analysis.md"
    
    try:
        print(f"Starting Landing AI ADE experiment...")
        print(f"Processing: {pdf_path}")
        
        # Test Landing AI ADE
        start_time = time.time()
        response_data = test_landing_ai_ade(pdf_path, api_key)
        end_time = time.time()
        
        print(f"Processing completed in {end_time - start_time:.2f} seconds")
        
        # Save response
        with open(output_json, 'w') as f:
            json.dump(response_data, f, indent=2)
        
        print(f"Response saved to: {output_json}")
        
        # Analyze response
        analyze_landing_ai_response(response_data, analysis_file)
        
        print("\nLanding AI ADE experiment completed successfully!")
        print("Check the generated files for detailed results.")
        
    except Exception as e:
        print(f"Error during experiment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()