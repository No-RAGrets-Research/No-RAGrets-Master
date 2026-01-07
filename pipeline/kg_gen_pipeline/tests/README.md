# KG Pipeline Test Suite

Comprehensive testing framework for the Knowledge Graph extraction pipeline with relation-to-source traceability.

## Test Structure

```
tests/
├── run_tests.py           # Main test runner
├── unit/                  # Unit tests for individual components
│   ├── test_chunker.py    # Docling chunker tests
│   └── test_kg_extractor.py # KG extractor tests
└── integration/           # Integration and validation tests
    ├── test_pipeline.py   # End-to-end pipeline tests
    └── test_steps.py      # Step-by-step validation tests
```

## Running Tests

### Run All Tests

```bash
cd kg_gen_pipeline
python tests/run_tests.py
```

### Run Specific Test Categories

```bash
# Unit tests only
python tests/run_tests.py --unit

# Integration tests only
python tests/run_tests.py --integration

# Step validation only
python tests/run_tests.py --steps
```

### Run Individual Test Files

```bash
# Test chunker functionality
python tests/unit/test_chunker.py

# Test KG extractor functionality
python tests/unit/test_kg_extractor.py

# Test complete pipeline
python tests/integration/test_pipeline.py

# Validate pipeline steps
python tests/integration/test_steps.py
```

## Test Coverage

### Unit Tests

- **Chunker Tests**: Sentence segmentation, chunk creation, document offsets
- **KG Extractor Tests**: Entity finding, span calculation, cross-chunk detection

### Integration Tests

- **Pipeline Tests**: End-to-end processing, span traceability, performance
- **Step Validation**: Validates Steps 1-3 implementation and integration

## What Gets Tested

### Step 1: Sentence Segmentation

- PASS spaCy sentence boundary detection
- PASS Document offset calculation
- PASS Chunk structure with sentences array

### Step 2: Relation Span Mapping

- PASS Entity finding within sentences
- PASS Relation-to-span calculation
- PASS Confidence scoring
- PASS Single/multi-sentence span types

### Step 3: Cross-Chunk Detection

- PASS Multi-chunk entity tracking
- PASS Cross-chunk relation creation
- PASS Cross-chunk span structure
- PASS Integration with existing pipeline

### Pipeline Integration

- PASS End-to-end processing from Docling JSON to KG
- PASS Backward compatibility
- PASS Performance characteristics
- PASS Output format validation

## Expected Results

All tests should pass with output like:

```
🧪 KG Pipeline Test Suite
==================================================
=== RUNNING UNIT TESTS ===
PASS All unit tests passed!

=== RUNNING INTEGRATION TESTS ===
PASS All integration tests passed!

=== RUNNING STEP VALIDATION ===
PASS All step validations passed!

==================================================
 ALL TESTS PASSED!
```

## Test Data

Tests use a combination of:

- **Synthetic data**: Controlled test cases for specific functionality
- **Mock data**: Simulated pipeline results for edge case testing
- **Real data**: Actual processed files when available (e.g., Kulkarni paper)

## Adding New Tests

1. **Unit tests**: Add to `tests/unit/` for testing individual functions
2. **Integration tests**: Add to `tests/integration/` for testing component interactions
3. **Update test runner**: Add new test imports to `run_tests.py`

## Troubleshooting

### Import Errors

Make sure to run tests from the `kg_gen_pipeline` directory:

```bash
cd kg_gen_pipeline
python tests/run_tests.py
```

### Missing Dependencies

Ensure all required packages are installed:

- spacy
- ollama (for KG generation)
- Standard library modules

### Test File Paths

Tests look for output files in standard locations:

- `output/text_chunks/` for chunk files
- Uses temporary files for synthetic tests
