# Visual Review Implementation Plan

## Overview

Extend the paper review system to support figure and table analysis using vision-capable models. This enhancement will provide comprehensive quality assessment that includes visual elements alongside text-based evaluation.

---

## Architecture

### Current State (Text-Only)

```
PDF → Docling → export_to_markdown() → Text Review Endpoints
                                      ↓
                                  LLM (Ollama/GPT-4o-mini)
                                      ↓
                                  Rubric Evaluations
```

**Limitations:**

- Tables converted to markdown (lose structure)
- Figures become placeholder text (lose visual content)
- No assessment of figure quality, clarity, or appropriateness

### Proposed State (Multimodal)

```
PDF → Docling JSON
         ├─→ export_to_markdown() → Text Review (existing)
         │                           ↓
         │                       Text LLM (Ollama/GPT-4o-mini)
         │
         ├─→ figures[] → Extract Images → Figure Review (new)
         │                                  ↓
         │                              Vision LLM (GPT-4o/Qwen-VL)
         │
         └─→ tables[] → Structured Data → Table Review (new)
                                           ↓
                                       Text LLM (any model)
```

---

## Implementation Phases

### Phase 1: Infrastructure Setup

**Goal:** Create vision model abstraction and configuration

**Tasks:**

1. Create `knowledge_graph/llm_review/utils/vision_runner.py`

   - Similar to `llm_runner.py` but for vision models
   - Support GPT-4o (OpenAI API)
   - Support Qwen-VL (local or Ollama)
   - Fallback logic if vision unavailable

2. Update `.env` configuration:

   ```bash
   # Text models (existing)
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.1:8b

   # Vision models (new)
   VISION_PROVIDER=openai    # or 'qwen' or 'ollama_vision'
   VISION_MODEL=gpt-4o       # or 'qwen-vl-chat' or 'llava'
   VISION_BASE_URL=          # optional for local models
   ```

3. Add vision dependencies to `requirements.txt`:
   - Already have: `openai`, `python-dotenv`, `docling`
   - May need: `transformers`, `torch` (if using Qwen-VL locally)

**Deliverables:**

- `vision_runner.py` with `get_vision_client()` function
- Updated `.env.example` with vision model options
- Documentation on supported vision providers

**Estimated Effort:** 2-3 hours

---

### Phase 2: Figure Extraction & Review

**Goal:** Enable figure quality assessment using vision models

**Tasks:**

1. Create `knowledge_graph/llm_review/utils/figure_extractor.py`

   - Reuse logic from `kg_gen_pipeline/core/visual_kg_extractor.py`
   - Parse Docling JSON for figure metadata
   - Extract images from PDF using PyMuPDF
   - Match figures to captions
   - Return list of figures with images and metadata

2. Create figure review prompt: `knowledge_graph/llm_review/prompts/rubric_figures.txt`

   - Assess figure quality for presentation rubric
   - Check: clarity, labels, axes, legends, color schemes
   - Check: appropriate chart types, readability
   - Check: proper captions, references in text
   - Output: Tier 1-3 assessment with specific feedback

3. Add API endpoint: `POST /api/review/figures`

   - Request body: `{"pdf_filename": "paper.pdf"}`
   - Parse Docling JSON to find all figures
   - Extract each figure image
   - Send to vision model with figure rubric
   - Return array of figure assessments

4. Add single figure endpoint: `POST /api/review/figure/{figure_id}`
   - Request body: `{"pdf_filename": "paper.pdf"}`
   - Extract specific figure (e.g., "page5_fig1")
   - Send to vision model
   - Return single figure assessment

**Deliverables:**

- Figure extraction utility
- Figure quality rubric prompt
- Two new API endpoints for figure review
- Updated API_ENDPOINTS.md documentation

**Estimated Effort:** 4-5 hours

---

### Phase 3: Table Extraction & Review

**Goal:** Enable structured table analysis using existing LLM

**Tasks:**

