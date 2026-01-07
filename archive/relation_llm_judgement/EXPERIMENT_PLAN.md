# Multi-Model LLM Judge Experiment for Relation Extraction Evaluation

## Objective

Use multiple Ollama models as judges to evaluate whether extracted triples (relations) are valid given their source context (text spans, PDF sections, or images). Focus on relations involving high-connectivity hub entities to maximize impact on knowledge graph quality.

---

## 1. Experiment Design Overview

### What to Judge

- **Quality Assessment**: Is the extracted relation (subject-predicate-object) accurately representing the source text?
- **Faithfulness**: Does the triple truly exist in the source, or is it hallucinated/inferred?
- **Precision**: Are the entity boundaries correctly identified?
- **Contextual Appropriateness**: Given the document section/context, is this a meaningful extraction?

### Judging Modalities

- **Text-based**: Judge from source span text (`/api/relations/{id}/source-span`)
- **Visual-based**: Judge from PDF section image (`/api/relations/{id}/section-image`)
- **Hybrid**: Combine both text and visual context

---

## 2. Data Collection Strategy (Hub Entity Focus)

### Phase 1: Identify Hub Entities

**Step 1: Get Most Connected Entities**

- Use `/api/entities/most-connected?limit=50` to get top 50 most connected entities
- Stratify by entity type (e.g., top chemicals, organisms, processes)
- Consider both incoming and outgoing connection counts

**Step 2: Sample Relations from Hub Entities**

For each hub entity:

- Use `/api/entities/{entity_name}/connections?max_relations=1000`
- Sample relations where the hub is either subject OR object
- Target coverage:
  - **Pilot**: Top 5 hub entities → 25-50 relations
  - **Full Study**: Top 20-30 hub entities → 100-200 relations
  - **Extended**: Top 50 hub entities → 250-500 relations

**Step 3: Diversification Within Hub Sample**

Ensure balanced sampling across:

- **Predicates**: Mix of common and rare relationship types (use `/api/predicates/frequency`)
- **Confidence scores**: Include both high and low confidence extractions
- **Document sections**: Abstract, Methods, Results, Discussion
- **Papers**: Cross-paper diversity to test consistency
- **Entity roles**: Relations where hub is subject vs object
- **Co-occurring entities**: Avoid over-sampling same entity pairs

### Why Hub Entity Focus?

1. **Higher Impact**: Relations involving hub entities are more critical to the graph's utility
2. **Diverse Context**: Hub entities appear in multiple contexts, providing varied extraction scenarios
3. **Quality Control Priority**: Errors in high-connectivity nodes propagate more widely through the graph
4. **Representative Sample**: Hub entities likely span multiple relation types and papers
5. **Actionable Insights**: Results guide targeted improvements for the most important entities

### Phase 2: Context Retrieval

For each sampled relation, fetch:

- Relation metadata from `/api/relations/{id}/provenance`
- Text context from `/api/relations/{id}/source-span`
- Visual context from `/api/relations/{id}/section-image`
- Subject/object positions within sentences

---

## 3. Judge Model Selection

### Recommended Ollama Models

Vary by size and capability:

- **Small models**: `llama3.2:3b`, `phi3:mini`, `mistral:7b`
- **Medium models**: `llama3.1:8b`, `gemma2:9b`
- **Large models**: `llama3.1:70b`, `qwen2.5:32b`, `mixtral:8x7b`
- **Vision models**: `llama3.2-vision:11b`, `llava:13b` (for image-based judging)

### Why Multiple Models?

