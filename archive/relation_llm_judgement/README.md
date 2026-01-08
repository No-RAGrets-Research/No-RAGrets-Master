# Relation LLM Judgement

Multi-model LLM judge experiment for evaluating knowledge graph relation extraction quality.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment:

```bash
cp .env.example .env
# Edit .env with your API endpoint
```

3. Ensure Ollama is running:

```bash
ollama serve
```

## Project Structure

```
.
””€”€ src/
”‚  OK””€”€ api_client.py       # Knowledge Graph API client
”‚  OK””€”€ sampler.py          # Hub entity and relation sampling
”‚  OK””€”€ judge.py            # Ollama judge interface
”‚  OK””€”€ prompts.py          # Prompt templates
”‚  OK”””€”€ storage.py          # Data storage utilities
””€”€ scripts/
”‚  OK”””€”€ run_pilot.py        # Pilot experiment script
””€”€ data/                   # Input data (if any)
””€”€ results/                # Experiment outputs
”””€”€ EXPERIMENT_PLAN.md      # Detailed experiment design
```

## Running the Pilot

```bash
python scripts/run_pilot.py
```

This will:

- Fetch top 5 hub entities
- Sample 25-50 relations
- Run 2-3 judge models
- Save results to `results/pilot_<timestamp>.csv`
  LLMs Judge our Relations
