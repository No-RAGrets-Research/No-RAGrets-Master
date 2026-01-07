| Dimension                                       | Description                                                               | Evaluation Points (LLM-Checkable)                                                                                        |
| ----------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **1️⃣ Methodological Transparency**     | Whether the method description includes complete and quantitative details | Whether time, temperature, concentration, speed, supplier, etc. are specified; whether supplementary materials are cited |
| **2️⃣ Reproducibility & Traceability**  | Whether others can reproduce the experiment based on the description      | Whether catalog numbers, strain numbers, buffer pH, etc. are included                                                    |
| **3️⃣ Scientific Rigor**                | Whether the experimental design logic is sound                            | Whether control groups, repeated experiments, and statistical significance explanations are provided                     |
| **4️⃣ Data Completeness & Consistency** | Whether data in the document matches the description                      | Whether figures and text are consistent and units standardized                                                           |
| **5️⃣ Presentation & Documentation**    | Whether descriptions are clear and unambiguous                            | Whether sentences are clear, parameter units consistent, and tables/figures properly formatted and annotated             |

| Rubric                                    | Suggested Level of Granularity | Example Description                                                                                                              |
| ----------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| **Methodological Transparency**     | Medium–High                   | Should specify time, temperature, rpm, pH, concentration, and volume, but general descriptions like “as usual” are acceptable. |
| **Reproducibility & Traceability**  | High                           | Must clearly indicate brand, catalog number, ATCC number, strain name, etc.                                                      |
| **Scientific Rigor**                | Medium                         | Not required to state “several replications,” but should mention replication and control.                                      |
| **Data Completeness & Consistency** | Medium                         | Don’t need to check every figure/table for consistency; only verify whether numbers, units, and figures match.                  |
| **Presentation & Documentation**    | Low                            | Check whether the language is clear and whether appendices/references are cited; formal formatting is not required.              |

# Level 1: Master Prompt

You will analyze it in five independent dimensions:

1. Methodological Transparency
2. Reproducibility & Traceability
3. Scientific Rigor
4. Data Completeness & Consistency
5. Presentation & Documentation

⚠️ Boundaries:

- You evaluate *reporting quality and completeness*, not *scientific correctness or data authenticity*.
- You must never claim whether the experiment “works,” “fails,” or “is true.”
- Missing information should be marked as “not reported,” not “incorrect.”

Each dimension produces a short diagnostic list.
After all dimensions are processed, synthesize them into an Evidence-Based Review Summary.

# Level 2: Rubric Modules

## Methodological Transparency

### Goal

Assess whether each experimental procedure in the paper is described with **enough quantitative and contextual detail** for another laboratory to replicate it.

You are checking  **reporting completeness** , not  **scientific correctness** .

If information is missing, mark it as *“not reported”* rather than *“incorrect.”*

### TIER 1 – Quantitative Descriptions (Critical Layer)

These items must be explicitly reported with numbers + units.

**Check for:**