1. Create `knowledge_graph/llm_review/utils/table_extractor.py`

   - Reuse logic from `kg_gen_pipeline/extract_tables_only.py`
   - Parse Docling JSON for table metadata
   - Extract structured table data (grid format)
   - Convert to readable text representation
   - Return list of tables with data and metadata

2. Create table review prompt: `knowledge_graph/llm_review/prompts/rubric_tables.txt`

   - Assess table quality for data rubric
   - Check: completeness, appropriate metrics
   - Check: statistical reporting (means, std, p-values)
   - Check: proper headers, units, captions
   - Check: data availability statements
   - Output: Tier 1-3 assessment with recommendations

3. Add API endpoint: `POST /api/review/tables`

   - Request body: `{"pdf_filename": "paper.pdf"}`
   - Parse Docling JSON to find all tables
   - Extract structured data for each table
   - Send to text LLM with table rubric
   - Return array of table assessments

4. Add single table endpoint: `POST /api/review/table/{table_id}`
   - Request body: `{"pdf_filename": "paper.pdf"}`
   - Extract specific table (e.g., "page3_table0")
   - Send to text LLM
   - Return single table assessment

**Deliverables:**

- Table extraction utility
- Table quality rubric prompt
- Two new API endpoints for table review
- Updated API_ENDPOINTS.md documentation

**Estimated Effort:** 3-4 hours

---

### Phase 4: Comprehensive Review Integration

**Goal:** Combine text, figure, and table reviews into unified assessment

**Tasks:**

1. Create `POST /api/review/comprehensive` endpoint

   - Request body:
     ```json
     {
       "pdf_filename": "paper.pdf",
       "include_figures": true, // optional, default false
       "include_tables": true // optional, default false
     }
     ```
   - Orchestrate all review types:
     - Run text review (6 rubrics)
     - If `include_figures`: Run figure reviews
     - If `include_tables`: Run table reviews
   - Merge results into unified report

2. Enhance rubric synthesis to include visual elements

   - Modify `synthesize_review()` in `result_merger.py`
   - Incorporate figure feedback into presentation rubric
   - Incorporate table feedback into data rubric
   - Generate unified improvement checklist

3. Update response structure:
   ```json
   {
     "text_review": {
       "rubric_responses": [...],
       "merged_text": "...",
       "final_summary": "..."
     },
     "figure_reviews": [
       {
         "figure_id": "page5_fig1",
         "assessment": "Tier 2...",
         "issues": ["Missing error bars", "Small font size"]
       }
     ],
     "table_reviews": [
       {
         "table_id": "page3_table0",
         "assessment": "Tier 1...",
         "strengths": ["Complete metrics", "Statistical tests"]
       }
     ],
     "comprehensive_summary": "Overall Tier 2-3 with strong methodology but presentation issues...",
     "metadata": {
       "text_provider": "ollama",
       "vision_provider": "openai",
       "processing_time": "4m 30s"
     }
   }
   ```

**Deliverables:**

- Comprehensive review orchestrator endpoint
- Enhanced synthesis logic
- Unified review report structure
- Complete documentation

**Estimated Effort:** 3-4 hours

---

### Phase 5: Documentation & Testing

**Goal:** Complete documentation and validate all functionality

**Tasks:**

1. Update `API_ENDPOINTS.md`:

   - Add Section 6.2: Figure Review Endpoints
   - Add Section 6.3: Table Review Endpoints
   - Add Section 6.4: Comprehensive Review
   - Include vision model configuration guide
   - Add curl examples for all new endpoints

2. Update `MIGRATION_PLAN.md` or create new guide:

   - How to configure vision models
   - Cost comparison (GPT-4o vs Qwen-VL)
   - Performance expectations
   - When to use each review type

3. Create example workflows:

   - Text-only review (existing, fast)
   - Text + tables review (enhanced data assessment)
   - Full review with figures (complete presentation analysis)
   - Individual element reviews (debugging)

