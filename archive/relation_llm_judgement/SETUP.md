# Setup and Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install required packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env to set your API endpoint (if different from default)
# Default: http://localhost:8001/api
```

### 3. Ensure Services are Running

**Knowledge Graph API:**

```bash
# Make sure the Knowledge Graph API is running
# Default: http://localhost:8001
```

**Ollama:**

```bash
# Start Ollama service
ollama serve

# The pilot script will automatically pull required models:
# - llama3.2:3b
# - mistral:7b
# - llama3.1:8b
```

### 4. Run the Pilot Experiment

```bash
python scripts/run_pilot.py
```

This will:

1. Connect to the Knowledge Graph API
2. Fetch top 5 hub entities
3. Sample ~30 relations from those entities
4. Run 3 judge models on each relation
5. Save results to `results/pilot_<timestamp>/`

### 5. Review Results

The experiment creates a timestamped directory with:

- `results.csv` - Flattened data for analysis
- `results_full.json` - Complete nested data structure
- `diversity_report.json` - Sample diversity metrics
- `summary_stats.json` - Summary statistics

## Configuration Options

Edit `.env` to customize:

```bash
API_BASE_URL=http://localhost:8001/api
NUM_HUB_ENTITIES=5
RELATIONS_PER_ENTITY=10
MAX_RELATIONS_TOTAL=50
```

Or modify directly in `scripts/run_pilot.py`:

```python
NUM_HUB_ENTITIES = 5
TARGET_RELATIONS = 30
PER_ENTITY_MAX = 10

TEXT_MODELS = [
    "llama3.2:3b",
    "mistral:7b",
    "llama3.1:8b"
]
```

## Using Different Models

### Text-based Models (any size)

```python
TEXT_MODELS = [
    "llama3.2:3b",      # Small, fast
    "mistral:7b",        # Medium
    "llama3.1:8b",       # Medium
    "qwen2.5:32b",       # Large
    "llama3.1:70b"       # Very large
]
```

### Vision Models (for image-based judging)

```python
# In run_pilot.py, set:
use_vision=True

# And specify vision models:
vision_models=["llama3.2-vision:11b", "llava:13b"]

# Also enable image downloading:
include_image=True
```

## Troubleshooting

### API Connection Error

```
Error connecting to API
```

**Solution:** Ensure Knowledge Graph API is running on http://localhost:8001

### Ollama Connection Error

```
Error pulling model
```

**Solution:** Ensure Ollama is running (`ollama serve`)

### Missing Models

The script will automatically pull missing models, but you can pre-pull:

```bash
ollama pull llama3.2:3b
ollama pull mistral:7b
ollama pull llama3.1:8b
```

### Import Errors

```
Import "requests" could not be resolved
```

**Solution:** Install dependencies: `pip install -r requirements.txt`

## Next Steps After Pilot

1. **Analyze Results:**

   - Open `results/pilot_*/results.csv` in Excel/Pandas
   - Look for patterns in model agreement
   - Identify problematic relations

2. **Manual Annotation:**

   - Select 50-100 relations for human labeling
   - Create ground truth labels
   - Compare against model judgments

3. **Expand to Phase 2:**

   - Increase `NUM_HUB_ENTITIES` to 20
   - Increase `TARGET_RELATIONS` to 200
   - Add more judge models
   - Enable vision models if useful

4. **Analysis:**
   - Calculate inter-model agreement (Cohen's Kappa)
   - Measure accuracy vs human labels
   - Identify best-performing models
   - Find systematic extraction errors

## Project Structure

```
.
””€”€ src/
”‚  OK””€”€ __init__.py
”‚  OK””€”€ api_client.py       # Knowledge Graph API client
”‚  OK””€”€ sampler.py          # Hub entity and relation sampling
”‚  OK””€”€ judge.py            # Ollama judge interface
”‚  OK””€”€ prompts.py          # Prompt templates
”‚  OK”””€”€ storage.py          # Data storage utilities
””€”€ scripts/
”‚  OK”””€”€ run_pilot.py        # Main pilot script
””€”€ results/                # Experiment outputs (timestamped)
””€”€ data/                   # Optional input data
””€”€ requirements.txt
””€”€ .env.example
””€”€ EXPERIMENT_PLAN.md      # Detailed experiment design
””€”€ SETUP.md               # This file
”””€”€ README.md
```