- Compare small vs large model judgment quality
- Identify if certain models are better judges for specific relation types
- Evaluate inter-model agreement (Cohen's Kappa)
- Assess cost-performance tradeoffs

---

## 4. Judgment Task Design

### Judgment Dimensions

**A. Accuracy (Binary: Correct/Incorrect)**

- Is the triple accurately extracted from the source?

**B. Faithfulness (Scale 1-5)**

- 1 = Hallucinated (not in source)
- 3 = Partially supported
- 5 = Directly stated

**C. Entity Boundary Quality (Scale 1-5)**

- Are subject and object correctly identified and scoped?

**D. Confidence Calibration (Binary: Agree/Disagree)**

- Does the extraction confidence match the actual quality?

---

## 5. Prompting Strategy

### Text-based Judging Prompt Template

```
You are evaluating a knowledge extraction system. Given a sentence and an extracted relation, assess if the extraction is correct.

**Extracted Relation:**
Subject: {subject}
Predicate: {predicate}
Object: {object}

**Source Sentence:**
{sentence_text}

**Subject Position:** Characters {start}-{end}: "{matched_text}"
**Object Position:** Characters {start}-{end}: "{matched_text}"

**Questions:**
1. Is this relation accurately represented in the sentence? (Yes/No)
2. Faithfulness: How directly is this stated? (1-5 scale)
3. Are entity boundaries correct? (1-5 scale)
4. Provide a brief justification (1-2 sentences).
```

### Image-based Judging Prompt Template

```
You are shown a PDF page section with a highlighted region. An extraction system identified a relation from this text.

**Extracted Relation:**
{subject} → {predicate} → {object}

**Task:**
1. Can you find this relation in the highlighted text?
2. Is it accurately extracted?
3. Rate quality (1-5)
```

---

## 6. Ground Truth Establishment

### Human Annotation Phase (Critical)

- Manually annotate a subset (50-100 relations) as "gold standard"
- At least 2 annotators with inter-annotator agreement calculation

### Annotation Categories

- **Perfect**: Exact and complete extraction
- **Acceptable**: Minor issues but semantically correct
- **Partial**: Missing context or overspecified
- **Wrong**: Incorrect or hallucinated

### Purpose

- Measure judge model accuracy against human consensus
- Identify which models best approximate human judgment
- Validate automated quality control approaches

---

## 7. Experimental Workflow

### Step 1: Sample Collection

- Query API to get N diverse relations from hub entities
- Store relation IDs, metadata, and contexts locally

### Step 2: Judge Orchestration

For each relation:

- For each judge model:
  - Send text-based prompt → record response
  - Send image-based prompt (for vision models) → record response
- Store all judgments in structured format (JSON/CSV)

### Step 3: Human Validation

- Annotate subset with human judgments
- Calculate inter-annotator agreement

### Step 4: Analysis

- Compare judge models vs human ground truth
- Inter-model agreement analysis
- Performance by relation type, predicate, confidence score
- Text vs image modality effectiveness

---

## 8. Evaluation Metrics

### Judge Performance

- **Accuracy**: Percentage agreement with human labels
- **Precision/Recall**: For binary correct/incorrect judgments
- **MAE/RMSE**: For scale-based ratings (faithfulness, boundary quality)
- **Cohen's Kappa**: Inter-model agreement

### Stratified Analysis

- Performance by predicate type
- Performance by extraction confidence score
- Performance by document section
- Performance by source paper complexity
- Performance by hub entity (high vs medium connectivity)

### Model Comparison

- Small vs large model accuracy
- Cost-performance tradeoff (inference time)
- Best model for automated quality control
- Text-only vs vision-enabled model performance

---

## 9. Data Pipeline Architecture

### Input

- Relation IDs from knowledge graph (focused on hub entity relations)

### Processing

1. API calls to fetch contexts
2. Prompt generation per model
3. Ollama inference calls (batch if possible)
4. Response parsing and structured storage

### Output

CSV/JSON with columns:

- `relation_id`, `subject`, `predicate`, `object`
- `hub_entity` (which hub entity this relation involves)
- `entity_connectivity` (connection count of the hub)
- `source_text`, `confidence_score`, `section`, `paper`
- `judge_model_1_rating`, `judge_model_2_rating`, ...
- `human_label` (for ground truth subset)

---

## 10. Experiment Phases

### Phase 1: Pilot (Week 1)

- Top 5 hub entities
- 25-50 relations
- 2-3 judge models
- Text-only modality
- Manual result review

### Phase 2: Expansion (Week 2-3)

- Top 20 hub entities
- 100-200 relations
- 5-7 judge models
- Add vision models + image modality
- Human annotation of 50-100 samples

### Phase 3: Full Analysis (Week 4)

- Top 30-50 hub entities
- 250-500 relations
- Statistical analysis
- Model comparison report
- Recommendations for best judge model

---

## 11. Research Questions

1. Which Ollama models are most reliable judges?
2. Do larger models always judge better?
3. Is visual context (images) necessary or is text sufficient?
4. Can we automatically identify low-quality extractions?
5. Which relation types are hardest to judge?
6. Can we use judge scores to improve extraction confidence calibration?
7. Are relations involving hub entities more or less accurate than average?
8. Do certain hub entities have systematic extraction issues?
9. Which predicates are most problematic for high-connectivity entities?

---

## 12. Expected Outcomes

### Deliverables

- Annotated dataset with multi-model judgments focused on hub entities
- Performance comparison report across judge models
- Recommended judge model for automated quality control
- Insights on extraction system strengths/weaknesses
- Hub entity quality analysis (which critical entities need attention)

### Insights for Graph Improvement

- **Network-Level Quality**: If hub relations are high quality → graph is reliable
- **Targeted Fixes**: Identify which hub entities need extraction improvements
- **Priority Ranking**: Focus remediation efforts on highest-impact relations
- **Extraction Model Fine-tuning**: Guide where to improve the extraction system

---

## 13. Tools & Implementation Needs

### Components to Build

1. **API client** to fetch relation contexts and hub entity data
2. **Ollama interface** to run multiple models
3. **Prompt management system** with templates
4. **Response parser** to extract structured judgments
5. **Human annotation interface** (simple web form or CLI)
6. **Analysis notebook** for metrics and visualization

### Technologies

- Python for scripting
- `requests` for API calls
- `ollama` Python package for model inference
- `pandas` for data management
- `scikit-learn` for metrics (accuracy, kappa, etc.)
- `matplotlib`/`seaborn` for visualization

---

## 14. API Endpoints Reference

### Key Endpoints for This Experiment

**Hub Entity Identification:**

- `GET /api/entities/most-connected?limit=50`

**Relation Sampling:**

- `GET /api/entities/{entity_name}/connections?max_relations=1000`
- `GET /api/relations/search?predicate={}&subject={}&limit={}`

**Context Retrieval:**

- `GET /api/relations/{relation_id}/provenance`
- `GET /api/relations/{relation_id}/source-span`
- `GET /api/relations/{relation_id}/section-image`

**Metadata:**

- `GET /api/predicates/frequency`
- `GET /api/graph/stats`

---

## 15. Success Criteria

### Minimum Viable Outcome

- Identify at least one reliable judge model with >80% accuracy vs human labels
- Establish automated quality control pipeline for hub entity relations
- Document systematic issues in current extraction system

### Stretch Goals

- Achieve >90% accuracy with ensemble of judge models
- Build real-time quality scoring system for new extractions
- Create model selection guide (when to use which judge model)
- Publish findings on LLM-as-judge for scientific knowledge graphs