4. Testing checklist:
   - Text review still works (no regression)
   - Figure extraction from PDF
   - GPT-4o vision model integration
   - Qwen-VL local model integration (if supported)
   - Table extraction from Docling JSON
   - Comprehensive review orchestration
   - Error handling (missing figures, corrupt tables)
   - Cost tracking and reporting

**Deliverables:**

- Complete API documentation
- Configuration guide
- Example workflows
- Test validation report

**Estimated Effort:** 2-3 hours

---

## File Structure

```
knowledge_graph/
├── llm_review/
│   ├── prompts/
│   │   ├── rubric1_methodology.txt          (existing)
│   │   ├── rubric2_reproducibility.txt      (existing)
│   │   ├── rubric3_rigor.txt                (existing)
│   │   ├── rubric4_data.txt                 (existing)
│   │   ├── rubric5_presentation.txt         (existing)
│   │   ├── rubric6_references.txt           (existing)
│   │   ├── rubric_figures.txt               (new - Phase 2)
│   │   ├── rubric_tables.txt                (new - Phase 3)
│   │   └── synthesizer.txt                  (existing, update Phase 4)
│   │
│   └── utils/
│       ├── llm_runner.py                    (existing - text models)
│       ├── vision_runner.py                 (new - Phase 1)
│       ├── figure_extractor.py              (new - Phase 2)
│       ├── table_extractor.py               (new - Phase 3)
│       ├── result_merger.py                 (existing, update Phase 4)
│       ├── text_loader.py                   (existing)
│       └── formatter.py                     (existing)
│
├── api.py                                   (update all phases)
└── .env                                     (update Phase 1)

Documentation/
├── API_ENDPOINTS.md                         (update Phase 5)
└── VISUAL_REVIEW_IMPLEMENTATION_PLAN.md    (this file)
```

---

## API Endpoint Summary

### Existing (Text-Only)

- `POST /api/review` - Complete 6-rubric text review
- `POST /api/review/rubric/{rubric_name}` - Single rubric text review

### New (Visual Content)

- `POST /api/review/figures` - Review all figures in paper
- `POST /api/review/figure/{figure_id}` - Review single figure
- `POST /api/review/tables` - Review all tables in paper
- `POST /api/review/table/{table_id}` - Review single table
- `POST /api/review/comprehensive` - Unified text + visual review

---

## Configuration Examples

### Development (Free, Local)

```bash
# Text reviews with Ollama
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b

# Figure reviews with Qwen-VL locally
VISION_PROVIDER=qwen
VISION_MODEL=qwen-vl-chat
```

### Production (Paid, Cloud)

```bash
# Text reviews with OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Figure reviews with GPT-4o
VISION_PROVIDER=openai
VISION_MODEL=gpt-4o
```

### Hybrid (Cost Optimization)

```bash
# Text reviews with Ollama (free)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b

# Figure reviews with GPT-4o (paid, but only when needed)
VISION_PROVIDER=openai
VISION_MODEL=gpt-4o
```

---

## Cost Considerations

### Text-Only Review

- Ollama (local): $0.00
- OpenAI GPT-4o-mini: ~$0.02-0.05 per paper
- Time: 3 minutes (Ollama) or 30-60 seconds (OpenAI)

### With Figure Analysis

- Add GPT-4o vision: ~$0.01-0.05 per figure
- Typical paper: 3-5 figures = ~$0.03-0.25 per paper
- Add Qwen-VL (local): $0.00 but slower (30-60 sec per figure)

### With Table Analysis

- Uses text LLM (same cost as text review)
- Minimal additional cost
- Typical paper: 2-3 tables = ~$0.01-0.03 extra (OpenAI)

### Comprehensive Review

- Ollama + GPT-4o figures: ~$0.10-0.30 per paper
- All OpenAI: ~$0.15-0.50 per paper
- All local (Ollama + Qwen-VL): $0.00, ~10-15 minutes

---

## Performance Expectations

### Text Review (Existing)

- Ollama: ~3 minutes for 6 rubrics
- OpenAI: ~30-60 seconds for 6 rubrics

