#!/usr/bin/env python3
"""
Proof of Concept Part 2: Complete Visual Triple Extraction Pipeline
Combines Docling JSON parsing, PDF image extraction, and VLM analysis
"""

import json
import fitz  # PyMuPDF
import io
from PIL import Image
from pathlib import Path
import os
import torch
import gc
from transformers import AutoProcessor, AutoModelForImageTextToText

class VisualTripleExtractor:
    """Complete pipeline for extracting visual triples from scientific figures."""
    
    def __init__(self, model_name="Qwen/Qwen3-VL-4B-Instruct", cleanup_images=True):
        self.model_name = model_name
        self.cleanup_images = cleanup_images
        self.processor = None
        self.model = None
        self.device = None
        
    def load_model(self):
        """Load the VLM model and processor."""
        print(f"Loading VLM model: {self.model_name}")
        
        # Environment setup for memory management
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        
        try:
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            self.processor.tokenizer.padding_side = 'left'
            
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_name,
                device_map="auto",
                dtype=torch.float16
            )
            
            self.device = self.model.device
            print(f"Model loaded on device: {self.device}")
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def cleanup_memory(self):
        """Clean up memory and GPU resources."""
        try:
            # Force garbage collection
            gc.collect()
            
            # Clear GPU cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                torch.mps.empty_cache()
                
        except Exception as e:
            print(f"Memory cleanup warning: {e}")
    
    def parse_docling_figures(self, docling_json_path):
        """Extract figure metadata from Docling JSON."""
        print(f"Parsing Docling JSON: {docling_json_path}")
        
        with open(docling_json_path, 'r') as f:
            data = json.load(f)
        
        # Extract captions
        captions = [item for item in data['texts'] if item.get('label') == 'caption']
        
        # Extract pictures  
        pictures = data.get('pictures', [])
        
        # Organize by page
        figures_by_page = {}
        
        for caption in captions:
            if 'prov' in caption:
                for prov in caption['prov']:
                    page_num = prov['page_no']
                    if page_num not in figures_by_page:
                        figures_by_page[page_num] = {'captions': [], 'pictures': []}
                    figures_by_page[page_num]['captions'].append({
                        'text': caption['text'],
                        'prov': prov
                    })
        
        for picture in pictures:
            if 'prov' in picture:
                for prov in picture['prov']:
                    page_num = prov['page_no']
                    if page_num not in figures_by_page:
                        figures_by_page[page_num] = {'captions': [], 'pictures': []}
                    figures_by_page[page_num]['pictures'].append({
                        'self_ref': picture.get('self_ref', ''),
                        'prov': prov
                    })
        
        print(f"Found figures on {len(figures_by_page)} pages")
        return figures_by_page

    def extract_pdf_images(self, pdf_path, target_pages=None):
        """Extract embedded images from PDF pages."""
        print(f"Extracting images from PDF: {pdf_path}")
        
        pdf_doc = fitz.open(pdf_path)
        extracted_images = {}
        
        for page_num in range(len(pdf_doc)):
            page_num_1based = page_num + 1
            
            if target_pages and page_num_1based not in target_pages:
                continue
                
            page = pdf_doc[page_num]
            images = page.get_images(full=True)
            
            if images:
                extracted_images[page_num_1based] = []
                
                for img_index, img in enumerate(images):
                    try:
                        xref = img[0]
                        base_image = pdf_doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        
                        extracted_images[page_num_1based].append({
                            'index': img_index,
                            'pil_image': pil_image,
                            'size': pil_image.size,
                            'mode': pil_image.mode
                        })
                        
                    except Exception as e:
                        print(f"  Error extracting image {img_index} on page {page_num_1based}: {e}")
        
        pdf_doc.close()
        return extracted_images

    def match_figures_to_images(self, docling_figures, pdf_images):
        """Match Docling figures with PDF images."""
        print("Matching figures to images...")
        
        matches = []
        
        for page_num in docling_figures.keys():
            docling_data = docling_figures[page_num]
            pdf_data = pdf_images.get(page_num, [])
            
            print(f"  Page {page_num}: {len(docling_data['captions'])} captions, {len(pdf_data)} images")
            
            # Simple positional matching
            for i, caption in enumerate(docling_data['captions']):
                if i < len(pdf_data):
                    matches.append({
                        'page': page_num,
                        'caption': caption,
                        'image': pdf_data[i],
                        'figure_id': f"page{page_num}_fig{i+1}"
                    })
        
        print(f"Successfully matched {len(matches)} figures to images")
        return matches

    def extract_triples_from_image(self, image, caption_text, figure_id):
        """Extract triples from a single image using VLM."""
        try:
            # Prepare image
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Limit resolution to prevent memory issues
            image.thumbnail((1280, 1280))
            
            # Create messages for triple extraction
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {
                            "type": "text",
                            "text": (
                                "You are a scientific reasoning assistant.\n"
                                "Analyze this figure together with its caption, and extract factual triples "
                                "in the format (subject, relation, object).\n"
                                "Focus on scientific entities and relationships.\n"
                                f"Caption: {caption_text}\n\nOutput as a Python list of tuples:"
                            ),
                        },
                    ],
                }
            ]
            
            # Process with model
            text_prompt = self.processor.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            
            inputs = self.processor(text=[text_prompt], images=[image], return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs, 
                    max_new_tokens=512,
                    temperature=None,
                    top_p=None,
                    top_k=None
                )
            
            # Extract generated tokens
            input_length = inputs.input_ids.shape[1]
            generated_tokens = outputs[0][input_length:]
            generated_text = self.processor.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
            
            # Clean up output
            cleanup_patterns = ["Output as a Python list of tuples:", "output as a python list of tuples:", "\nOutput:", "\noutput:"]
            for pattern in cleanup_patterns:
                if pattern in generated_text:
                    generated_text = generated_text.split(pattern, 1)[-1].strip()
            
            return {
                'figure_id': figure_id,
                'raw_output': generated_text,
                'success': True
            }
            
        except Exception as e:
            return {
                'figure_id': figure_id,
                'error': str(e),
                'success': False
            }
        
        finally:
            # Clean up memory
            if 'inputs' in locals():
                del inputs
            if 'outputs' in locals():
                del outputs
            torch.cuda.empty_cache()
            gc.collect()

    def process_paper(self, docling_json_path, pdf_path, output_file):
        """Process a complete paper through the visual triple extraction pipeline."""
        print("=" * 60)
        print("VISUAL TRIPLE EXTRACTION PIPELINE - PROOF OF CONCEPT PART 2")
        print("=" * 60)
        
        # Step 1: Parse Docling figures
        docling_figures = self.parse_docling_figures(docling_json_path)
        if not docling_figures:
            print("No figures found in Docling JSON")
            return False
        
        # Step 2: Extract PDF images
        target_pages = list(docling_figures.keys())
        pdf_images = self.extract_pdf_images(pdf_path, target_pages)
        if not pdf_images:
            print("No images extracted from PDF")
            return False
        
        # Step 3: Match figures to images
        matches = self.match_figures_to_images(docling_figures, pdf_images)
        if not matches:
            print("No figure-image matches found")
            return False
        
        # Step 4: Load VLM model
        if not self.load_model():
            print("Failed to load VLM model")
            return False
        
        # Step 5: Extract triples from each matched figure
        results = []
        
        print(f"\nExtracting triples from {len(matches)} figures...")
        
        for i, match in enumerate(matches, 1):
            figure_id = match['figure_id']
            caption_text = match['caption']['text']
            image = match['image']['pil_image']
            
            print(f"\nProcessing {figure_id} ({i}/{len(matches)})...")
            print(f"Caption: {caption_text[:100]}...")
            
            result = self.extract_triples_from_image(image, caption_text, figure_id)
            
            # Add provenance information
            result.update({
                'page': match['page'],
                'caption': caption_text,
                'provenance': match['caption']['prov'],
                'image_info': {
                    'size': match['image']['size'],
                    'mode': match['image']['mode']
                }
            })
            
            results.append(result)
            
            if result['success']:
                print(f"  Successfully extracted triples")
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
            
            # Cleanup: Clear image from memory after processing
            if self.cleanup_images and 'image' in match and 'pil_image' in match['image']:
                try:
                    match['image']['pil_image'].close()
                    del match['image']['pil_image']
                except Exception:
                    pass  # Ignore cleanup errors
        
        # Additional memory cleanup
        if self.cleanup_images:
            self.cleanup_memory()
        
        # Step 6: Save results
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        # Summary
        print(f"\n" + "=" * 60)
        print(f"PIPELINE COMPLETE")
        print(f"Successfully processed {successful}/{len(results)} figures")
        print(f"Results saved to: {output_file}")
        
        # Optional: Format for KG integration
        try:
            from visual_kg_formatter import VisualKGFormatter
            formatter = VisualKGFormatter()
            kg_output = output_file.replace('.json', '_kg_format.json')
            formatter.process_visual_output(output_file, kg_output)
            print(f"KG-formatted output: {kg_output}")
            print(f"Ready for: python ../knowledge_graph/kg_data_loader.py {kg_output}")
        except ImportError:
            print("visual_kg_formatter not available - skipping KG format conversion")
        except Exception as e:
            print(f"KG formatting failed: {e}")
        
        print("=" * 60)
        
        return True

def main():
    """Run the complete visual triple extraction pipeline."""
    
    # File paths
    docling_json = "output/docling_json/Copy of Kulkarni et al. 2021.json"
    pdf_path = "../papers/Copy of Kulkarni et al. 2021.pdf"
    output_file = "output/visual_triples_poc.json"
    
    # Check files exist
    if not Path(docling_json).exists():
        print(f"Error: Docling JSON not found: {docling_json}")
        return
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF not found: {pdf_path}")
        return
    
    # Run pipeline
    extractor = VisualTripleExtractor()
    success = extractor.process_paper(docling_json, pdf_path, output_file)
    
    if success:
        print("\nProof of concept Part 2 completed successfully!")
    else:
        print("\nProof of concept Part 2 failed.")

if __name__ == "__main__":
    main()