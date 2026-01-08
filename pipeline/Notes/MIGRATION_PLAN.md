# Paper Review System Migration Plan

## Overview

This document outlines the complete plan for migrating the LLM-based paper review system from the `feature-llm-review` branch to the main system, including support for both OpenAI and Ollama LLM providers.

**Source Branch**: `No-RAGrets-Truth-Experiments-and-Pipelines-feature-llm-review/`
**Target**: Main system at `/knowledge_graph/`
**Status**: Planning complete, ready for implementation

---

## System Architecture

### Current Review System (Feature Branch)

The review system uses a 6-rubric evaluation framework plus meta-synthesis:

1. **Rubric 1: Methodology & Research Design** - Evaluates experimental approach
2. **Rubric 2: Reproducibility & Transparency** - Checks for replicability
3. **Rubric 3: Scientific Rigor** - Assesses statistical validity
4. **Rubric 4: Data Quality & Management** - Evaluates data handling
5. **Rubric 5: Presentation & Clarity** - Reviews communication quality
6. **Rubric 6: References & Literature Review** - Checks citations
7. **Synthesizer** - Meta-reviewer that consolidates all rubric outputs

Each rubric uses a 3-tier evaluation system:

- **Tier 1**: Quantitative descriptions (critical elements)
- **Tier 2**: Procedural context (supportive elements)
- **Tier 3**: Verification & references (integrative elements)

### Module Structure

```
knowledge_graph/llm_review/
””€”€ main.py                    # Standalone batch processor
””€”€ prompts/
”‚  OK””€”€ rubric1_methodology.txt
”‚  OK””€”€ rubric2_reproducibility.txt
”‚  OK””€”€ rubric3_rigor.txt
”‚  OK””€”€ rubric4_data.txt
”‚  OK””€”€ rubric5_presentation.txt
”‚  OK””€”€ rubric6_references.txt
”‚  OK”””€”€ synthesizer.txt
”””€”€ utils/
   OK””€”€ text_loader.py         # Docling PDF to markdown
   OK””€”€ llm_runner.py          # OpenAI/Ollama client
   OK””€”€ result_merger.py       # Concatenate rubric outputs
   OK”””€”€ formatter.py           # Output formatting
```

### API Integration

**Endpoint**: `POST /api/review`

**Request Format**:

```json
{
  "text": "Paper markdown content...",
  "pdf_filename": "paper.pdf"
}
```

**Response Format**:

```json
{
  "rubric_responses": [
    {
      "rubric_name": "Methodology",
      "response": "Evaluation text..."
    }
  ],
  "merged_text": "Combined rubric outputs...",
  "final_summary": "Meta-review synthesis..."
}
```

---

## Phase 1: File Structure Setup

### Tasks

1. **Copy llm_review module from feature branch**

   ```bash
   cp -r ../No-RAGrets-Truth-Experiments-and-Pipelines-feature-llm-review/knowledge_graph/llm_review/ \
        knowledge_graph/llm_review/
   ```

2. **Create Python package structure**

   ```bash
   touch knowledge_graph/llm_review/__init__.py
   touch knowledge_graph/llm_review/utils/__init__.py
   touch knowledge_graph/llm_review/prompts/__init__.py
   ```

3. **Verify file permissions**
   ```bash
   chmod +x knowledge_graph/llm_review/main.py
   ```

### Verification

- Check that all 6 rubric files exist in `prompts/`
- Verify synthesizer.txt is present
- Confirm all 4 utility files exist in `utils/`

---

## Phase 2: LLM Provider Abstraction

### Current Implementation (OpenAI Only)

```python
# utils/llm_runner.py (feature branch)
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def run_prompt(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content
```

### New Implementation (OpenAI + Ollama)

