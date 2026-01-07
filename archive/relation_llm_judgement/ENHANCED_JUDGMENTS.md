# Enhanced Judgment Dimensions for Relation Extraction Evaluation

## Current Dimensions (Pilot)

- ✅ **Accuracy**: Is the triple correct? (Binary)
- ✅ **Faithfulness**: How directly stated? (1-5)
- ✅ **Boundary Quality**: Are entity spans correct? (1-5)

---

## Recommended Additional Dimensions

### 1. **Contextual Completeness** (Critical)

**Question**: Does the extracted relation capture all necessary context?

**Scale**: 1-5

- 1 = Missing critical context (misleading)
- 3 = Partially complete
- 5 = Fully captures necessary context

**Example**:

- Text: "Methanotrophs convert methane to methanol using MMO enzymes at 30°C"
- Extraction: `Methanotrophs → convert → methane`
- Issue: Missing "to methanol" (the product) - Score: 2/5

**Why Critical**: Under-specified relations can be factually correct but scientifically useless.

---

### 2. **Relation Specificity** (Critical)

**Question**: Is the predicate specific enough for the domain?

**Scale**: 1-5

- 1 = Too generic (e.g., "is related to")
- 3 = Moderately specific
- 5 = Domain-specific and precise

**Example**:

- Bad: `Enzyme → acts on → Substrate` (Score: 2/5)
- Good: `MMO → hydroxylates → methane` (Score: 5/5)

**Why Critical**: Vague predicates reduce graph utility for scientific queries.

---

### 3. **Causal/Temporal Accuracy** (Critical)

**Question**: If the relation implies causation or sequence, is it correct?

**Scale**: Binary or 1-5

- Does the relation correctly represent cause/effect?
- Is temporal ordering preserved?

**Example**:

- Text: "Methane oxidation produces methanol, which is then converted to formaldehyde"
- Wrong: `formaldehyde → produces → methanol` (reversed causality)
- Right: `methanol → is converted to → formaldehyde`

**Why Critical**: Wrong directionality breaks reasoning chains.

---

### 4. **Quantitative Accuracy** (Critical for Science)

**Question**: If the relation includes numerical values, are they correct?

**Scale**: 1-5

- 1 = Numbers wrong or missing units
- 3 = Approximately correct
- 5 = Exact with proper units

**Example**:

- Text: "Methane has 28-34 times higher GWP than CO2 over 100 years"
- Extraction: `Methane → has → 28-34 times higher global warming potential...`
- Check: Are the numbers (28-34, 100 years) preserved correctly?

**Why Critical**: Scientific precision depends on accurate quantitative data.

---

### 5. **Ambiguity/Specificity of Entities** (Critical)

**Question**: Are the entities disambiguated properly?

**Scale**: 1-5

- 1 = Highly ambiguous (e.g., "it", "they", "the enzyme")
- 3 = Somewhat specific
- 5 = Fully specified with qualifiers

**Example**:

- Ambiguous: `Type I methanotrophs → use → MMO` (which MMO? pMMO or sMMO?)
- Specific: `Type I methanotrophs → use → particulate MMO (pMMO)`

**Why Critical**: Ambiguous entities reduce graph linkability and query precision.

---

### 6. **Co-reference Resolution** (Medium Priority)

**Question**: Are pronouns/references correctly resolved to entities?

**Scale**: Binary

- Correct entity resolution?
- Pronoun correctly mapped?

**Example**:

- Text: "Methanotrophs oxidize methane. They use MMO for this reaction."
- Question: Is "They" correctly mapped to "Methanotrophs"?

**Why Important**: Affects extraction from multi-sentence spans.

---

### 7. **Negation Handling** (Critical)

**Question**: Is negation correctly captured?

**Scale**: Binary

- Is "NOT" relation properly represented?
- False positive extraction from negative statements?

**Example**:

