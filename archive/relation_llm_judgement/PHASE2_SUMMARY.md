# Phase 2: Enhanced Sampling Implementation

## What I Built

I've created a comprehensive Phase 2 experiment framework that addresses the sampling limitations from your pilot study. Here's what's ready to use:

---

## New Components

### 1. **Enhanced Sampler** (`src/enhanced_sampler.py`)

A sophisticated sampling module with 6 different strategies:

- **Predicate-Stratified**: Sample evenly across relation types (e.g., "is author of", "catalyzes", "inhibits")
- **Paper-Stratified**: Ensure relations come from multiple papers, not just one
- **Confidence-Stratified**: Sample across confidence score ranges (low/medium/high/very high)
- **Error-Pattern Targeted**: Find relations with negations, conditionals, qualifiers
- **Random Baseline**: Completely random sample for comparison
- **Multi-Strategy**: Combine all strategies in one comprehensive sample

### 2. **Phase 2 Experiment Script** (`scripts/run_phase2.py`)

Production-ready script that:

- Samples 100 relations by default (configurable to 200)
- Uses multi-strategy approach (40 predicate, 30 paper, 20 confidence, 10 random)
- Runs same 3 models from pilot (llama3.2:3b, mistral:7b, llama3.1:8b)
- Generates comprehensive diversity analysis
- Saves detailed sampling report

### 3. **Comparison Script** (`scripts/compare_phases.py`)

Analyzes differences between Phase 1 (pilot) and Phase 2:

- Agreement rate changes
- Model performance deltas
- Predicate distribution comparison
- Sample diversity metrics
- Strategy effectiveness analysis

### 4. **Documentation** (`SAMPLING_STRATEGIES.md`)

Complete guide explaining:

- Problems with hub entity sampling
- 6 sampling strategies with implementations
- Recommended multi-strategy approach
- Benefits and targets for each strategy

---

## How to Run Phase 2

### Quick Start (100 relations, ~1.5 hours)

```bash
source venv/bin/activate
python scripts/run_phase2.py
```

### Configuration Options

Edit `scripts/run_phase2.py` to customize:

```python
# Sample size
TARGET_SAMPLE_SIZE = 100  # Or 200 for Phase 2B

# Strategy distribution
STRATEGY_DISTRIBUTION = {
    'predicate_stratified': 40,   # 40 relations across predicates
    'paper_stratified': 30,       # 30 relations across papers
    'confidence_stratified': 20,  # 20 confidence-based
    'error_patterns': 0,          # Set to 30 for targeted edge cases (slower)
    'random_baseline': 10         # 10 completely random
}
```

### After Running

Compare Phase 1 vs Phase 2:

```bash
python scripts/compare_phases.py \
    results/pilot_20251119_193809 \
    results/phase2_YYYYMMDD_HHMMSS
```

---

## Expected Improvements Over Phase 1

### Phase 1 (Pilot - 30 relations)

- ❌ Hub entity bias (28/30 from same paper)
- ❌ Predicate imbalance (~3 unique predicates)
- ❌ Single paper focus
- ✅ High agreement (90%)
- ✅ High faithfulness (4.80-5.00/5)

### Phase 2 (Enhanced - 100 relations)

- ✅ Multi-paper coverage (~5-10 papers)
- ✅ Predicate diversity (~15-20 unique predicates)
- ✅ Confidence calibration testing
- ✅ Error pattern targeting
- ⚠️ Agreement may drop (reveals edge cases)
- 🎯 More realistic quality assessment

---

## What Phase 2 Will Tell You

### 1. **Generalization Performance**

- Do models maintain accuracy across different predicates?
- Are some predicate types more challenging?

### 2. **Confidence Calibration**

- Do low-confidence extractions actually have lower quality?
- Can you trust the confidence scores?

### 3. **Cross-Document Consistency**

- Do models perform equally well across papers?
- Are there paper-specific extraction issues?

### 4. **Edge Case Detection**

- Which sampling strategy reveals most disagreements?
- What types of relations cause confusion?

### 5. **Sampling Strategy Effectiveness**

- Does predicate-stratified find more issues than random?
- Which strategy is most efficient for quality assessment?

---

## Incremental Approach

### Option A: Conservative (Recommended First)

```python
TARGET_SAMPLE_SIZE = 100
STRATEGY_DISTRIBUTION = {
    'predicate_stratified': 50,
    'paper_stratified': 30,
    'random_baseline': 20,
    'confidence_stratified': 0,  # Skip for now
    'error_patterns': 0           # Skip (slow)
}
```

**Time**: ~1.5 hours  
**Focus**: Predicate & paper diversity

### Option B: Comprehensive

```python
TARGET_SAMPLE_SIZE = 150
STRATEGY_DISTRIBUTION = {
    'predicate_stratified': 50,
    'paper_stratified': 40,
    'confidence_stratified': 30,
    'error_patterns': 20,
    'random_baseline': 10
}
```

**Time**: ~3 hours  
**Focus**: All strategies including edge cases

### Option C: Maximum Scale (Phase 2B)

```python
TARGET_SAMPLE_SIZE = 200
STRATEGY_DISTRIBUTION = {
    'predicate_stratified': 80,
    'paper_stratified': 50,
    'confidence_stratified': 40,
    'error_patterns': 20,
    'random_baseline': 10
}
```

**Time**: ~4-5 hours  
**Focus**: Statistical significance

---

## Files Generated

Phase 2 creates:

```
results/phase2_YYYYMMDD_HHMMSS/
├── results_full.json           # Complete judgment data
├── results_summary.csv         # Flattened for analysis
├── statistics.json             # Performance metrics
└── sampling_report.json        # Strategy distribution & diversity
```

---

## Next Steps After Phase 2

1. **Run Phase 2** with Option A (100 relations)
2. **Compare to Phase 1** using `compare_phases.py`
3. **Analyze disagreements** by sampling strategy
4. **Decide**: Scale to 200 or implement enhanced judgment dimensions?
5. **Manual annotation** of ~20-30 relations for ground truth

---

## Benefits Over Phase 1

| Aspect            | Phase 1         | Phase 2        |
| ----------------- | --------------- | -------------- |
| Sample Size       | 30              | 100-200        |
| Sampling          | Hub entity only | Multi-strategy |
| Predicates        | ~3 unique       | ~15-20 unique  |
| Papers            | 1-2             | 5-10           |
| Edge Cases        | Rare            | Targeted       |
| Statistical Power | Low             | Medium-High    |
| Diversity Report  | No              | Yes            |
| Strategy Analysis | No              | Yes            |

---

## Ready to Run!

Everything is implemented and ready. Just run:

```bash
source venv/bin/activate
python scripts/run_phase2.py
```

Then compare:

```bash
python scripts/compare_phases.py \
    results/pilot_20251119_193809 \
    results/phase2_<timestamp>
```

Let me know if you want to adjust the configuration or add any features!