```python
# utils/llm_runner.py (updated)
from openai import OpenAI
import os
from typing import Optional

def get_llm_client() -> tuple[OpenAI, str]:
    """
    Initialize LLM client based on environment configuration.

    Returns:
        tuple: (OpenAI client, model name)
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "ollama":
        # Ollama uses OpenAI-compatible API
        client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"  # Dummy key required but not validated
        )
        model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    else:
        # Standard OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    return client, model

# Initialize once at module level
_client, _model = get_llm_client()

def run_prompt(prompt: str, temperature: float = 0.7) -> str:
    """
    Execute prompt with configured LLM provider.

    Args:
        prompt: The prompt to send to the LLM
        temperature: Sampling temperature (0.0-2.0)

    Returns:
        str: LLM response text
    """
    completion = _client.chat.completions.create(
        model=_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return completion.choices[0].message.content
```

### Configuration Variables

Add to `.env` file:

```bash
# LLM Provider Configuration
LLM_PROVIDER=openai          # Options: "openai" or "ollama"

# OpenAI Configuration (when LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-...        # Your OpenAI API key
OPENAI_MODEL=gpt-4o-mini     # Model to use

# Ollama Configuration (when LLM_PROVIDER=ollama)
OLLAMA_MODEL=llama3.1:8b     # Local model to use
OLLAMA_BASE_URL=http://localhost:11434/v1  # Optional: override default
```

### Benefits

- **Development**: Use Ollama for free, fast local iteration
- **Production**: Switch to OpenAI for higher quality
- **Privacy**: Keep sensitive papers local during development
- **Offline**: Work without internet connection
- **Cost**: Zero API costs during prototyping

### Recommended Ollama Models

For development and debugging:

- `llama3.1:8b` - Fast, good quality, well-rounded (4.7GB)
- `mistral:7b` - Very fast inference, good for iteration (4.1GB)
- `qwen2.5:7b` - Extremely fast, excellent for rapid testing (4.7GB)
- `deepseek-r1:8b` - Strong reasoning capabilities (4.7GB)

For production-quality local evaluation:

- `llama3.1:70b` - High quality, slower (40GB)
- `qwen2.5:32b` - Good balance of speed/quality (19GB)

---

## Phase 3: Dependency Management

### Current Dependencies (Feature Branch)

From `feature-llm-review/knowledge_graph/requirements.txt`:

```
openai>=1.0.0
python-dotenv>=1.0.0
docling>=1.0.0  # Already in main system
```

### Update Main Requirements

Check if already present in main `knowledge_graph/requirements.txt`:

```bash
grep -E "openai|python-dotenv" knowledge_graph/requirements.txt
```

If missing, add:

```bash
# LLM Integration
openai>=1.0.0
python-dotenv>=1.0.0
```

### Installation

```bash
cd knowledge_graph
pip install -r requirements.txt
```

### Ollama Setup (Optional)

For local development with Ollama:

1. **Install Ollama**:

   ```bash
   # macOS
   brew install ollama

   # Or download from https://ollama.ai
   ```

2. **Start Ollama service**:

   ```bash
   ollama serve
   ```

3. **Pull a model**:

   ```bash
   ollama pull llama3.1:8b
   ```

4. **Verify API**:
   ```bash
   curl http://localhost:11434/v1/models
   ```

---

## Phase 4: API Integration

### Import Additions

Add to `knowledge_graph/api.py` (after existing imports, around line 24):

```python
from llm_review.utils.text_loader import load_paper_text
from llm_review.utils.llm_runner import run_prompt
from llm_review.utils.result_merger import merge_rubric_outputs, synthesize_review
```

### Request Model

Add to models section (around line 168):

```python
class ReviewRequest(BaseModel):
    """Request model for paper review endpoint."""
    text: Optional[str] = None
    pdf_filename: Optional[str] = None

    @validator('text', 'pdf_filename')
    def check_one_provided(cls, v, values):
        """Ensure either text or pdf_filename is provided, but not both."""
        if not v and not values.get('text') and not values.get('pdf_filename'):
            raise ValueError('Either text or pdf_filename must be provided')
        return v
```

