# VLM Experiments Summary

## Overview

This directory contains comprehensive experiments comparing four different PDF processing tools for scientific document analysis. The experiments evaluate text extraction, structure preservation, multimodal understanding, and figure analysis capabilities.

## Experiment Structure

### Test Document

- **File**: `Baldo et al. 2024.pdf` - A scientific paper on "Methane biohydroxylation into methanol by Methylosinus trichosporium OB3b"
- **Content**: 13-page academic paper with figures, tables, equations, and complex scientific content

## Tools Tested

### 1. PyMuPDF (Baseline)

- **Script**: [`pymupdf_experiment.py`](./pymupdf_experiment.py)
- **Output**: [`pymupdf_output_Baldo et al. 2024_20251012_134557.json`](./pymupdf_output_Baldo%20et%20al.%202024_20251012_134557.json)
- **Analysis**: [`pymupdf_output_Baldo et al. 2024_20251012_134557_analysis.md`](./pymupdf_output_Baldo%20et%20al.%202024_20251012_134557_analysis.md)
- **Capabilities**: Basic text extraction, no image processing
- **Results**: 63,106 characters, 13 text chunks, 0 image chunks

### 2. Docling (Open Source)

- **Script**: [`docling_experiment.py`](./docling_experiment.py)
- **Output**: [`docling_output_Baldo et al. 2024_20251012_130449.json`](./docling_output_Baldo%20et%20al.%202024_20251012_130449.json)
- **Analysis**: [`docling_output_Baldo et al. 2024_20251012_130449_analysis.md`](./docling_output_Baldo%20et%20al.%202024_20251012_130449_analysis.md)
- **Capabilities**: Structure recognition, table extraction, basic image detection
- **Results**: 62,137 characters, 11 chunks (2 tables, 9 images)

### 3. Landing AI ADE (Advanced Multimodal)

- **Script**: [`landing_ai_experiment.py`](./landing_ai_experiment.py)
- **Output**: [`landing_ai_output_Baldo et al. 2024_20251012_125823.json`](./landing_ai_output_Baldo%20et%20al.%202024_20251012_125823.json)
- **Analysis**: [`landing_ai_output_Baldo et al. 2024_20251012_125823_analysis.md`](./landing_ai_output_Baldo%20et%20al.%202024_20251012_125823_analysis.md)
- **Capabilities**: Advanced figure descriptions, detailed content analysis, spatial grounding
- **Results**: 81,685 characters, 208 chunks with rich multimodal understanding

### 4. NVIDIA NeMo Retriever Parse

- **Script**: [`nvidia_nemo_experiment.py`](./nvidia_nemo_experiment.py)
- **Outputs**:
  - [`nvidia_nemo_output_Baldo et al. 2024_20251012_144120.json`](./nvidia_nemo_output_Baldo%20et%20al.%202024_20251012_144120.json) (markdown_bbox)
  - [`nvidia_nemo_output_Baldo et al. 2024_20251012_144736.json`](./nvidia_nemo_output_Baldo%20et%20al.%202024_20251012_144736.json) (markdown_no_bbox)
  - [`nvidia_nemo_output_Baldo et al. 2024_20251012_145035.json`](./nvidia_nemo_output_Baldo%20et%20al.%202024_20251012_145035.json) (detection_only)
- **Analysis Files**: Multiple analysis files for each mode
- **Capabilities**: Image-based analysis with multiple processing modes
- **Results**: ~60,320 characters, 26 chunks with OCR-based extraction

## Key Findings

### Text Extraction Quality

1. **PyMuPDF**: Fast, reliable text extraction but no structure preservation
2. **Docling**: Best structured text with proper headers, sections, and formatting
3. **Landing AI**: Excellent content understanding with semantic analysis
4. **NVIDIA NeMo**: Good OCR-based text extraction with spatial awareness

### Table Processing

- **PyMuPDF** Completed SuccessfullyNo table detection (sees as plain text)
- **Docling** Completed Successfully**2 tables extracted** with proper structure
- **Landing AI** Completed SuccessfullyAdvanced table understanding and content analysis
- **NVIDIA NeMo** Completed SuccessfullyBasic table detection capabilities

### Image/Figure Analysis

- **PyMuPDF** Completed SuccessfullyNo image processing (0 image chunks)
- **Docling** Completed SuccessfullyBasic image detection (9 image placeholders)
- **Landing AI** Completed Successfully**Detailed figure descriptions** and visual understanding
- **NVIDIA NeMo** Completed SuccessfullyImage-based analysis with OCR capabilities

### Document Structure

- **PyMuPDF**: Flat text extraction, page-level organization only
- **Docling**: Excellent hierarchical structure with headers and sections
- **Landing AI**: Semantic understanding of content relationships
- **NVIDIA NeMo**: Layout-aware processing with spatial positioning

## Performance Comparison

| Tool        | Characters | Chunks | Tables | Images | Processing   | API Cost      |
| ----------- | ---------- | ------ | ------ | ------ | ------------ | ------------- |
| PyMuPDF     | 63,106     | 13     | 0      | 0      | Local/Fast   | Free          |
| Docling     | 62,137     | 11     | 2      | 9      | Local/Medium | Free          |
| Landing AI  | 81,685     | 208    |OKOK      |OKOK      | API/Slow     | $0.10/page\*  |
| NVIDIA NeMo | 60,320     | 26     |OKOK      |OKOK      | API/Medium   | $0.002/page\* |

\*Approximate costs based on API pricing

## Comprehensive Analysis

- **Four-Way Comparison**: [`four_way_comparison.md`](./four_way_comparison.md)

## Use Case Recommendations

### Choose PyMuPDF When:

- Fast text extraction is priority
- No images/tables need processing
- Local processing required
- Simple content extraction

### Choose Docling When:

- Document structure is important
- Tables need extraction
- Open-source solution required
- Good balance of features and speed

### Choose Landing AI ADE When:

- Detailed figure analysis needed
- Scientific content understanding required
- Budget allows API costs
- Highest quality multimodal analysis needed

### Choose NVIDIA NeMo When:

- Image-based processing preferred
- Multiple output formats needed
- Cost-effective API solution
- Spatial layout awareness important

## Technical Implementation

### Environment Setup

- API keys configured in [`.env`](../.env)
- Dependencies managed via requirements.txt
- Consistent experiment framework across all tools

### Git Integration

- All experiments tracked in `vlm_experiments` branch
- Large output files excluded via [`.gitignore`](../.gitignore)
- Clean repository history maintained

## Limitations Discovered

1. **PyMuPDF**: Missing image extraction despite capabilities
2. **Docling**: Limited figure description details
3. **Landing AI**: Higher cost and processing time
4. **NVIDIA NeMo**: Occasional OCR inconsistencies

## Future Enhancements

1. **PyMuPDF Enhancement**: Implement bitmap image extraction using `page.get_images()`
2. **Performance Optimization**: Batch processing for multiple documents
3. **Cost Analysis**: Detailed API usage tracking
4. **Quality Metrics**: Automated comparison scoring system

## Repository Structure

```
vlm_experiments/
””€”€ VLM_EXPERIMENTS_SUMMARY.md          # This file
””€”€ four_way_comparison.md              # Comprehensive comparison
””€”€ *_experiment.py                     # Experiment scripts
””€”€ *_output_*.json                     # Raw outputs
””€”€ *_analysis.md                       # Analysis reports
”””€”€ test_documents/                     # Test PDFs
```

---

**Last Updated**: October 17, 2025  
**Branch**: vlm_experiments  
**Repository**: [baseline-model](https://github.com/No-RAGrets-Research/baseline-model)