- Text: "Type II methanotrophs do NOT produce methanol efficiently"
- Wrong: `Type II methanotrophs → produce → methanol` ❌
- Right: Should either skip or mark as negative relation

**Why Critical**: Extracting false positives from negative statements is a major error.

---

### 8. **Hallucination Detection** (Critical)

**Question**: Is this relation actually stated or inferred/hallucinated?

**Scale**: 1-5

- 1 = Completely hallucinated
- 2 = Heavily inferred (not directly stated)
- 3 = Implied with strong context
- 4 = Paraphrased but accurate
- 5 = Directly stated

**Example**:

- Text: "Methanotrophs are used in methanol production"
- Hallucination: `Methanotrophs → produce large quantities of → methanol` (added "large quantities")

**Why Critical**: Distinguishes actual vs. inferred knowledge.

---

### 9. **Qualifier/Modifier Preservation** (Medium Priority)

**Question**: Are important qualifiers preserved?

**Scale**: 1-5

- Conditions, constraints, or exceptions captured?
- Probability/certainty markers preserved?

**Example**:

- Text: "Some methanotrophs can potentially convert methane under anaerobic conditions"
- Loss: `Methanotrophs → convert → methane` (missing "some", "potentially", "anaerobic")

**Why Important**: Qualifiers affect applicability of knowledge.

---

### 10. **Cross-Document Consistency** (Advanced)

**Question**: Is this relation consistent with same relation extracted from other papers?

**Scale**: 1-5

- Compare same triple across multiple sources
- Flag contradictions

**Example**:

- Paper A: `Methane → has GWP of → 28 times CO2`
- Paper B: `Methane → has GWP of → 34 times CO2`
- Flag: Inconsistency (actually both correct for different time horizons)

**Why Important**: Validates extraction reliability and identifies evolving knowledge.

---

## Recommended Priority for Implementation

### **Phase 2 (Next - High Priority)**

1. ✅ **Contextual Completeness** - Are relations fully specified?
2. ✅ **Relation Specificity** - Are predicates specific enough?
3. ✅ **Negation Handling** - False positives from negative statements?
4. ✅ **Hallucination Detection** - Distinguishes actual vs. inferred

### **Phase 3 (Medium Priority)**

5. **Causal/Temporal Accuracy** - Correct directionality
6. **Quantitative Accuracy** - Numbers and units preserved
7. **Entity Specificity** - Proper disambiguation

### **Phase 4 (Advanced)**

8. **Co-reference Resolution** - Pronoun mapping
9. **Qualifier Preservation** - Conditions and constraints
10. **Cross-Document Consistency** - Multi-source validation

---

## Implementation Suggestions

### For Phase 2, Add These Questions to Prompts:

```
4. Contextual Completeness: Does the relation include all necessary context from the source? (1-5)
5. Relation Specificity: Is the predicate specific and meaningful? (1-5 where 1=too generic, 5=precise)
6. Negation Check: Is this extracted from a negative/contradictory statement? (Yes/No)
7. Hallucination Level: How directly is this stated vs. inferred? (1=hallucinated, 5=directly stated)
```

### Modified Prompt Template:

```
**Questions:**
1. Is this relation accurately represented in the sentence? (Yes/No)
2. Faithfulness: How directly is this stated? (1-5)
3. Boundary Quality: Are entity boundaries correct? (1-5)
4. Contextual Completeness: Does it capture all necessary context? (1-5)
5. Predicate Specificity: Is the predicate specific enough? (1-5)
6. Negation: Is this from a negative statement that shouldn't be extracted? (Yes/No)
7. Hallucination: Is this directly stated or inferred/hallucinated? (1-5)
```

---

## Expected Impact

Adding these dimensions will help identify:

- **Over-generalized relations** (low specificity scores)
- **Under-specified relations** (low completeness scores)
- **Hallucinated knowledge** (low hallucination scores)
- **False positives from negations** (negation flags)

This creates a more robust evaluation that catches subtle quality issues beyond simple accuracy.