### Review Endpoint

Add to endpoints section (around line 1290):

```python
@app.post("/api/review")
async def review_paper(request: ReviewRequest):
    """
    Evaluate a scientific paper using 6 specialized rubrics.

    Args:
        request: ReviewRequest with either text or pdf_filename

    Returns:
        dict: Rubric responses, merged text, and final synthesis

    Example:
        POST /api/review
        {"pdf_filename": "paper.pdf"}

        POST /api/review
        {"text": "Paper markdown content..."}
    """
    try:
        # Load paper text
        if request.text:
            paper_text = request.text
        elif request.pdf_filename:
            paper_text = load_paper_text(request.pdf_filename)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'text' or 'pdf_filename' must be provided"
            )

        # Define rubrics
        rubric_files = [
            "prompts/rubric1_methodology.txt",
            "prompts/rubric2_reproducibility.txt",
            "prompts/rubric3_rigor.txt",
            "prompts/rubric4_data.txt",
            "prompts/rubric5_presentation.txt",
            "prompts/rubric6_references.txt"
        ]

        # Run each rubric
        rubric_responses = []
        for rubric_file in rubric_files:
            with open(rubric_file, 'r') as f:
                rubric_prompt = f.read()

            full_prompt = f"{rubric_prompt}\n\n---PAPER---\n{paper_text}"
            response = run_prompt(full_prompt)

            rubric_name = rubric_file.split('/')[-1].replace('.txt', '')
            rubric_responses.append({
                "rubric_name": rubric_name,
                "response": response
            })

        # Merge rubric outputs
        merged_text = merge_rubric_outputs(rubric_responses)

        # Generate final synthesis
        final_summary = synthesize_review(merged_text)

        return {
            "rubric_responses": rubric_responses,
            "merged_text": merged_text,
            "final_summary": final_summary
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")
```

---

## Phase 5: Configuration Setup

### Environment File

Create `knowledge_graph/.env` (or update existing):

```bash
# Dgraph Configuration
DGRAPH_ALPHA_URL=localhost:8080

# LLM Provider Selection
LLM_PROVIDER=openai          # Change to "ollama" for local development

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-...   # Your OpenAI API key
OPENAI_MODEL=gpt-4o-mini     # Cost-effective model

# Ollama Configuration (for local development)
OLLAMA_MODEL=llama3.1:8b     # Fast, good quality
# OLLAMA_MODEL=mistral:7b    # Alternative: faster iteration
# OLLAMA_MODEL=qwen2.5:7b    # Alternative: fastest feedback
```

### .gitignore

Ensure `.env` is in `.gitignore`:

```bash
echo ".env" >> .gitignore
```

### Provider Switching

Development workflow:

```bash
# Local development with Ollama (free, fast)
echo "LLM_PROVIDER=ollama" > knowledge_graph/.env

# Production with OpenAI (higher quality)
echo "LLM_PROVIDER=openai" > knowledge_graph/.env
echo "OPENAI_API_KEY=sk-..." >> knowledge_graph/.env
```

---

## Phase 6: Documentation

### Update API_ENDPOINTS.md

Add new section at the end of the file:

````markdown
## 6. Paper Review Endpoints

### Review Paper with LLM Evaluation

**POST** `/api/review`

Evaluate a scientific paper using 6 specialized rubrics and generate a comprehensive review. Supports both direct text input and PDF file processing.

**Request Body:**

```json
{
  "text": "Paper markdown content...", // Option 1: Direct text
  "pdf_filename": "paper.pdf" // Option 2: PDF file in papers/ directory
}
```
````

Note: Provide either `text` OR `pdf_filename`, not both.

**Response:**

```json
{
  "rubric_responses": [
    {
      "rubric_name": "rubric1_methodology",
      "response": "Evaluation of research design and methodology..."
    },
    {
      "rubric_name": "rubric2_reproducibility",
      "response": "Assessment of reproducibility and transparency..."
    }
    // ... 4 more rubrics
  ],
  "merged_text": "Combined evaluation text from all rubrics...",
  "final_summary": "Meta-review synthesis with actionable recommendations..."
}
```