* Mass / volume / concentration values (e.g., 100 mg, 10 mL, 0.1 M).
* Centrifugation: speed (g or rpm) + time (+ temperature if relevant).
* Shaking incubation / microbe growth: temperature (°C), rpm, duration (h), and medium type.
* PCR conditions: temperatures for denaturation / annealing / extension, step durations, cycle count, and reaction volume.
* Media and buffer composition (including pH and any modifications).
* Optical density or growth phase indicator (e.g., OD₆₀₀ = 0.8).
* Supplier and catalog number for all purchased chemicals or reagents.
* Microbial strain or plasmid identifier (e.g.,  *ATCC 3153* , Addgene #12345).
* Reference to supplementary materials if detailed protocols are provided there.

**Cross-links:**

Missing Tier 1 details → also affects *Reproducibility & Traceability* and  *Scientific Rigor* .

### TIER 2 – Procedural & Environmental Context (Supportive Layer)

These details enhance reproducibility but may vary by study type.

**Check for:**

* Controlled environment parameters (O₂/CO₂ level, humidity, light cycle, sterility conditions).
* Sample collection and storage details (time point, temperature, medium, number of freeze-thaw cycles).
* Instrument model, manufacturer, or calibration method (for centrifuge, spectrophotometer, PCR machine, etc.).
* Safety or ethical statements (if pathogens, animal or human materials are used).
* Logical ordering and clarity of experimental steps (method should be reconstructable in sequence).

**Cross-links:**

Tier 2 supports evaluation in *Scientific Rigor* (controls and design) and *Presentation & Documentation* (flow and clarity).

### TIER 3 – Verification & Reference (Integrative Layer)

Assesses whether the methods are anchored to external or internal verification sources.

**Check for:**

* Statement of replicates or repeat experiments (biological vs technical).
* References to established protocols or standard methods (e.g., “following Sambrook et al., 2012”).
* Accessibility of data or supplementary materials (link, repository name, identifier).
* Software or instrument version numbers for analysis tools (LC-MS, NMR, sequencing software).
* Mention of internal validation tests or cross-lab comparison (if any).

**Cross-links:**

Tier 3 feeds into *Data Completeness & Consistency* and overall meta-review summary.

### Output format

✅ Good Practices
⚠️ Missing / Weak Points
💡 Improvement Suggestions

---

## Reproducibility & Traceability

### Goal

Evaluate whether **materials, biological entities, and procedures** are **traceable, identifiable, and reproducible** by an independent lab.

This rubric builds directly on  *Methodological Transparency* , focusing on  **source verification, identification, and procedural reproducibility** .

You are judging  *reporting sufficiency for replication* , not  *whether replication was actually done* .

### TIER 1 – Material & Reagent Traceability (Critical Layer)

**Check for:**

* Each chemical, compound, or reagent lists:
  * Common name (e.g., “Sodium nitrate”),
  * Supplier / manufacturer (e.g., Sigma Aldrich),
  * Catalog or batch number.
* Microbial strains, plasmids, or cell lines include:
  * Full species or strain name,
  * Source collection and identifier (e.g.,  *Methylosinus trichosporium* , ATCC 3153),
  * If modified, a note describing modification or origin.
* Buffers or media traceable to either a cited protocol or a clearly defined composition.
* Reference to commercial kits (PCR, extraction, etc.) includes kit name and supplier.
* Instrumentation traceability: model and manufacturer stated for at least critical instruments (centrifuge, incubator, spectrophotometer).

**Cross-links:**

* Depends on quantitative details from  *Methodological Transparency Tier 1* .
* Missing supplier/identifier info also lowers *Data Consistency* reliability.

### TIER 2 – Procedural Reproducibility (Supportive Layer)

**Check for:**

* All steps necessary for replication are present in logical order.
* Use of standard or previously published methods is cited (e.g., “following protocol X”).
* Critical environmental or setup parameters (temperature, pressure, light, gas) are reported or referenced.
* Any random or stochastic elements (e.g., random seed, inoculation timing) have description of control strategy.
* Clear distinction between biological vs technical replicates.

**Cross-links:**

* Shared with *Scientific Rigor* (control design, replication).
* Relies on *Transparency Tier 2* (contextual environment).

### TIER 3 – Verification & Accessibility (Integrative Layer)

**Check for:**

* Raw or processed data availability statement (e.g., “Data available in Supplementary Table S2”).
* Mention of repository accession numbers for sequences, structures, or materials (GenBank, PDB, Addgene).
* Any code, scripts, or analysis pipelines linked with version or DOI.
* Description of how reproducibility was internally validated (e.g., “repeated twice independently”).
* Ethical or legal compliance for strain/material use (import/export or biosafety statements).

**Cross-links:**

* Supports *Data Completeness & Consistency* (data linkage) and *Presentation & Documentation* (referencing clarity).

### Output format

✅ Good Practices

+ [“All reagents listed with supplier and catalog #.”]
+ [“Strain ATCC 3153 and plasmid Addgene #11234 properly identified.”]

⚠️ Missing / Weak Points
– [“No supplier information for buffers.”]
– [“Plasmid source not provided.”]
– [“No repository accession for sequence data.”]

💡 Improvement Suggestions

- Add supplier + catalog # for all reagents.
- Include culture collection IDs for microbial strains.
- Provide accession numbers for genetic or structural data.
- Link raw data or code repositories.

---

## Scientific Rigor

### **Goal**

Evaluate whether the experimental design and reasoning in the paper are **methodologically sound, logically consistent, and statistically supported.**

This rubric **does not judge correctness of the science itself** —

you are only assessing whether the described design, controls, and analysis **meet expected standards of rigor** in microbiology and chemical materials research.

### **TIER 1 – Experimental Design Soundness (Critical Layer)**

**Check for:**

* Each experiment has a **clear hypothesis or objective** stated.
* Experimental **variables and controls** are clearly defined (positive/negative control, blank, baseline condition).
* The **number of replicates** (biological vs technical) is mentioned or inferable.
* **Independent repeats** of key experiments are described (“performed in triplicate”).
* **Statistical test methods** are identified (e.g., t-test, ANOVA, regression).
* The **statistical significance** threshold or confidence interval is stated (e.g., p < 0.05).
* Units, scales, and normalization procedures are consistent across all comparisons.

**Cross-links:**

* Depends on *Methodological Transparency Tier 1–2* (conditions & replicates).
* Missing control or replicate info propagates to *Reproducibility* warnings.

### **TIER 2 – Logical Consistency & Interpretation (Supportive Layer)**

**Check for:**

* The experimental steps follow a **logical cause–effect sequence** that matches the research question.
* Results logically follow from methods (no unexplained jumps between sections).
* Control results are used to validate experimental effects.
* If unexpected results appear, authors provide  **plausible explanations or limitations** .
* All figures/tables support claims made in text (no over-interpretation).
* No self-contradiction between results and discussion.

**Cross-links:**

* Overlaps with *Data Completeness & Consistency* for figure–text alignment.
* Supports *Presentation & Documentation* by improving narrative coherence.

### **TIER 3 – Analytical & Validation Rigor (Integrative Layer)**

**Check for:**

* Proper data analysis workflow is described (software, model, or algorithm named).
* Statistical or computational validation described (cross-validation, baseline comparison, calibration curve).
* Mentions of **error estimation** (SD, SEM, confidence interval).
* Discussion includes known limitations or possible confounders.
* Reproducibility validation (e.g., “findings confirmed by independent batch or lab”).
* Consistency across replicates or trials explicitly reported.

**Cross-links:**

* Integrates with *Reproducibility & Traceability Tier 3* (verification).
* Results transparency supports *Data Completeness* scoring.

### **Output Format**

✅ Good Practices

+ [“Control and experimental groups clearly defined; three biological replicates reported.”]
+ [“Statistical tests (ANOVA, t-test) and p-values provided.”]
+ [“Limitations discussed in final paragraph.”]

⚠️ Missing / Weak Points
– [“No negative control described.”]
– [“Number of replicates not mentioned.”]
– [“Statistical analysis method not stated.”]
– [“Discussion overclaims beyond data shown.”]

💡 Improvement Suggestions

- Add details on replicate count and control group.
- Specify statistical methods used and corresponding p-values.
- Include a short discussion of potential confounding factors.
- Ensure claims match presented data.

---

## Data Completeness & Consistency

### **Goal**

Evaluate whether all reported data, figures, tables, and numerical results in the paper are  **complete, internally consistent, and correspond to the described methods and results** .

You are **not** judging whether the numbers are “correct,” only whether the **reporting and alignment** are clear, complete, and traceable.

### **TIER 1 – Data Presence & Alignment (Critical Layer)**

**Check for:**

* All figures/tables referenced in text are actually present.
* All numerical results mentioned in text are traceable to a figure/table.
* Each figure/table has a  **title, legend, and labeled axes with units** .
* Units are consistent with those used in the Methods section (e.g., mg/L vs g/L).
* Statistical notations (mean ± SD, error bars) appear where applicable.
* Every mentioned experiment reports corresponding output data (no “method without result”).
* Data range and sample size (n) are explicitly stated if relevant.
* Figures and tables are logically ordered and referenced in sequence (e.g., “see Fig. 2a”).

**Cross-links:**

* Relies on *Transparency* (parameter reporting) and *Rigor* (replicate consistency).
* Missing figure-text alignment may flag under  *Presentation & Documentation* .

### **TIER 2 – Numerical & Logical Consistency (Supportive Layer)**

**Check for:**

* Numerical values are consistent across text, figure legends, and tables.
* Derived values (ratios, yields, efficiencies) are mathematically consistent with raw numbers.
* Reported replicates (n) match across figures and methods.
* Units are not mixed or misapplied within same dataset.
* Figure panels (a/b/c) correspond to proper captions and narrative order.
* If control data are shown, corresponding control description exists in Methods.
* Reported error margins and statistical symbols (p-values) appear consistently.

**Cross-links:**

* Shared with *Scientific Rigor* (statistical tests) and *Transparency* (reported units).
* Impacts *Reproducibility* if quantitative details are inconsistent.

### **TIER 3 – Data Accessibility & Metadata (Integrative Layer)**

**Check for:**

* Data availability statement provided (e.g., “Raw data available in Supplementary Table S3”).
* Supplementary materials include full numeric datasets or summary tables.
* File formats and repository identifiers are listed (DOI, Zenodo, Dryad, etc.).
* Metadata (units, sample descriptions, instrument parameters) accompany raw data.
* Version or timestamp included for data files or software-generated outputs.
* If figures are composites, sources or merges are identified (“Images from same sample set”).

**Cross-links:**

* Integrates directly with *Reproducibility & Traceability Tier 3* (data repositories).
* Supports *Presentation & Documentation* for transparency of appendices.

### **Output Format**

✅ Good Practices

+ [“All figures referenced and include axis labels with units.”]
+ [“Statistical data presented as mean ± SD with n = 3 indicated.”]
+ [“Raw data available in Supplementary Table S2.”]

⚠️ Missing / Weak Points
– [“Figure 3b lacks unit labels on y-axis.”]
– [“Error bars shown but number of replicates not specified.”]
– [“Values in Table 1 inconsistent with text description.”]
– [“No data availability statement found.”]

💡 Improvement Suggestions

- Add explicit units to all figure axes.
- Ensure numerical values match between tables and text.
- Include replicate number and statistical notation.
- Provide data availability or repository link.

## Presentation & Documentation

## **Goal**

Evaluate whether the paper is written and organized in a  **clear, professional, and accessible manner** , such that all methods, data, and conclusions can be followed without ambiguity.

You are checking  **communication quality** , not the research correctness.

### **TIER 1 – Structural Organization (Critical Layer)**

**Check for:**

* Presence and clarity of main sections:  *Abstract, Introduction, Methods, Results, Discussion, Conclusion* .
* Logical order between sections (Methods → Results → Discussion).
* Each section begins with a clear purpose statement and connects to the next one.
* Methods section clearly separated from Results (no mixing of findings inside protocol descriptions).
* Figure and table captions are descriptive and self-contained.
* Section titles and subtitles use consistent hierarchical style.

**Cross-links:**

* Depends on information from *Data Completeness* (for figure placement and references).
* Supports clarity evaluation in *Scientific Rigor* (logical flow).

### **TIER 2 – Clarity & Language Quality (Supportive Layer)**

**Check for:**

* Sentences concise, unambiguous, and free of grammatical errors.
* Consistent use of scientific terminology and units.
* Avoids vague phrases (“appropriate amount”, “as usual method”).
* Defines all abbreviations at first mention.
* Numbers and symbols formatted consistently throughout (°C, μL, ×10⁻³).
* Use of active vs passive voice is consistent and scientifically neutral.
* Any non-English terms or trade names properly italicized or annotated.

**Cross-links:**

* Shares terminology consistency with  *Methodological Transparency* .
* Affects *Reproducibility* and *Rigor* if meaning is obscured by vague language.

### **TIER 3 – Referencing & Supplementary Documentation (Integrative Layer)**

**Check for:**

* All citations formatted consistently (APA, ACS, or journal style).
* References accurately correspond to in-text citations (no missing numbers or duplicates).
* Supplementary files or appendices clearly cited in text (“see Table S1”, “Supplementary Figure 2”).
* Figures and tables numbered consistently across main and supplementary materials.
* Document metadata (title page, author affiliations, keywords) present and formatted properly.
* If data repositories or software are cited, include DOI or URL links.

**Cross-links:**

* Integrates with *Data Completeness Tier 3* for repository verification.
* Supports *Reproducibility Tier 3* by linking to external resources.

### **Output Format**

✅ Good Practices

+ [“Paper sections clearly structured from Introduction to Conclusion.”]
+ [“Figure captions fully describe methods and units.”]
+ [“References formatted consistently per ACS style.”]

⚠️ Missing / Weak Points
– [“Methods and Results merged in one section.”]
– [“Unclear terminology: ‘appropriate amount’ used instead of numeric value.”]
– [“Supplementary tables not referenced in main text.”]
– [“Inconsistent citation numbering between text and reference list.”]

💡 Improvement Suggestions

- Separate Methods and Results sections.
- Replace vague phrases with quantitative details.
- Ensure all supplementary materials are explicitly referenced.
- Standardize reference format and citation order.

---

## **RUBRIC 6 – Reference Extraction**

### **Goal**

Extract all reference entries and in-text citations mentioned in the paper,

then list them in a structured and standardized format for downstream use

(e.g., citation verification, literature cross-check, or knowledge graph linking).

You are **not** evaluating reference quality — only collecting and formatting them.

### **Prompt Template**

SYSTEM ROLE:
You are a citation extraction assistant specializing in scientific papers.
Your goal is to extract and standardize all reference information mentioned in the text.

TASK:
Given the following paper text, identify all:

- Full reference entries (from the References / Bibliography section).
- In-text citations (e.g., “(Smith et al., 2020)”, “[12]”, “(Ref. 5)”).

PROCESS:

1. First, extract all full reference entries appearing in the reference section.

   - Preserve author names, year, title, journal, volume, pages, DOI (if present).
   - If multiple formats are mixed (APA, ACS, numbered), normalize to a consistent style (APA-like).
   - Remove duplicates and fix minor formatting issues (extra punctuation, missing commas).
2. Then, extract all in-text citations and map them (if possible) to their corresponding reference entries.
3. If the paper uses numbered citations ([1], [2], etc.), preserve both the **citation number** and the **reference content**.If the paper uses author–year style, list by author/year.
4. Output in the following structure:

---

📚 **Extracted References**

[1] Author(s). (Year). *Title.* Journal, Volume(Issue), Pages. DOI (if available).
[2] ...

---

🔗 **In-text Citations Found**

- (Smith et al., 2020) → matches [5]
- [3] → “Doe et al., Nature, 2019”

---

🧭 **Unmatched Citations**
[List any citation mentioned in text but not found in reference list.]

---

💡 **Notes**
[Any notes such as “References truncated”, “Non-standard citation style detected”, etc.]

RULES:

- Maintain academic formatting.
- Do not invent missing information; only normalize what is visible.
- If no reference section exists, list all in-text citations found.
- Keep consistent capitalization and punctuation.

---

# Level 3: **Evidence-Based Review Summary**

You are a scientific meta-reviewer.
You have received five structured evaluation reports from domain experts, each covering one rubric:

1. Methodological Transparency
2. Reproducibility & Traceability
3. Scientific Rigor
4. Data Completeness & Consistency
5. Presentation & Documentation

Each report lists:
✅ Good Practices
⚠️ Missing / Weak Points
💡 Improvement Suggestions

Your task:

- Synthesize all five into a single unified review.
- Remove duplicate points.
- Preserve factual details (parameters, techniques, conditions).
- Present the result in the following format:

🧪 **Evidence-Based Review Summary**

🔬 Good Practices
[List consolidated strengths across rubrics.]

⚠️ Missing or Weak Points
[List missing or unclear items, grouped by theme.]

💡 Improvement Checklist
[Concise actionable recommendations.]

📄 Notes
[Cross-cutting comments about clarity, data linkage, or supplementary materials.]

Keep language objective, concise, and fact-based.
Do not assign scores or subjective judgments.
