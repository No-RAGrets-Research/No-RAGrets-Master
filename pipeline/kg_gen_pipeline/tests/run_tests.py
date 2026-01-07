#!/usr/bin/env python3
"""
KG Pipeline Test Suite
Run comprehensive tests for the knowledge graph extraction pipeline.
"""

import sys
import os
import argparse
from pathlib import Path

# Add the parent directory to the Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_unit_tests():
    """Run unit tests for individual components."""
    print("=== RUNNING UNIT TESTS ===")
    
    try:
        from tests.unit.test_chunker import TestDoclingChunker
        from tests.unit.test_kg_extractor import TestKGExtractor
        
        # Run chunker tests
        print("\n--- Testing Docling Chunker ---")
        chunker_test = TestDoclingChunker()
        chunker_test.run_all_tests()
        
        # Run KG extractor tests
        print("\n--- Testing KG Extractor ---")
        extractor_test = TestKGExtractor()
        extractor_test.run_all_tests()
        
        print("\nAll unit tests passed!")
        return True
        
    except Exception as e:
        print(f"\nUnit tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_integration_tests():
    """Run integration tests for the full pipeline."""
    print("\n=== RUNNING INTEGRATION TESTS ===")
    
    try:
        from tests.integration.test_pipeline import TestPipeline
        
        pipeline_test = TestPipeline()
        pipeline_test.run_all_tests()
        
        print("\nAll integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\nIntegration tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_step_validation():
    """Run validation tests for each step of the pipeline."""
    print("\n=== RUNNING STEP VALIDATION ===")
    
    try:
        from tests.integration.test_steps import TestStepValidation
        
        step_test = TestStepValidation()
        step_test.run_all_steps()
        
        print("\nAll step validations passed!")
        return True
        
    except Exception as e:
        print(f"\nStep validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Run KG Pipeline Tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--steps", action="store_true", help="Run step validation only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    
    args = parser.parse_args()
    
    # Default to all tests if no specific test type specified
    if not any([args.unit, args.integration, args.steps]):
        args.all = True
    
    print("KG Pipeline Test Suite")
    print("=" * 50)
    
    success = True
    
    if args.unit or args.all:
        success &= run_unit_tests()
    
    if args.integration or args.all:
        success &= run_integration_tests()
    
    if args.steps or args.all:
        success &= run_step_validation()
    
    print("\n" + "=" * 50)
    if success:
        print("ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()