**Evaluation Framework:**

The system evaluates papers using 6 specialized rubrics:

1. **Methodology & Research Design** - Experimental approach, controls, design quality
2. **Reproducibility & Transparency** - Data availability, protocol clarity, reproducibility
3. **Scientific Rigor** - Statistical validity, error handling, systematic approach
4. **Data Quality & Management** - Data collection, processing, quality control
5. **Presentation & Clarity** - Writing quality, figure clarity, organization
6. **References & Literature Review** - Citation completeness, literature coverage

Each rubric uses a 3-tier evaluation system:

- **Tier 1**: Quantitative descriptions (critical elements)
- **Tier 2**: Procedural context (supportive elements)
- **Tier 3**: Verification & references (integrative elements)

**Final Synthesis:**

After all rubrics complete, a meta-reviewer:

- Consolidates findings across all dimensions
- Eliminates duplicate observations
- Groups issues by theme (methodology, data, presentation, etc.)
- Generates actionable checklist for improvement

**LLM Provider Configuration:**

The system supports two LLM providers:

- **OpenAI** (Production): High-quality evaluations using GPT-4o-mini
- **Ollama** (Development): Free local evaluation for iteration

Configure via environment variables in `.env`:

```bash
# Use OpenAI (production)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Use Ollama (development)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
```

**Example Usage:**

```bash
# Review a paper from PDF
curl -X POST http://localhost:8001/api/review \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "A. Priyadarsini et al. 2023.pdf"}'

# Review paper from text
curl -X POST http://localhost:8001/api/review \
  -H "Content-Type: application/json" \
  -d '{"text": "# Abstract\n\nThis paper presents..."}'
```

**Performance:**

- Processing time: ~30-60 seconds per paper (6 rubrics + synthesis)
- OpenAI: ~$0.02-0.05 per paper review (GPT-4o-mini)
- Ollama: Free, local processing (varies by model and hardware)

**Use Cases:**

- Automated quality assessment of scientific papers
- Pre-submission self-review checklist generation
- Systematic evaluation across paper corpus
- Comparison of methodology across studies

````

### Create README for llm_review Module

Create `knowledge_graph/llm_review/README.md`:

```markdown
# Paper Review System

Automated scientific paper evaluation using LLM-based rubric assessment.

## Overview

This module provides comprehensive evaluation of scientific papers using 6 specialized rubrics that assess different aspects of research quality. A meta-reviewer then synthesizes all evaluations into actionable feedback.

## Architecture

### Rubrics

1. **Methodology** - Research design, controls, experimental approach
2. **Reproducibility** - Data availability, protocol clarity, replicability
3. **Rigor** - Statistical validity, error handling, systematic methods
4. **Data** - Data quality, collection methods, management practices
5. **Presentation** - Writing clarity, figure quality, organization
6. **References** - Citation completeness, literature coverage

### Processing Pipeline

````

Input (PDF/Text)OK†’ 6 Rubric EvaluationsOK†’ MergeOK†’ Meta-SynthesisOK†’ Final Review

````

## Usage

### Standalone Script

Process papers in batch mode:

```bash
cd knowledge_graph/llm_review
python main.py
````

Place PDFs in `papers/` directory. Results saved to `outputs/`.

### API Endpoint

Integrate with FastAPI server:

```python
POST /api/review
{
  "pdf_filename": "paper.pdf"
}
```

See `API_ENDPOINTS.md` for full documentation.

## Configuration

### Environment Variables

```bash
# Provider selection
LLM_PROVIDER=openai          # or "ollama"

# OpenAI (production)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Ollama (development)
OLLAMA_MODEL=llama3.1:8b
```

### LLM Providers

**OpenAI** (Default):

