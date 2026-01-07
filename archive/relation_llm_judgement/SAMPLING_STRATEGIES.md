# Enhanced Sampling Strategies for Phase 2

## Problems with Current Sampling

### 1. **Hub Entity Bias**

- Current: Samples only from top N most-connected entities
- Issue: Over-represents frequently mentioned entities (like author names)
- Miss: Less common but scientifically important entities

### 2. **Predicate Distribution**

- Current: Random sampling leads to uneven predicate distribution
- Issue: Common predicates (like "is author of") dominate
- Miss: Rare but important predicates (like "catalyzes", "inhibits")

### 3. **Sample Size**

- Current: 30 relations is too small for robust evaluation
- Need: 100-200 relations for statistical significance

### 4. **Source Paper Diversity**

- Current: 28/30 relations from same paper
- Issue: Paper-specific extraction quirks not identified
- Need: Better cross-paper distribution

---

## Recommended Sampling Strategies for Phase 2

### Strategy 1: **Stratified Random Sampling by Predicate**

Sample evenly across predicate types to ensure coverage of all relation types.

**Implementation**:

```python
# Get predicate distribution
predicates = get_all_predicates()

# Sample N relations per predicate type
for predicate in predicates:
    sample_n_relations(predicate=predicate, n=5-10)
```

**Benefits**:

- Ensures rare predicates are evaluated
- Identifies predicate-specific extraction issues
- More balanced evaluation

**Target**: 10 relations × 15-20 predicates = 150-200 relations

---

### Strategy 2: **Paper-Stratified Sampling**

Ensure relations come from multiple papers to test cross-document consistency.

**Implementation**:

```python
# Get all papers
papers = get_all_papers()

# Sample evenly from each paper
relations_per_paper = target_total // len(papers)
for paper in papers:
    sample_relations(paper=paper, n=relations_per_paper)
```

**Benefits**:

- Detects paper-specific extraction patterns
- Tests generalization across writing styles
- Validates cross-document consistency

**Target**: 20-30 relations × 5-10 papers = 100-300 relations

---

### Strategy 3: **Confidence Score Sampling**

Sample across confidence score ranges to validate confidence calibration.

**Implementation**:

```python
# Stratify by confidence buckets
confidence_buckets = [
    (0.0, 0.5),   # Low confidence
    (0.5, 0.75),  # Medium confidence
    (0.75, 0.9),  # High confidence
    (0.9, 1.0)    # Very high confidence
]

for low, high in confidence_buckets:
    sample_relations(confidence_range=(low, high), n=25)
```

**Benefits**:

- Tests if low-confidence = low-quality
- Validates extraction confidence scores
- Identifies confidence calibration issues

**Target**: 25 relations × 4 buckets = 100 relations

---

### Strategy 4: **Entity Type Diversity Sampling**

Sample based on entity types (chemical, organism, process, etc.).

**Implementation**:

```python
# Get entity type distributions
entity_types = ['chemical', 'organism', 'process', 'enzyme', 'location']

# Sample relations involving each entity type
for entity_type in entity_types:
    sample_relations(subject_type=entity_type, n=20)
    sample_relations(object_type=entity_type, n=20)
```

**Benefits**:

- Tests extraction quality across entity categories
- Identifies entity-type-specific issues
- More domain coverage

**Target**: 20 relations × 5 types × 2 (subject/object) = 200 relations

---

### Strategy 5: **Complexity-Based Sampling**

Sample based on relation complexity (sentence length, nesting, etc.).

**Implementation**:

```python
# Complexity metrics
complexity_levels = {
    'simple': 'single sentence, <50 words',
    'medium': 'single sentence, 50-100 words',
    'complex': 'multi-sentence or >100 words',
    'cross_chunk': 'spans multiple document sections'
}

for level in complexity_levels:
    sample_relations(complexity=level, n=25)
```

**Benefits**:

- Tests extraction on varying difficulty levels
- Identifies when extraction fails
- Validates source span quality

**Target**: 25 relations × 4 levels = 100 relations

---

### Strategy 6: **Error-Prone Pattern Targeting**

Specifically sample patterns known to cause extraction errors.

**Target Patterns**:

1. **Negations**: "does NOT", "cannot", "fails to"
2. **Conditionals**: "if", "when", "under conditions"
3. **Qualifiers**: "some", "most", "potentially", "rarely"
4. **Comparisons**: "more than", "less than", "similar to"
5. **Temporal**: "before", "after", "during", "then"
6. **Causal**: "causes", "leads to", "results in"

**Implementation**:

```python
error_patterns = ['NOT', 'cannot', 'if', 'some', 'potentially']
for pattern in error_patterns:
    sample_relations(text_contains=pattern, n=10)
```

**Benefits**:

- Directly tests challenging cases
- Validates negation/qualifier handling
- Identifies systematic errors

**Target**: 10 relations × 10 patterns = 100 relations

---

## Recommended Multi-Strategy Approach for Phase 2

### **Comprehensive Sample: 200 Relations**

**Distribution**:

1. **Predicate-Stratified** (60 relations)

   - 10 most common predicates × 3 relations
   - 10 rare predicates × 3 relations

2. **Paper-Stratified** (50 relations)

   - Top 5 papers × 10 relations each

3. **Confidence-Stratified** (40 relations)

   - Low (0-0.5): 10 relations
   - Medium (0.5-0.75): 10 relations
   - High (0.75-0.9): 10 relations
   - Very High (0.9-1.0): 10 relations

4. **Error-Pattern Targeted** (30 relations)

   - Negations: 10 relations
   - Conditionals: 10 relations
   - Qualifiers: 10 relations

5. **Random Baseline** (20 relations)
   - Completely random sample for comparison

---

## Implementation Priority

### **Phase 2A: Moderate Scale (100 relations)**

- 50 relations: Predicate-stratified
- 30 relations: Paper-stratified
- 20 relations: Error-pattern targeted

**Effort**: ~2-3 hours LLM inference (3 models × 100 relations)

### **Phase 2B: Large Scale (200 relations)**

- Full multi-strategy approach
- Add confidence stratification
- Add complexity stratification

**Effort**: ~4-6 hours LLM inference

---

## Benefits of Enhanced Sampling

1. **Statistical Validity**: Larger sample = reliable metrics
2. **Issue Detection**: Stratification reveals systematic problems
3. **Generalization**: Tests across papers, predicates, entity types
4. **Edge Case Coverage**: Error patterns target known failure modes
5. **Confidence Validation**: Tests if confidence scores are calibrated

---

## Tools Needed

I can create:

1. **Enhanced sampler module** with stratification strategies
2. **Phase 2 experiment script** (100-200 relations)
3. **Sampling report generator** showing distribution statistics
4. **Comparison tool** to analyze Phase 1 vs Phase 2 results
