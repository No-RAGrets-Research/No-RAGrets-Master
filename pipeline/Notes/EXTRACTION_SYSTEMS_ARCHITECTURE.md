# Extraction Systems Architecture

**Document Purpose:** Comprehensive technical documentation of the three extraction systems (text, visual, table) and their integration into the knowledge graph.

**Last Updated:** December 7, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Text Extraction System](#text-extraction-system)
4. [Visual Extraction System](#visual-extraction-system)
5. [Table Extraction System](#table-extraction-system)
6. [Comparative Analysis](#comparative-analysis)
7. [Knowledge Graph Integration](#knowledge-graph-integration)
8. [Data Flow](#data-flow)
9. [Provenance Tracking](#provenance-tracking)

---

## Overview

The knowledge graph generation pipeline extracts structured information from scientific papers using three parallel extraction systems, each specialized for different content types:

- **Text Extraction**: Extracts relations from prose text (introduction, methods, results, discussion)
- **Visual Extraction**: Extracts relations from figures, charts, and diagrams
- **Table Extraction**: Extracts relations from structured tabular data

All three systems converge into a unified knowledge graph with consistent schema and provenance tracking.

### Key Design Principles

1. **Source Fidelity**: Each extraction maintains precise links to source content
2. **Modular Processing**: Systems can run independently or sequentially
3. **Format Consistency**: All outputs conform to the same relation schema
4. **Provenance Tracking**: Every relation traces back to exact document location
5. **Deduplication**: Relations extracted from multiple sources are intelligently merged

---

## Architecture

### Pipeline Flow

```
PDF Document
   OK†
[Stage 1] Docling PDF Parsing
   OK””€ Text extraction with structure preservation
   OK””€ Figure detection and metadata extraction
   OK””€ Table detection and structure parsing
   OK”””€ Output: Structured JSON with all content types
   OK†
[Stage 2] Text Chunking
   OK””€ Segment text into processable chunks
   OK””€ Preserve section structure
   OK””€ Sentence segmentation using spaCy
   OK”””€ Output: Text chunks with sentence-level offsets
   OK†
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚        PARALLEL EXTRACTION SYSTEMS                 OK”‚
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”¤
”‚                                                    OK”‚
”‚  [Text Extraction]     [Visual Extraction]        OK”‚
”‚        OK†OK                     OK†OK                   OK”‚
”‚   Text Triples           Visual Triples           OK”‚
”‚                                                    OK”‚
”‚            [Table Extraction]                      OK”‚
”‚                   OK†OK                               OK”‚
”‚              Table Triples                         OK”‚
”‚                                                    OK”‚
”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
   OK†
[Stage 3] Relation Formatting
   OK””€ Normalize relation structure
   OK””€ Add source-specific metadata
   OK”””€ Prepare for database loading
   OK†
[Stage 4] Knowledge Graph Loading
   OK””€ Entity deduplication
   OK””€ Relation deduplication
   OK””€ Graph database insertion
   OK”””€ Output: Unified knowledge graph
```

---

## Text Extraction System

### Purpose

Extract structured knowledge from natural language prose in scientific papers. This is the primary extraction system and handles the majority of content.

### Technology Stack

- **LLM**: Mistral 7B via Ollama (local inference)
- **NLP**: spaCy (sentence segmentation, character offsets)
- **Processing**: Chunk-based extraction with context preservation

### Process Flow

#### 1. Text Chunking

**Input**: Docling JSON with parsed text elements
**Output**: JSONL file with text chunks

```python
# Each chunk contains:
{
    "index": 0,
    "section": "Introduction",
    "chunk": "Full text of the chunk...",
    "sentences": [
        {
            "sentence_id": 0,
            "text": "Methanotrophs use methane.",
            "char_start": 0,
            "char_end": 27,
            "document_start": 1234,
            "document_end": 1261
        }
    ],
    "provenance": [
        {
            "docling_ref": "#/texts/42",
            "label": "paragraph",
            "pages": [{"page_no": 3, "bbox": {...}}]
        }
    ]
}
```

**Key Features**:

- Preserves document structure (sections, paragraphs)
- Tracks page numbers and bounding boxes
- Maintains character offsets for precise location mapping
- Links to Docling references for frontend rendering

#### 2. Relation Extraction

**Input**: Text chunks with provenance
**Output**: Relations with entity pairs and predicates

**LLM Prompt Strategy**:

```
Extract knowledge triples from the following text.
Focus on scientific entities and their relationships.
Format: (subject, predicate, object)

Text: [chunk text]

Output as Python list of tuples.
```

**LLM Configuration**:

- Model: Mistral 7B Instruct
- Temperature: 0.0 (deterministic)
- Max tokens: 512
- API: Ollama local inference

#### 3. Span Mapping

After LLM extraction, relations are mapped back to specific sentences:

```python
def calculate_relation_span(relation, chunk_sentences, chunk_id):
    """Map relation to sentence locations."""
    subject = relation["subject"]
    object = relation["object"]

    # Find sentences containing subject and object
    subject_sentences = find_sentences_containing_entity(subject, chunk_sentences)
    object_sentences = find_sentences_containing_entity(object, chunk_sentences)

    # Determine span type based on sentence coverage
    if same_sentence(subject_sentences, object_sentences):
        span_type = "single_sentence"
        sentences = [sentence_id]
    elif adjacent_sentences(subject_sentences, object_sentences):
        span_type = "multi_sentence"
        sentences = [start_id, end_id]
    else:
        span_type = "cross_chunk"
        sentences = all_sentence_ids
```

**Span Types**:

- `single_sentence`: Subject and object in same sentence
- `multi_sentence`: Subject and object in adjacent sentences
- `cross_chunk`: Relation spans multiple chunks
- `chunk_fallback`: Entity locations unclear, use entire chunk

#### 4. Source Span Structure

```json
{
  "span_type": "multi_sentence",
  "text_evidence": "Full text containing the relation...",
  "confidence": 0.85,
  "location": {
    "chunk_id": 14,
    "sentence_range": [1, 3],
    "document_offsets": {
      "start": 47722,
      "end": 48205
    }
  },
  "subject_positions": [
    {
      "start": 20,
      "end": 30,
      "sentence_id": 1,
      "matched_text": "Methanotrophs"
    }
  ],
  "object_positions": [
    {
      "start": 85,
      "end": 92,
      "sentence_id": 2,
      "matched_text": "methane"
    }
  ],
  "docling_ref": "#/texts/42"
}
```

### Output Format

```json
{
  "subject": "Methanotrophs",
  "predicate": "oxidize",
  "object": "methane",
  "section": "Introduction",
  "pages": [2, 3],
  "chunk_id": 14,
  "source_span": {
    /* detailed span data */
  },
  "confidence": 0.85
}
```

### Performance Characteristics

- **Processing Speed**: ~30-60 seconds per paper (depends on length)
- **GPU Requirements**: None (CPU-based LLM inference)
- **Memory Usage**: ~4-8GB RAM for Mistral 7B
- **Typical Output**: 50-200 relations per paper

---

## Visual Extraction System

### Purpose

Extract structured knowledge from figures, charts, diagrams, and other visual elements that contain information not captured in text.

### Technology Stack

- **Vision-Language Model**: Qwen3-VL-4B-Instruct
- **PDF Processing**: PyMuPDF (fitz) for image extraction
- **Image Processing**: PIL for image manipulation
- **Device**: CUDA GPU (required for VLM inference)

### Process Flow

#### 1. Figure Detection

**Input**: Docling JSON with figure metadata
**Output**: List of figures with captions and locations

```python
def parse_docling_figures(docling_json_path):
    """Extract figure metadata from Docling JSON."""
    with open(docling_json_path, 'r') as f:
        data = json.load(f)

    # Extract captions (labeled as 'caption')
    captions = [item for item in data['texts']
                if item.get('label') == 'caption']

    # Extract picture metadata
    pictures = data.get('pictures', [])

    # Organize by page for matching
    figures_by_page = organize_by_page(captions, pictures)

    return figures_by_page
```

**Figure Metadata**:

```json
{
  "page": 5,
  "caption": "Figure 3. CH4 flux rates across different sites...",
  "prov": {
    "page_no": 5,
    "bbox": { "l": 72, "t": 200, "r": 540, "b": 450 },
    "charspan": [2500, 2750]
  },
  "self_ref": "#/pictures/2"
}
```

#### 2. Image Extraction

**Input**: PDF file and target page numbers
**Output**: PIL Image objects with metadata

```python
def extract_pdf_images(pdf_path, target_pages):
    """Extract embedded images from PDF."""
    doc = fitz.open(pdf_path)
    extracted_images = []

    for page_num in target_pages:
        page = doc[page_num - 1]

        # Get all images on the page
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))

            extracted_images.append({
                "page": page_num,
                "image_index": img_index,
                "pil_image": pil_image,
                "size": pil_image.size,
                "mode": pil_image.mode
            })

    return extracted_images
```

#### 3. Figure-Image Matching

**Challenge**: Associate extracted images with figure captions

**Strategy**: Spatial proximity matching using page numbers and bounding boxes

```python
def match_figures_to_images(docling_figures, pdf_images):
    """Match Docling figure metadata with PDF images."""
    matches = []

    for page_num, figures_data in docling_figures.items():
        page_captions = figures_data['captions']
        page_images = [img for img in pdf_images
                       if img['page'] == page_num]

        # Match based on position (largest image usually the main figure)
        for caption in page_captions:
            if page_images:
                # Use largest image on page
                image = max(page_images, key=lambda x: x['size'][0] * x['size'][1])

                matches.append({
                    "figure_id": f"page{page_num}_fig{len(matches)}",
                    "caption": caption,
                    "image": image,
                    "page": page_num
                })

    return matches
```

#### 4. Visual Triple Extraction

**Input**: Image + Caption
**Output**: Knowledge triples extracted from visual content

**VLM Prompt**:

```
You are a scientific reasoning assistant.
Analyze this figure together with its caption, and extract factual triples
in the format (subject, relation, object).
Focus on scientific entities and relationships.

Caption: [caption text]

Output as a Python list of tuples:
```

**Processing**:

```python
def extract_triples_from_image(image, caption_text, figure_id):
    """Extract triples using vision-language model."""
    # Prepare image (convert to RGB, resize if needed)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.thumbnail((1280, 1280))  # Limit resolution

    # Create VLM input
    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": prompt_with_caption}
        ]
    }]

    # Process with VLM
    inputs = processor(text=[prompt], images=[image], return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=None
        )

    # Decode and parse output
    generated_text = processor.tokenizer.decode(outputs, skip_special_tokens=True)
    triples = parse_vlm_output(generated_text)

    return triples
```

#### 5. Visual Source Span

```json
{
  "span_type": "visual_figure",
  "figure_id": "page5_fig0",
  "page_number": 5,
  "caption_evidence": "Figure 3. CH4 flux rates across different sites...",
  "bbox_coordinates": {
    "l": 72,
    "t": 200,
    "r": 540,
    "b": 450
  },
  "confidence": 0.9,
  "extraction_method": "visual_triple_extraction",
  "image_info": {
    "size": [468, 250],
    "mode": "RGB"
  },
  "charspan": [2500, 2750],
  "docling_ref": "#/pictures/2"
}
```

### Output Format

```json
{
  "subject": "Site A",
  "predicate": "has_higher_CH4_flux_than",
  "object": "Site B",
  "figure_id": "page5_fig0",
  "source_span": {
    /* visual span data */
  },
  "confidence": 0.9
}
```

### Performance Characteristics

- **Processing Speed**: ~10-30 seconds per figure (GPU-dependent)
- **GPU Requirements**: CUDA-capable GPU with 6GB+ VRAM
- **Memory Usage**: ~6-8GB VRAM, ~8GB RAM
- **Typical Output**: 3-15 relations per figure
- **Success Rate**: ~70-90% (depends on figure complexity)

### Unique Challenges

1. **Image Quality**: Low-resolution figures reduce extraction accuracy
2. **Complex Visualizations**: Multi-panel figures may require separate processing
3. **Text in Images**: OCR needed for text-heavy figures
4. **Color Encoding**: Color-coded data requires model interpretation
5. **Graph Types**: Different chart types (bar, line, scatter) have different information density

---

## Table Extraction System

### Purpose

Extract structured knowledge from tables containing measurements, comparisons, experimental results, and quantitative data.

### Technology Stack

- **LLM**: Mistral 7B (same as text extraction)
- **NLP**: spaCy (sentence segmentation)
- **Processing**: Table-specific chunking and linearization

### Process Flow

#### 1. Table Detection

**Input**: Docling JSON with table elements
**Output**: List of tables with structure and content

```python
def extract_tables_from_docling(docling_json_path):
    """Extract table elements from Docling JSON."""
    with open(docling_json_path, 'r') as f:
        data = json.load(f)

    # Tables have label 'table' in Docling output
    tables = [item for item in data.get('texts', [])
              if item.get('label') == 'table']

    return tables
```

**Table Structure**:

```json
{
  "text": "Full table content...",
  "label": "table",
  "prov": [
    {
      "page_no": 7,
      "bbox": { "l": 72, "t": 100, "r": 540, "b": 400 },
      "charspan": [3000, 3500]
    }
  ],
  "data": {
    "num_rows": 5,
    "num_cols": 4,
    "table_cells": [
      { "row": 0, "col": 0, "text": "Site" },
      { "row": 0, "col": 1, "text": "CH4 Flux" }
      // ... more cells
    ]
  },
  "self_ref": "#/tables/0"
}
```

#### 2. Table Linearization

**Challenge**: Convert 2D table structure to text suitable for LLM processing

**Strategy**: Create readable text representation preserving row/column relationships

```python
def table_data_to_text(table_data):
    """Convert structured table to readable text."""
    lines = []

    # Get dimensions
    num_rows = table_data.get('num_rows', 0)
    num_cols = table_data.get('num_cols', 0)

    # Create grid
    grid = [['' for _ in range(num_cols)] for _ in range(num_rows)]

    # Fill grid from cells
    for cell in table_data.get('table_cells', []):
        row = cell.get('row', 0)
        col = cell.get('col', 0)
        text = cell.get('text', '').strip()
        if row < num_rows and col < num_cols:
            grid[row][col] = text

    # Convert to text (row by row)
    for row_idx, row in enumerate(grid):
        if row_idx == 0:
            # Header row
            lines.append("Headers: " + " | ".join(row))
        else:
            # Data row
            lines.append(f"Row {row_idx}: " + " | ".join(row))

    return "\n".join(lines)
```

**Example Linearization**:

```
Headers: Site | CH4 Flux (mg m-2 d-1) | Temperature (Â°C) | Moisture (%)
Row 1: Site A | 120 | 25 | 65
Row 2: Site B | 85 | 22 | 58
Row 3: Site C | 150 | 28 | 72
```

#### 3. Table Chunking

**Input**: Linearized table text
**Output**: Chunks with sentence segmentation

```python
def create_table_chunk(table, table_id, paper_name):
    """Convert table to chunk for LLM extraction."""
    # Get text content (prefer structured over raw)
    if 'data' in table:
        text_content = table_data_to_text(table['data'])
    else:
        text_content = table.get('text', '')

    # Segment into sentences using spaCy
    sentences = segment_text_into_sentences(text_content)

    # Create chunk
    chunk = {
        "chunk": f"[Table {table_id}]\n{text_content}",
        "provenance": [{
            "docling_ref": table.get('self_ref', f'#/tables/{table_id}'),
            "label": "table",
            "pages": [{
                "page_no": table['prov'][0]['page_no'],
                "bbox": table['prov'][0]['bbox']
            }]
        }],
        "section": f"Visual Analysis: Table {table_id}",
        "table_id": table_id,
        "sentences": sentences  # For span mapping
    }

    return chunk
```

#### 4. Relation Extraction

**Same LLM as text extraction** (Mistral 7B) but with table context:

**LLM Prompt**:

```
Extract knowledge triples from the following table.
Focus on quantitative relationships and comparisons.
Format: (subject, predicate, object)

Table: [linearized table text]

Output as Python list of tuples.
```

**Table-Specific Patterns**:

- Comparisons: "Site A has higher flux than Site B"
- Measurements: "Site A has flux of 120 mg m-2 d-1"
- Correlations: "Temperature affects CH4 flux"

#### 5. Table Source Span

```json
{
  "span_type": "visual_table",
  "table_id": "page7_table0",
  "page_number": 7,
  "text_evidence": "Site A | 120 | 25 | 65",
  "confidence": 0.95,
  "location": {
    "table_id": "page7_table0",
    "row_range": [1, 1],
    "bbox": {
      "l": 72,
      "t": 100,
      "r": 540,
      "b": 400
    }
  },
  "extraction_method": "table_triple_extraction",
  "charspan": [3000, 3500],
  "docling_ref": "#/tables/0"
}
```

### Output Format

```json
{
  "subject": "Site A",
  "predicate": "has_CH4_flux",
  "object": "120 mg m-2 d-1",
  "table_id": "page7_table0",
  "section": "Results",
  "pages": [7],
  "source_span": {
    /* table span data */
  },
  "confidence": 0.95
}
```

### Performance Characteristics

- **Processing Speed**: ~10-20 seconds per table
- **GPU Requirements**: None (CPU-based LLM)
- **Memory Usage**: ~4-8GB RAM
- **Typical Output**: 10-50 relations per table (depends on complexity)
- **Success Rate**: ~85-95% (tables are highly structured)

### Unique Advantages

1. **High Precision**: Structured format reduces ambiguity
2. **Quantitative Data**: Easy extraction of measurements
3. **Comparative Relations**: Natural comparisons across rows
4. **Completeness**: Less likely to miss information

---

## Comparative Analysis

### Similarities

All three systems share core design patterns:

1. **Two-Stage Processing**:

   - Stage 1: Content detection and extraction
   - Stage 2: LLM/VLM-based relation extraction

2. **Provenance Tracking**:

   - All maintain links to source locations
   - Character offsets, page numbers, bounding boxes
   - Docling references for frontend rendering

3. **Confidence Scoring**:

   - Relations include confidence estimates
   - Based on extraction method and content clarity

4. **Output Format**:

   - Consistent triple structure: (subject, predicate, object)
   - Standardized source_span format
   - Compatible with same database schema

5. **Sentence Segmentation**:
   - Text and table extraction both use spaCy
   - Enables precise span mapping
   - Character offset preservation

### Differences

| Aspect                | Text Extraction        | Visual Extraction           | Table Extraction        |
| --------------------- | ---------------------- | --------------------------- | ----------------------- |
| **Primary Model**     | Mistral 7B (Text LLM)  | Qwen3-VL (Vision-Language)  | Mistral 7B (Text LLM)   |
| **Input Type**        | Natural language prose | Images + Captions           | Structured tabular data |
| **GPU Required**      | No (CPU inference)     | Yes (CUDA GPU)              | No (CPU inference)      |
| **Processing Speed**  | 30-60 sec/paper        | 10-30 sec/figure            | 10-20 sec/table         |
| **Typical Relations** | 50-200 per paper       | 3-15 per figure             | 10-50 per table         |
| **Confidence**        | 0.7-0.9                | 0.6-0.9                     | 0.8-0.95                |
| **Span Type**         | Sentence ranges        | Figure regions              | Table cells/rows        |
| **Content Format**    | Linear text            | Visual + Caption            | Grid structure          |
| **Preprocessing**     | Chunking + spaCy       | Image extraction + matching | Linearization + spaCy   |

### Information Coverage

**Text Extraction**:

- Captures narrative relationships
- Contextual information
- Background knowledge
- Methodology descriptions
- Qualitative observations

**Visual Extraction**:

- Visual trends and patterns
- Graphical comparisons
- Spatial relationships
- Visual-only data (not in text)
- Complex multi-dimensional relationships

**Table Extraction**:

- Precise quantitative data
- Systematic comparisons
- Measurements with units
- Statistical values
- Structured experimental results

### Complementary Nature

The three systems extract **non-overlapping information**:

```
Paper Content = Text + Visuals + Tables
              = 60%  + 25%    + 15%    (approximate)

Extraction Coverage:
- Text-only relations: ~40-50%
- Visual-only relations: ~20-30%
- Table-only relations: ~15-20%
- Overlapping relations: ~5-10% (deduplicated)
```

---

## Knowledge Graph Integration

### Unified Schema

All three extraction systems produce relations conforming to the same schema:

```graphql
type Relation {
  id: ID!
  subject: String!
  predicate: String!
  object: String!
  source_paper: String!
  section: String
  pages: [Int]
  confidence: Float

  # Source-specific fields
  chunk_id: Int # Text extraction
  figure_id: String # Visual extraction
  table_id: String # Table extraction
  # Unified provenance
  source_span: SourceSpan!

  # Timestamps
  created_at: DateTime
  updated_at: DateTime
}

type SourceSpan {
  span_type: String! # "single_sentence", "visual_figure", "visual_table", etc.
  text_evidence: String
  confidence: Float
  location: Location
  docling_ref: String # Link to Docling JSON element
  # Text-specific
  subject_positions: [Position]
  object_positions: [Position]

  # Visual-specific
  figure_id: String
  caption_evidence: String
  bbox_coordinates: BBox

  # Table-specific
  table_id: String
  row_range: [Int]
}
```

### Loading Pipeline

**Stage 1: Entity Extraction**

```python
def extract_entities_from_triples(triples):
    """Extract unique entities from all relation sources."""
    entities = set()

    for triple in triples:
        entities.add(triple['subject'])
        entities.add(triple['object'])

    return list(entities)
```

**Stage 2: Entity Deduplication**

```python
def deduplicate_entities(entities):
    """Merge similar entity names."""
    # Normalize names (lowercase, strip whitespace)
    # Fuzzy matching for minor variations
    # Merge: "methanotrophs" == "Methanotrophs" == "methanotroph"

    deduplicated = {}
    for entity in entities:
        canonical = find_canonical_form(entity)
        deduplicated[canonical] = entity

    return deduplicated
```

**Stage 3: Entity Loading**

```python
def load_entities_to_graph(entities, paper_metadata):
    """Insert entities into graph database."""
    for entity in entities:
        mutation = """
        mutation addEntity($name: String!, $source_paper: String!) {
            addEntity(input: {
                name: $name,
                source_papers: [$source_paper],
                entity_type: "concept"
            }) {
                entity {
                    id
                    name
                }
            }
        }
        """

        variables = {
            "name": entity,
            "source_paper": paper_metadata['filename']
        }

        result = dgraph.mutate(mutation, variables)
```

**Stage 4: Relation Loading**

```python
def load_relations_to_graph(triples, entity_map):
    """Insert relations with full provenance."""
    for triple in triples:
        # Get entity IDs
        subject_id = entity_map[triple['subject']]
        object_id = entity_map[triple['object']]

        mutation = """
        mutation addRelation(
            $subject: ID!,
            $object: ID!,
            $predicate: String!,
            $source_span: String!,
            $confidence: Float!
        ) {
            addRelation(input: {
                subject: {id: $subject},
                object: {id: $object},
                predicate: $predicate,
                source_span: $source_span,
                confidence: $confidence
            }) {
                relation {
                    id
                }
            }
        }
        """

        variables = {
            "subject": subject_id,
            "object": object_id,
            "predicate": triple['predicate'],
            "source_span": json.dumps(triple['source_span']),
            "confidence": triple['confidence']
        }

        result = dgraph.mutate(mutation, variables)
```

**Stage 5: Relation Deduplication**

```python
def deduplicate_relations():
    """Merge duplicate relations from multiple sources."""
    # Query existing relations
    query = """
    query {
        queryRelation {
            id
            subject { name }
            predicate
            object { name }
            source_paper
        }
    }
    """

    relations = dgraph.query(query)

    # Group by (subject, predicate, object)
    groups = defaultdict(list)
    for relation in relations:
        key = (
            relation['subject']['name'],
            relation['predicate'],
            relation['object']['name']
        )
        groups[key].append(relation)

    # Merge duplicates (keep highest confidence)
    for key, duplicates in groups.items():
        if len(duplicates) > 1:
            primary = max(duplicates, key=lambda r: r.get('confidence', 0))
            others = [r for r in duplicates if r['id'] != primary['id']]

            # Delete duplicates
            for other in others:
                delete_relation(other['id'])
```

### Cross-Source Integration

Relations from different sources are merged intelligently:

**Example: Same Relation from Text and Table**

**Text Extraction**:

```json
{
  "subject": "Site A",
  "predicate": "has_higher_CH4_flux_than",
  "object": "Site B",
  "source_span": {
    "span_type": "single_sentence",
    "text_evidence": "Site A showed significantly higher CH4 flux than Site B.",
    "docling_ref": "#/texts/42"
  },
  "confidence": 0.8
}
```

**Table Extraction**:

```json
{
  "subject": "Site A",
  "predicate": "has_CH4_flux",
  "object": "120 mg m-2 d-1",
  "source_span": {
    "span_type": "visual_table",
    "text_evidence": "Site A | 120 | ...",
    "docling_ref": "#/tables/0"
  },
  "confidence": 0.95
}
```

**Merged in Graph**:

```json
{
  "subject": "Site A",
  "predicate": "has_higher_CH4_flux_than",
  "object": "Site B",
  "confidence": 0.8,
  "source_spans": [
    {
      "source": "text",
      "docling_ref": "#/texts/42",
      "text_evidence": "Site A showed significantly higher CH4 flux than Site B."
    }
  ],
  "supporting_evidence": [
    {
      "source": "table",
      "relation": "Site A has_CH4_flux 120 mg m-2 d-1",
      "docling_ref": "#/tables/0"
    }
  ]
}
```

---

## Data Flow

### Complete Pipeline Data Flow

```
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚                      PDF Document                          OK”‚
”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”¬”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
                        OK†
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚               Docling PDF Parsing                          OK”‚
”‚ OK””€ Text elements (paragraphs, sections)                   OK”‚
”‚ OK””€ Figure metadata (captions, locations)                  OK”‚
”‚ OK”””€ Table structures (cells, headers)                      OK”‚
”””€”€”€”€”€”€”€”€”¬”€”€”€”€”€”€”€”€”€”€”€”€”€”€”¬”€”€”€”€”€”€”€”€”€”€”€”€”€”€”¬”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
        OK†OK             OK†OK             OK†
   OK””€”€”€”€”€”€”€”€”   OK””€”€”€”€”€”€”€”€”€”  OK””€”€”€”€”€”€”€”€”€”€”
   OK”‚  Text OK”‚   OK”‚ FiguresOK”‚  OK”‚  Tables OK”‚
   OK”‚Elements”‚   OK”‚MetadataOK”‚  OK”‚StructureOK”‚
   OK”””€”€”€”¬”€”€”€”€”˜   OK”””€”€”€”€”¬”€”€”€”€”˜  OK”””€”€”€”€”¬”€”€”€”€”€”˜
       OK†OK             OK†OK             OK†
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”OK””€”€”€”€”€”€”€”€”€”€”€”€”€”OK””€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚Text Chunking OK”‚OK”‚Image Extract”‚OK”‚LinearizationOK”‚
”‚+ spaCy SegmenOK”‚OK”‚+ Matching  OK”‚OK”‚+ spaCy Segmen”‚
”””€”€”€”€”€”€”€”¬”€”€”€”€”€”€”€”˜OK”””€”€”€”€”€”€”¬”€”€”€”€”€”€”˜OK”””€”€”€”€”€”€”¬”€”€”€”€”€”€”€”˜
       OK†OK               OK†OK               OK†
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”OK””€”€”€”€”€”€”€”€”€”€”€”€”€”OK””€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚   Mistral 7B OK”‚OK”‚  Qwen3-VL  OK”‚OK”‚  Mistral 7B OK”‚
”‚  LLM Extract OK”‚OK”‚VLM Extract OK”‚OK”‚  LLM ExtractOK”‚
”””€”€”€”€”€”€”€”¬”€”€”€”€”€”€”€”˜OK”””€”€”€”€”€”€”¬”€”€”€”€”€”€”˜OK”””€”€”€”€”€”€”¬”€”€”€”€”€”€”€”˜
       OK†OK               OK†OK               OK†
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”OK””€”€”€”€”€”€”€”€”€”€”€”€”€”OK””€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚  Span MappingOK”‚OK”‚Visual SpansOK”‚OK”‚Table Spans  OK”‚
”””€”€”€”€”€”€”€”¬”€”€”€”€”€”€”€”˜OK”””€”€”€”€”€”€”¬”€”€”€”€”€”€”˜OK”””€”€”€”€”€”€”¬”€”€”€”€”€”€”€”˜
       OK†OK               OK†OK               OK†
       OK”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”´”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
                        OK†
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚              Relation Normalization                        OK”‚
”‚ OK””€ Standardize format                                     OK”‚
”‚ OK””€ Add provenance metadata                                OK”‚
”‚ OK”””€ Calculate confidence scores                            OK”‚
”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”¬”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
                        OK†
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚              Knowledge Graph Loading                       OK”‚
”‚ OK””€ Entity extraction & deduplication                      OK”‚
”‚ OK””€ Relation insertion with provenance                     OK”‚
”‚ OK””€ Cross-source deduplication                             OK”‚
”‚ OK”””€ Graph indexing                                         OK”‚
”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”¬”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
                        OK†
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚              Unified Knowledge Graph                       OK”‚
”‚ OK””€ 14,900 relations (current corpus)                      OK”‚
”‚ OK””€ Multiple source types per paper                        OK”‚
”‚ OK””€ Full provenance chains                                 OK”‚
”‚ OK”””€ API-accessible with docling_ref                        OK”‚
”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
```

---

## Provenance Tracking

### Multi-Level Provenance

Every relation maintains a complete chain of provenance:

**Level 1: Paper**

- Source paper filename
- Paper metadata (authors, year, title)

**Level 2: Document Location**

- Page numbers
- Section (Introduction, Methods, Results, etc.)
- Bounding box coordinates

**Level 3: Content Element**

- Text: Chunk ID, sentence range
- Visual: Figure ID, caption
- Table: Table ID, row range

**Level 4: Character Offsets**

- Document-level character positions
- Sentence-level character positions
- Entity mention positions

**Level 5: Docling Reference**

- Direct link to Docling JSON element
- Enables frontend DOM selection
- Format: `#/texts/42`, `#/pictures/2`, `#/tables/0`

### Provenance Query Example

```graphql
query getRelationProvenance($relationId: ID!) {
    getRelation(id: $relationId) {
        subject
        predicate
        object

        # Paper provenance
        source_paper
        section
        pages

        # Content provenance
        chunk_id
        figure_id
        table_id

        # Detailed provenance
        source_span

        # Docling reference for frontend
        docling_ref: source_span.docling_ref
    }
}
```

### Frontend Integration

The `docling_ref` field enables direct document scrolling:

```javascript
// Fetch relation with provenance
const response = await fetch(`/api/relations/${relationId}/source-span`);
const data = await response.json();

// Extract docling reference
const doclingRef = data.source_span.docling_ref; // e.g., "#/texts/42"

// Direct DOM selection
const element = document.querySelector(`[data-docling-ref="${doclingRef}"]`);

// Scroll to element
element.scrollIntoView({ behavior: "smooth", block: "center" });

// Highlight element
element.classList.add("highlighted");
```

This completes the **end-to-end provenance chain** from knowledge graph relation back to the exact location in the original PDF document.

---

## Summary

The three extraction systems form a **comprehensive knowledge extraction architecture**:

1. **Text Extraction**: Narrative relations from prose (majority of content)
2. **Visual Extraction**: Visual-specific relations from figures (unique insights)
3. **Table Extraction**: Quantitative relations from tables (high precision)

All systems:

- Use state-of-the-art models (Mistral 7B, Qwen3-VL)
- Maintain complete provenance chains
- Conform to unified schema
- Support frontend rendering via `docling_ref`
- Enable precise document location tracking

The integration produces a **rich, multi-source knowledge graph** that captures the complete information content of scientific papers.