- High-quality evaluations
- Cost: ~$0.02-0.05 per paper
- Best for: Production, final reviews

**Ollama** (Optional):

- Free local processing
- Fast iteration during development
- Best for: Testing, prototyping, privacy-sensitive papers

## Development

### Switching Providers

```bash
# Development with Ollama
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=llama3.1:8b

# Production with OpenAI
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

### Recommended Models

Development (fast iteration):

- `llama3.1:8b` - Well-rounded
- `mistral:7b` - Very fast
- `qwen2.5:7b` - Fastest feedback

Production (high quality):

- OpenAI `gpt-4o-mini` - Cost-effective
- Ollama `llama3.1:70b` - Local high-quality

## Files

```
llm_review/
””€”€ main.py                    # Standalone batch processor
””€”€ prompts/                   # Rubric prompt templates
”‚  OK””€”€ rubric1_methodology.txt
”‚  OK””€”€ rubric2_reproducibility.txt
”‚  OK””€”€ rubric3_rigor.txt
”‚  OK””€”€ rubric4_data.txt
”‚  OK””€”€ rubric5_presentation.txt
”‚  OK””€”€ rubric6_references.txt
”‚  OK”””€”€ synthesizer.txt
”””€”€ utils/
   OK””€”€ text_loader.py         # PDFOK†’ markdown conversion
   OK””€”€ llm_runner.py          # LLM client abstraction
   OK””€”€ result_merger.py       # Output consolidation
   OK”””€”€ formatter.py           # Result formatting
```

````

---

## Phase 7: Testing

### Unit Tests

Create `knowledge_graph/tests/test_llm_review.py`:

```python
import pytest
from llm_review.utils.llm_runner import get_llm_client, run_prompt
from llm_review.utils.result_merger import merge_rubric_outputs

def test_llm_client_initialization():
    """Test LLM client can be initialized."""
    client, model = get_llm_client()
    assert client is not None
    assert model is not None

def test_prompt_execution():
    """Test basic prompt execution."""
    response = run_prompt("Say 'test successful' and nothing else.")
    assert len(response) > 0
    assert isinstance(response, str)

def test_rubric_merging():
    """Test rubric output merging."""
    rubric_responses = [
        {"rubric_name": "test1", "response": "Finding 1"},
        {"rubric_name": "test2", "response": "Finding 2"}
    ]
    merged = merge_rubric_outputs(rubric_responses)
    assert "Finding 1" in merged
    assert "Finding 2" in merged
````

Run tests:

```bash
cd knowledge_graph
pytest tests/test_llm_review.py -v
```

### Integration Tests

#### Test 1: Standalone Script

```bash
cd knowledge_graph/llm_review

# Create test paper
mkdir -p papers
echo "# Test Paper\n\nThis is a test." > papers/test.txt

# Run review
python main.py

# Check output
ls -lh outputs/
```

#### Test 2: API Endpoint with OpenAI

```bash
# Set OpenAI provider
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# Start API
cd knowledge_graph
python api.py

# Test endpoint (in another terminal)
curl -X POST http://localhost:8001/api/review \
  -H "Content-Type: application/json" \
  -d '{"text": "# Abstract\n\nThis paper presents a study on methanol production from methanotrophs using novel bioreactor designs. Methods involved culturing M. tundrae under controlled conditions with methane as the primary carbon source. Results showed 45% increase in methanol yield compared to batch processes."}' \
  | jq .
```

Expected output structure:

```json
{
  "rubric_responses": [...],
  "merged_text": "...",
  "final_summary": "..."
}
```

#### Test 3: API Endpoint with Ollama

```bash
# Start Ollama service
ollama serve

# Pull model
ollama pull llama3.1:8b

# Set Ollama provider
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=llama3.1:8b

# Restart API
cd knowledge_graph
python api.py

# Test endpoint
curl -X POST http://localhost:8001/api/review \
  -H "Content-Type: application/json" \
  -d '{"text": "# Abstract\n\nThis paper presents..."}' \
  | jq .
```

