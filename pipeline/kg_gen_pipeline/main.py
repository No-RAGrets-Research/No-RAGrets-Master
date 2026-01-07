#!/usr/bin/env python3
"""
Main entry point for the Knowledge Graph Pipeline.

This script provides easy access to the pipeline orchestrator without needing
to navigate into the core/ directory.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main orchestrator
from core.pipeline_orchestrator import main

if __name__ == "__main__":
    main()