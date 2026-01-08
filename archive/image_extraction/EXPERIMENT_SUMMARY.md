# PDF Image Extraction Experiment Summary

This repository contains experiments comparing different methods for extracting images and figures from PDF documents. The goal was to evaluate various approaches for automatically extracting visual content from academic papers.

## Test Document

**Target PDF**: "Baldo et al. 2024.pdf" (13 pages)

## Methods Tested

### 1. **PyMuPDF Image Extractor**

**File**: `pymupdf_image_extractor.py`  
**Technology**: [PyMuPDF](https://pymupdf.readthedocs.io/) (direct PDF parsing)

#### How it works:

- Extracts embedded images directly from PDF's internal structure
- No conversion involved - accesses original image objects using cross-reference (xref) numbers
- Uses `fitz.Pixmap()` to extract images at original resolution
- Ensures RGB format and removes alpha channels

#### Implementation:

```python
def extract_embedded_images(pdf_path: str, out_dir: str) -> list[str]:
    doc = fitz.open(pdf_path)
    for page in doc:
        for xref, *_ in page.get_images(full=True):
            pix = fitz.Pixmap(doc, xref)
            if pix.alpha: pix = fitz.Pixmap(pix, 0)  # RGB conversion
            pix.save(f"img_{xref}.png")
```

#### Results:

- **Output**: Embedded images at original quality
- **File naming**: `img_{xref}.png` (where xref is internal PDF reference)
- **Performance**: Fastest execution time

#### Pros:

-OKOK Highest image quality (lossless extraction)
-OKOK Fastest processing speed
-OKOK Gets actual embedded image files
-OKOK No external dependencies beyond PyMuPDF

#### Cons:

-OKOK Only finds explicitly embedded images
-OKOK Misses vector-based charts/diagrams
-OKOK Won't detect figures drawn as graphics primitives

---

### 2. **Basic LayoutParser Extractor**

**File**: `layoutparser_image_extractor.py`  
**Technology**: [LayoutParser](https://layout-parser.readthedocs.io/) + [EfficientDet](https://github.com/google/automl/tree/master/efficientdet)

#### How it works:

- Uses [pdf2image](https://github.com/Belval/pdf2image) with [Poppler](https://poppler.freedesktop.org/) backend to convert PDF pages to images (200 DPI)
- Applies EfficientDet AI model trained on PubLayNet dataset for document layout analysis
- Detects layout elements: Text, Title, List, Table, **Figure**
- Filters detections by confidence threshold (0.5)

#### Implementation:

```python
model = lp.EfficientDetLayoutModel(
    config_path="lp://PubLayNet/tf_efficientdet_d1/config",
    label_map={0:"Text",1:"Title",2:"List",3:"Table",4:"Figure"},
    device="cpu"
)
pages = convert_from_path(pdf_path, dpi=200)
layout = model.detect(image)
figures = [b for b in layout if b.type == "Figure"]
```

#### Results:

- **Figures found**: 1 figure
- **Location**: Page 12 (score: 0.857)
- **File naming**: `page{num:03d}_fig{num:02d}.png`

#### Pros:

-OKOK AI-powered semantic understanding
-OKOK Finds vector-based figures and charts
-OKOK Trained on academic document layouts
-OKOK Provides confidence scores

#### Cons:

-OKOK Conservative threshold missed valid figures
-OKOK PDF-to-image conversion loses quality
-OKOK Slower due to AI processing
-OKOK Requires model download (~80MB)

---

### 3. **Improved LayoutParser Extractor**

**File**: `improved_layoutparser_extractor.py`  
**Technology**: Enhanced version of LayoutParser approach

#### Improvements made:

- **Lower confidence threshold**: 0.3 (vs 0.5) for better sensitivity
- **Higher DPI conversion**: 300 (vs 200) for better image quality
- **Size filtering**: Minimum area requirements to reduce false positives
- **Padding**: Adds 10px margin around detected figures
- **Overlap removal**: Non-Maximum Suppression to eliminate duplicates
- **Progress reporting**: Detailed feedback during processing
- **Enhanced filenames**: Include confidence scores in output names

#### Implementation:

```python
def extract_figures_improved_layoutparser(pdf_path: str, out_dir: str,
                                        score_threshold: float = 0.3,
                                        dpi: int = 300,
                                        enable_nms: bool = True):
    pages = convert_from_path(pdf_path, dpi=dpi)  # Higher DPI
    figures = [block for block in layout if block.type == "Figure"]

    # Size filtering
    if width > 50 and height > 50 and area > 5000:
        valid_figures.append(fig)

    # NMS for overlap removal
    if enable_nms:
        filtered_files = apply_nms_to_files(out_files, all_detections)
```

#### Results:

- **Figures found**: 2 figures
- **Locations**:
  - Page 12 (score: 0.854)
  - Page 13 (score: 0.424)
- **File naming**: `page{num:03d}_fig{num:02d}_score{score:.3f}_lp.png`

#### Pros:

-OKOK Better detection sensitivity (found additional figure)
-OKOK Higher quality output images
-OKOK Fewer false positives through filtering
-OKOK Configurable parameters
-OKOK Detailed progress feedback

#### Cons:

-OKOK Still limited by PDF-to-image conversion quality
-OKOK Computationally intensive
-OKOK Longer processing time

---

### 4. **Computer Vision Extractor**

**File**: `cv_image_extractor.py`  
**Technology**: [OpenCV](https://opencv.org/) + [pdf2image](https://github.com/Belval/pdf2image)

#### How it works:

- Converts PDF to images using pdf2image (200 DPI)
- Applies [Canny edge detection](https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html) algorithm
- Finds contours using OpenCV's `findContours()`
- Filters by area, aspect ratio, and minimum dimensions
- No AI models - pure computer vision algorithms

#### Implementation:

```python
def extract_figures_with_cv(pdf_path: str, out_dir: str, min_area: int = 10000):
    pages = convert_from_path(pdf_path, dpi=200)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter by size and aspect ratio
    if area > min_area and 0.3 < aspect_ratio < 3.0:
        # Extract region
```

#### Results:

- **Regions found**: Multiple rectangular regions (count varies by parameters)
- **File naming**: `page{num:03d}_fig{num:02d}_cv.png`
- **Processing**: Fast execution

#### Pros:

-OKOK Fast processing speed
-OKOK No AI model dependencies
-OKOK Finds any rectangular content
-OKOK Configurable parameters
-OKOK Simple implementation

#### Cons:

-OKOK Many false positives (text blocks, tables, borders)
-OKOK Basic shape detection only
-OKOK No semantic understanding of content
-OKOK Requires manual tuning of parameters

---

### 5. **Model Testing Script**

**File**: `test_layoutparser.py`  
**Purpose**: Diagnostic tool to check LayoutParser model availability

#### Models tested:

1. **Detectron2LayoutModel** Completed SuccessfullyNot available (requires Detectron2 installation)
2. **PaddleDetectionLayoutModel** Completed SuccessfullyNot available (PaddlePaddle installation failed)
3. **EfficientDetLayoutModel** Completed SuccessfullyAvailable and working

#### Key findings:

- Only EfficientDet backend is readily available
- Detectron2 requires specific PyTorch versions and complex setup
- PaddlePaddle has compatibility issues with current Python versions

---

## Comparative Results

| Method                    | Figures Found    | Quality            | Speed   | Deps   | Type Detected           |
| ------------------------- | ---------------- | ------------------ | ------- | ------ | ----------------------- |
| **PyMuPDF**               | Embedded images  | Highest (lossless) | Fastest | Low    | Embedded images only    |
| **Basic LayoutParser**    | 1 figure         | Good               | Slow    | High   | AI-detected figures     |
| **Improved LayoutParser** | 2 figures        | Good               | Slow    | High   | AI-detected figures     |
| **CV Extractor**          | Multiple regions | Variable           | Fast    | Medium | Any rectangular content |

## Dependencies and Installation

### Core Dependencies:

- **[PyMuPDF](https://pymupdf.readthedocs.io/)**: `pip install PyMuPDF`
- **[LayoutParser](https://layout-parser.readthedocs.io/)**: `pip install "layoutparser[layoutmodels]"`
- **[pdf2image](https://github.com/Belval/pdf2image)**: `pip install pdf2image`
- **[Poppler](https://poppler.freedesktop.org/)**: `brew install poppler` (macOS system dependency)
- **[OpenCV](https://opencv.org/)**: `pip install opencv-python`
- **[PIL/Pillow](https://pillow.readthedocs.io/)**: `pip install pillow`
- **[NumPy](https://numpy.org/)**: `pip install numpy`

### Model Downloads:

- **EfficientDet model**: ~80MB (auto-downloaded on first use)

## Usage Examples

```bash
# PyMuPDF - embedded images
python pymupdf_image_extractor.py "document.pdf" [output_dir]

# Basic LayoutParser
python layoutparser_image_extractor.py "document.pdf" [output_dir] [threshold]

# Improved LayoutParser
python improved_layoutparser_extractor.py "document.pdf" [output_dir] [threshold] [dpi]

# Computer Vision
python cv_image_extractor.py "document.pdf" [output_dir]
```

## Key Insights

### 1. **No Single Method Captures Everything**

Different techniques are optimized for different types of content:

- **Embedded images**: PyMuPDF excels
- **Vector figures**: LayoutParser works best
- **Any rectangular content**: CV methods find most

### 2. **Quality vs Coverage Trade-off**

- **Highest quality**: PyMuPDF (lossless embedded images)
- **Best coverage**: CV methods (finds everything rectangular)
- **Best balance**: Improved LayoutParser (semantic understanding + good coverage)

### 3. **Performance Considerations**

- **Fastest**: PyMuPDF (direct PDF parsing)
- **Slowest**: LayoutParser (AI processing + high DPI conversion)
- **Memory usage**: LayoutParser requires most RAM for AI models

## Recommended Approaches

### For Different Use Cases:

1. **Academic paper figures**: Improved LayoutParser
2. **Embedded photos/images**: PyMuPDF
3. **Quick prototyping**: CV Extractor
4. **Comprehensive extraction**: Hybrid approach

### Optimal Hybrid Strategy:

```python
# 1. Extract embedded images (highest quality)
embedded_images = extract_embedded_images(pdf_path, "embedded/")

# 2. Find AI-detected figures
layout_figures = extract_figures_improved_layoutparser(pdf_path, "figures/")

# 3. Deduplicate overlapping results
final_results = deduplicate_by_overlap(embedded_images, layout_figures)
```

## Future Improvements

1. **Hybrid extractor**: Combine PyMuPDF + LayoutParser automatically
2. **Better deduplication**: Detect when embedded images appear in layout detection
3. **OCR integration**: Extract figure captions and metadata
4. **Vector graphics extraction**: Direct SVG/vector content extraction
5. **Multi-model ensemble**: Combine multiple AI models for better coverage

## Conclusion

The experiments demonstrate that **different PDF content types require different extraction strategies**. PyMuPDF excels for embedded images, while LayoutParser with AI provides the best semantic understanding of document layout. The optimal approach depends on the specific use case and performance requirements.

For most academic document processing tasks, the **Improved LayoutParser Extractor** provides the best balance of accuracy, coverage, and semantic understanding, despite its computational overhead.
