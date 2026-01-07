#!/usr/bin/env python3
"""
text_chunker.py
------------------------------
Simplified Docling-aware chunker that works directly on the 'texts' array.

Why this version:
- The 'texts' list in Docling JSON already contains all readable elements.
- Each element has a 'label' (e.g., section_header, text, list_item).
- We simply walk through in order, start new sections on section headers,
  and accumulate text + provenance as we go.

Features:
- Uses section_header to start new chunks
- Includes text and list_item content
- Preserves provenance (page number, bbox, docling_ref)
- Splits long sections into Part N chunks
- Ignores headers, footers, and captions
"""

import os
import json
import time
from pathlib import Path
from collections import Counter

# Import spaCy for sentence segmentation
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class DoclingTextsChunker:
    def __init__(self, max_chunk_size=5000):
        self.max_chunk_size = max_chunk_size
        
        # Initialize spaCy for sentence segmentation
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("Loaded spaCy model for sentence segmentation")
            except OSError:
                print("Warning: spaCy model 'en_core_web_sm' not found. Falling back to basic sentence splitting.")
                self.nlp = None
        else:
            print("Warning: spaCy not installed. Using basic sentence splitting.")

    # --------------------------------------------------------------
    # Sentence segmentation methods
    # --------------------------------------------------------------
    def segment_text_into_sentences(self, text: str, document_char_offset: int = 0):
        """
        Segment text into sentences with precise offset tracking.
        
        Args:
            text: The text to segment
            document_char_offset: Character position where this text starts in the document
            
        Returns:
            List of sentence dictionaries with offset information
        """
        sentences = []
        
        if self.nlp:
            # Use spaCy for accurate sentence segmentation
            doc = self.nlp(text)
            
            for sent_idx, sent in enumerate(doc.sents):
                sentence_text = sent.text.strip()
                if sentence_text:  # Skip empty sentences
                    sentences.append({
                        "sentence_id": sent_idx,
                        "text": sentence_text,
                        "char_start": sent.start_char,
                        "char_end": sent.end_char,
                        "document_start": document_char_offset + sent.start_char,
                        "document_end": document_char_offset + sent.end_char,
                        "length": len(sentence_text)
                    })
        else:
            # Fallback: basic sentence splitting using regex
            import re
            sentence_pattern = r'[.!?]+\s+'
            sentence_boundaries = list(re.finditer(sentence_pattern, text))
            
            start = 0
            for sent_idx, boundary in enumerate(sentence_boundaries):
                end = boundary.start() + 1  # Include the punctuation
                sentence_text = text[start:end].strip()
                
                if sentence_text:
                    sentences.append({
                        "sentence_id": sent_idx,
                        "text": sentence_text,
                        "char_start": start,
                        "char_end": end,
                        "document_start": document_char_offset + start,
                        "document_end": document_char_offset + end,
                        "length": len(sentence_text)
                    })
                
                start = boundary.end()
            
            # Handle last sentence if no ending punctuation
            if start < len(text):
                sentence_text = text[start:].strip()
                if sentence_text:
                    sentences.append({
                        "sentence_id": len(sentences),
                        "text": sentence_text,
                        "char_start": start,
                        "char_end": len(text),
                        "document_start": document_char_offset + start,
                        "document_end": document_char_offset + len(text),
                        "length": len(sentence_text)
                    })
        
        return sentences

    # --------------------------------------------------------------
    # STEP 1: Extract directly from texts[]
    # --------------------------------------------------------------
    def extract_chunks(self, docling_json_path: str, max_chunk_size: int = None):
        max_chunk_size = max_chunk_size or self.max_chunk_size
        print(f"Extracting chunks from: {docling_json_path}")

        with open(docling_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "texts" not in data:
            raise ValueError("Docling JSON missing 'texts' array")

        texts = data["texts"]
        print(f"Found {len(texts)} text elements")

        chunks = []
        current_section = "Front Matter"
        current_text = ""
        current_prov = []
        document_char_offset = 0  # Track position in document

        for entry in texts:
            label = (entry.get("label") or "").lower()
            text = (entry.get("text") or "").strip()

            # Skip empty or irrelevant items
            if not text or label in {"page_header", "page_footer", "caption", "footnote"}:
                continue

            # Start new section when a section_header appears
            if label == "section_header":
                if current_text.strip():
                    section_chunks = self._split_section_with_prov_and_sentences(
                        current_section,
                        current_text,
                        current_prov,
                        max_chunk_size,
                        document_char_offset
                    )
                    chunks.extend(section_chunks)
                    # Update document offset after processing section
                    document_char_offset += len(current_text) + 2  # Account for spacing
                    
                current_section = text
                current_text = ""
                current_prov = []
                continue

            # Include normal content
            if label in {"text", "list_item"}:
                current_text += text + "\n\n"
                current_prov.append(self._make_prov_entry(entry))

        # Final flush
        if current_text.strip():
            section_chunks = self._split_section_with_prov_and_sentences(
                current_section,
                current_text,
                current_prov,
                max_chunk_size,
                document_char_offset
            )
            chunks.extend(section_chunks)

        print(f"Generated {len(chunks)} chunks total")
        total_sentences = sum(len(chunk.get("sentences", [])) for chunk in chunks)
        print(f"Total sentences segmented: {total_sentences}")
        return chunks

    # --------------------------------------------------------------
    # STEP 2: provenance helper
    # --------------------------------------------------------------
    def _make_prov_entry(self, entry: dict) -> dict:
        """Turn a Docling text node into a provenance record."""
        prov_list = entry.get("prov", []) or []
        out = {
            "docling_ref": entry.get("self_ref") or entry.get("_docling_ref"),
            "label": entry.get("label"),
            "pages": [],
        }
        for prov in prov_list:
            page_no = prov.get("page_no")
            bbox = prov.get("bbox")
            out["pages"].append({
                "page_no": page_no,
                "bbox": bbox
            })
        return out

    # --------------------------------------------------------------
    # Enhanced section splitting with sentence segmentation
    # --------------------------------------------------------------
    def _split_section_with_prov_and_sentences(self, section_name: str, section_text: str,
                                             prov_list: list, max_chunk_size: int, 
                                             document_char_offset: int):
        """Split section into chunks with sentence-level segmentation."""
        paragraphs = section_text.split("\n\n")
        chunks = []
        current_chunk = ""
        current_chunk_prov = []
        part_index = 1
        prov_iter = iter(prov_list)
        pending_prov = []
        chunk_char_offset = document_char_offset  # Track where current chunk starts in document

        for paragraph in paragraphs:
            para = paragraph.strip()
            if not para:
                continue

            if not pending_prov:
                try:
                    pending_prov.append(next(prov_iter))
                except StopIteration:
                    pass

            candidate = current_chunk + para + "\n\n"
            if len(candidate) > max_chunk_size and current_chunk:
                # Create chunk with sentence segmentation
                header = f"[Section: {section_name} — Part {part_index}]\n"
                chunk_text = header + current_chunk.strip()
                
                # Add sentence segmentation to this chunk
                chunk_content = current_chunk.strip()  # Text without header
                sentences = self.segment_text_into_sentences(chunk_content, chunk_char_offset + len(header))
                
                chunks.append({
                    "chunk": chunk_text,
                    "provenance": current_chunk_prov,
                    "section": section_name,
                    # Add sentence data
                    "sentences": sentences,
                    "sentence_count": len(sentences),
                    "document_offsets": {
                        "start": chunk_char_offset,
                        "end": chunk_char_offset + len(chunk_text)
                    }
                })
                
                # Update offset for next chunk
                chunk_char_offset += len(chunk_text) + 2  # Account for spacing
                current_chunk = para + "\n\n"
                current_chunk_prov = pending_prov
                pending_prov = []
                part_index += 1
            else:
                current_chunk = candidate
                current_chunk_prov.extend(pending_prov)
                pending_prov = []

        # Handle final chunk
        if current_chunk.strip():
            header = f"[Section: {section_name}"
            if part_index > 1:
                header += f" — Part {part_index}"
            header += "]\n"
            leftover_prov = list(prov_iter)
            current_chunk_prov.extend(leftover_prov)
            
            chunk_text = header + current_chunk.strip()
            chunk_content = current_chunk.strip()  # Text without header
            
            # Add sentence segmentation to final chunk
            sentences = self.segment_text_into_sentences(chunk_content, chunk_char_offset + len(header))
            
            chunks.append({
                "chunk": chunk_text,
                "provenance": current_chunk_prov,
                "section": section_name,
                # Add sentence data
                "sentences": sentences,
                "sentence_count": len(sentences),
                "document_offsets": {
                    "start": chunk_char_offset,
                    "end": chunk_char_offset + len(chunk_text)
                }
            })

        return chunks

    # --------------------------------------------------------------
    # STEP 3: split long sections and align provenance (LEGACY - for compatibility)
    # --------------------------------------------------------------
    def _split_section_with_prov(self, section_name: str, section_text: str,
                                 prov_list: list, max_chunk_size: int):
        paragraphs = section_text.split("\n\n")
        chunks = []
        current_chunk = ""
        current_chunk_prov = []
        part_index = 1
        prov_iter = iter(prov_list)
        pending_prov = []

        for paragraph in paragraphs:
            para = paragraph.strip()
            if not para:
                continue

            if not pending_prov:
                try:
                    pending_prov.append(next(prov_iter))
                except StopIteration:
                    pass

            candidate = current_chunk + para + "\n\n"
            if len(candidate) > max_chunk_size and current_chunk:
                header = f"[Section: {section_name} — Part {part_index}]\n"
                chunks.append({
                    "chunk": header + current_chunk.strip(),
                    "provenance": current_chunk_prov,
                    "section": section_name,
                })
                current_chunk = para + "\n\n"
                current_chunk_prov = pending_prov
                pending_prov = []
                part_index += 1
            else:
                current_chunk = candidate
                current_chunk_prov.extend(pending_prov)
                pending_prov = []

        if current_chunk.strip():
            header = f"[Section: {section_name}"
            if part_index > 1:
                header += f" — Part {part_index}"
            header += "]\n"
            leftover_prov = list(prov_iter)
            current_chunk_prov.extend(leftover_prov)
            chunks.append({
                "chunk": header + current_chunk.strip(),
                "provenance": current_chunk_prov,
                "section": section_name,
            })

        return chunks

    def chunk_docling_json(self, docling_json_path: str, output_dir: str = "output/text_chunks") -> str:
        """Process a Docling JSON file and save chunks to organized output directory."""
        input_path = Path(docling_json_path)
        output_path = Path(output_dir)
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        output_file = output_path / f"{input_path.stem}.texts_chunks.jsonl"
        
        print(f"Processing: {input_path.name}")
        print(f"Output: {output_file}")
        
        # Extract chunks
        chunks = self.extract_chunks(str(input_path))
        
        # Save chunks
        with open(output_file, "w", encoding="utf-8") as out:
            for chunk in chunks:
                json.dump(chunk, out, ensure_ascii=False)
                out.write("\n")
        
        print(f"Created {len(chunks)} chunks in {output_file.name}")
        return str(output_file)


# --------------------------------------------------------------
# STEP 4: main utility for testing
# --------------------------------------------------------------
def main():
    import sys
    
    chunker = DoclingTextsChunker(max_chunk_size=5000)
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        output_dir_arg = sys.argv[2] if len(sys.argv) > 2 else "output/text_chunks"
        
        if os.path.exists(file_path):
            # Process the specified file
            try:
                start = time.time()
                chunks = chunker.extract_chunks(file_path)
                elapsed = time.time() - start

                print(f"\nFinished chunk extraction: {len(chunks)} total chunks ({elapsed:.2f}s).")

                counts = Counter(c["section"] for c in chunks)
                print("\nSection Distribution:")
                print("-" * 40)
                for section, count in counts.most_common():
                    print(f"{section:40s}: {count}")

                # Preview
                for i, ch in enumerate(chunks[:3], start=1):
                    print(f"\n--- Chunk {i} ({len(ch['chunk'])} chars) ---")
                    print(ch["chunk"][:300].replace("\n", " ") + "...")

                # Save to specified output directory
                input_filename = Path(file_path).stem
                output_dir = Path(output_dir_arg)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{input_filename}.texts_chunks.jsonl"
                with open(output_path, "w", encoding="utf-8") as out:
                    for ch in chunks:
                        json.dump(ch, out, ensure_ascii=False)
                        out.write("\n")

                print(f"\nChunks written to {output_path}")
                return

            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                return
        else:
            print(f"File not found: {file_path}")
            return
    
    # Fallback to test files if no command line argument
    test_files = [
        "Copy of A. Priyadarsini et al. 2023.json",
    ]

    for file_path in test_files:
        if not os.path.exists(file_path):
            continue

        try:
            start = time.time()
            chunks = chunker.extract_chunks(file_path)
            elapsed = time.time() - start

            print(f"\nFinished chunk extraction: {len(chunks)} total chunks ({elapsed:.2f}s).")

            counts = Counter(c["section"] for c in chunks)
            print("\nSection Distribution:")
            print("-" * 40)
            for section, count in counts.most_common():
                print(f"{section:40s}: {count}")

            # Preview
            for i, ch in enumerate(chunks[:3], start=1):
                print(f"\n--- Chunk {i} ({len(ch['chunk'])} chars) ---")
                print(ch["chunk"][:300].replace("\n", " ") + "...")

            # Save to proper text_chunks directory  
            input_filename = Path(file_path).stem
            output_dir = Path("output/text_chunks")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{input_filename}.texts_chunks.jsonl"
            with open(output_path, "w", encoding="utf-8") as out:
                for ch in chunks:
                    json.dump(ch, out, ensure_ascii=False)
                    out.write("\n")

            print(f"\nChunks written to {output_path}")
            return

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print("No suitable JSON file found. Make sure your Docling output is available.")


if __name__ == "__main__":
    main()