### Figure Review (New)

- GPT-4o: ~5-10 seconds per figure
- Qwen-VL local: ~30-60 seconds per figure
- Typical paper (4 figs): 20-40 seconds (GPT-4o) or 2-4 minutes (Qwen-VL)

### Table Review (New)

- Same as text LLM
- ~5-10 seconds per table (any model)
- Typical paper (3 tables): 15-30 seconds

### Comprehensive Review

- Text + Figures + Tables:
  - All Ollama/local: ~10-15 minutes
  - Ollama + GPT-4o figures: ~5-7 minutes
  - All OpenAI: ~2-3 minutes

---

## Success Criteria

### Phase 1 Complete

- [ ] Vision model abstraction created
- [ ] GPT-4o integration working
- [ ] Qwen-VL integration documented
- [ ] Environment configuration updated

### Phase 2 Complete

- [ ] Figure extraction working
- [ ] Figure quality rubric defined
- [ ] Figure review endpoints functional
- [ ] Sample figure review generated

### Phase 3 Complete

- [ ] Table extraction working
- [ ] Table quality rubric defined
- [ ] Table review endpoints functional
- [ ] Sample table review generated

### Phase 4 Complete

- [ ] Comprehensive review orchestration working
- [ ] Unified report generation
- [ ] Visual elements integrated into rubric scores
- [ ] Performance acceptable (<5 minutes with Ollama)

### Phase 5 Complete

- [ ] Complete API documentation
- [ ] Configuration guide published
- [ ] All endpoints tested
- [ ] Example workflows demonstrated

---

## Risk Mitigation

### Vision Model Unavailable

- **Risk:** Qwen-VL setup complex, GPT-4o costs money
- **Mitigation:** Make vision optional, text review still works
- **Fallback:** Graceful degradation with warning message

### Performance Issues

- **Risk:** Vision models slow, comprehensive review takes too long
- **Mitigation:** Async processing, progress updates, caching
- **Alternative:** Separate endpoints allow selective use

### Quality Concerns

- **Risk:** Vision model misinterprets figures
- **Mitigation:** Provide figure context (caption, section)
- **Validation:** Manual review of sample outputs

### Cost Overruns

- **Risk:** GPT-4o vision expensive for many figures
- **Mitigation:** Clear cost warnings in docs
- **Alternative:** Local Qwen-VL option
- **Optimization:** Cache results, batch processing

---

## Future Enhancements

### Beyond Initial Implementation

1. **Streaming Responses**

   - Real-time progress updates for long reviews
   - Server-Sent Events for comprehensive reviews

2. **Review History**

   - Store review results in database
   - Track improvements over time
   - Compare versions

3. **Custom Rubrics**

   - User-defined evaluation criteria
   - Domain-specific assessment
   - Configurable weights

4. **Batch Processing**

   - Review multiple papers in parallel
   - Generate comparative reports
   - Literature review quality assessment

5. **Enhanced Figure Analysis**

   - OCR for text in figures
   - Data extraction from charts
   - Reproducibility checks (code → figure match)

6. **Interactive Review**
   - Ask follow-up questions
   - Request clarification
   - Suggest specific improvements

---

## Timeline Estimate

- **Phase 1:** 2-3 hours
- **Phase 2:** 4-5 hours
- **Phase 3:** 3-4 hours
- **Phase 4:** 3-4 hours
- **Phase 5:** 2-3 hours

**Total:** 14-19 hours for complete implementation

**Minimum Viable Product (MVP):**

- Phase 1 + Phase 2 + Phase 5 (partial): ~8-10 hours
- Provides text review + figure analysis (most impactful features)

---

## Next Steps

1. Review and approve this plan
2. Set up vision model environment (GPT-4o or Qwen-VL)
3. Begin Phase 1: Infrastructure setup
4. Iterate through phases sequentially
5. Test at each phase before proceeding
6. Document as you go

**Ready to start implementation when approved!**