#### Test 4: Provider Switching

```bash
# Test switching between providers without code changes
export LLM_PROVIDER=ollama
python api.py &
curl -X POST http://localhost:8001/api/review -d '{"text": "..."}' | jq '.final_summary'
kill %1

export LLM_PROVIDER=openai
python api.py &
curl -X POST http://localhost:8001/api/review -d '{"text": "..."}' | jq '.final_summary'
kill %1
```

#### Test 5: Full Paper Review

```bash
# Test with actual paper from knowledge graph
curl -X POST http://localhost:8001/api/review \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "A. Priyadarsini et al. 2023.pdf"}' \
  -o review_output.json

# Examine results
jq '.rubric_responses[] | .rubric_name' review_output.json
jq '.final_summary' review_output.json
```

### Performance Testing

Compare OpenAI vs Ollama performance:

```bash
# Benchmark script
time curl -X POST http://localhost:8001/api/review \
  -H "Content-Type: application/json" \
  -d '{"text": "..."}'
```

Expected timings:

- OpenAI (gpt-4o-mini): 30-45 seconds
- Ollama (llama3.1:8b): 60-120 seconds (depends on hardware)
- Ollama (mistral:7b): 40-80 seconds

---

## Phase 8: Optional Enhancements

### Enhancement 1: Review History Storage

Store review results in Dgraph for future retrieval.

**Schema Extension**:

```graphql
type PaperReview {
  paper_id: string @index(exact)
  review_date: datetime
  rubric_responses: [RubricResponse]
  final_summary: string
  llm_provider: string
  llm_model: string
}

type RubricResponse {
  rubric_name: string
  response: string
}
```

**New Endpoint**:

```python
@app.get("/api/reviews/{paper_id}")
async def get_paper_reviews(paper_id: str):
    """Retrieve all reviews for a paper."""
    pass
```

### Enhancement 2: Streaming Responses

Implement Server-Sent Events for real-time rubric updates:

```python
@app.post("/api/review/stream")
async def review_paper_stream(request: ReviewRequest):
    """Stream rubric evaluations as they complete."""
    async def generate():
        for rubric in rubrics:
            response = run_prompt(rubric_prompt)
            yield json.dumps({"rubric": rubric, "response": response})

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Enhancement 3: Custom Rubric Selection

Allow users to select which rubrics to run:

```python
class ReviewRequest(BaseModel):
    text: Optional[str] = None
    pdf_filename: Optional[str] = None
    rubrics: List[str] = ["all"]  # or ["methodology", "rigor"]
```

### Enhancement 4: Comparative Analysis

Compare multiple papers side-by-side:

```python
@app.post("/api/review/compare")
async def compare_papers(paper_ids: List[str]):
    """Generate comparative review of multiple papers."""
    pass
```

### Enhancement 5: Model Performance Comparison

A/B test different models on same paper:

```python
@app.post("/api/review/compare-models")
async def compare_models(
    request: ReviewRequest,
    models: List[str] = ["gpt-4o-mini", "llama3.1:8b"]
):
    """Run review with multiple models and compare outputs."""
    pass
```

### Enhancement 6: Fallback Logic

Automatically fallback from Ollama to OpenAI on failure:

```python
def run_prompt_with_fallback(prompt: str) -> str:
    """Try Ollama first, fallback to OpenAI if it fails."""
    try:
        if os.getenv("LLM_PROVIDER") == "ollama":
            return run_prompt(prompt)
    except Exception as e:
        logger.warning(f"Ollama failed, falling back to OpenAI: {e}")
        # Temporarily switch to OpenAI
        os.environ["LLM_PROVIDER"] = "openai"
        return run_prompt(prompt)
```

---

## Implementation Checklist

### Phase 1: File Structure

- [ ] Copy llm_review/ directory from feature branch
- [ ] Create **init**.py files for Python packages
- [ ] Verify all prompt files present
- [ ] Verify all utility files present

### Phase 2: LLM Provider Abstraction

- [ ] Update llm_runner.py with provider abstraction
- [ ] Add get_llm_client() function
- [ ] Add OpenAI configuration
- [ ] Add Ollama configuration
- [ ] Test provider switching

### Phase 3: Dependencies

- [ ] Check current requirements.txt
- [ ] Add openai>=1.0.0 if missing
- [ ] Add python-dotenv>=1.0.0 if missing
- [ ] Install dependencies with pip
- [ ] Install Ollama (optional, for local development)
- [ ] Pull Ollama model (optional)

### Phase 4: API Integration

- [ ] Add imports to api.py
- [ ] Add ReviewRequest model
- [ ] Add POST /api/review endpoint
- [ ] Test endpoint with OpenAI
- [ ] Test endpoint with Ollama

### Phase 5: Configuration

- [ ] Create/update .env file
- [ ] Add OpenAI API key
- [ ] Add LLM provider selection
- [ ] Add model configuration
- [ ] Verify .env in .gitignore

### Phase 6: Documentation

- [ ] Add Section 6 to API_ENDPOINTS.md
- [ ] Create llm_review/README.md
- [ ] Document provider switching
- [ ] Document model recommendations
- [ ] Add usage examples

### Phase 7: Testing

- [ ] Write unit tests
- [ ] Test standalone script
- [ ] Test API with OpenAI
- [ ] Test API with Ollama
- [ ] Test provider switching
- [ ] Test full paper review
- [ ] Benchmark performance
- [ ] Validate all 6 rubrics run
- [ ] Verify synthesis quality

### Phase 8: Optional Enhancements

- [ ] Review history storage (optional)
- [ ] Streaming responses (optional)
- [ ] Custom rubric selection (optional)
- [ ] Comparative analysis (optional)
- [ ] Model comparison (optional)
- [ ] Fallback logic (optional)

---

## Success Criteria

1. **Functionality**: All 6 rubrics execute successfully and produce evaluations
2. **Provider Flexibility**: Can switch between OpenAI and Ollama via environment variable
3. **API Integration**: Review endpoint accessible at POST /api/review
4. **Documentation**: Complete API documentation with examples
5. **Testing**: All unit and integration tests pass
6. **Performance**: Review completes in reasonable time (<2 minutes)
7. **Quality**: Final synthesis provides actionable feedback

---

## Rollback Plan

If migration encounters critical issues:

1. **Remove llm_review/ directory**:

   ```bash
   rm -rf knowledge_graph/llm_review/
   ```

2. **Revert api.py changes**:

   ```bash
   git checkout knowledge_graph/api.py
   ```

3. **Remove added dependencies** (if they cause conflicts):

   ```bash
   pip uninstall openai python-dotenv
   ```

4. **Restore original requirements.txt**:
   ```bash
   git checkout knowledge_graph/requirements.txt
   ```

---

## Timeline Estimate

- **Phase 1-3** (Setup & Dependencies): 30 minutes
- **Phase 4** (API Integration): 1 hour
- **Phase 5** (Configuration): 15 minutes
- **Phase 6** (Documentation): 1 hour
- **Phase 7** (Testing): 1-2 hours
- **Phase 8** (Optional): Variable (per enhancement)

**Total Core Migration**: 3-4 hours

---

## Notes

- Ollama integration adds zero architectural complexity due to OpenAI API compatibility
- Same Python library (openai) used for both providers
- Provider switching requires only environment variable changes
- No message format or response parsing changes needed between providers
- Development workflow: iterate with Ollama, validate with OpenAI
- Cost savings: $0 during development, minimal cost in production

---

## Questions for Discussion

1. Should we default to OpenAI or Ollama for new developers?
2. Do we want to implement any Phase 8 enhancements immediately?
3. Should we add model performance comparison tool?
4. Do we want streaming responses for better UX?
5. Should we store review history in Dgraph?
