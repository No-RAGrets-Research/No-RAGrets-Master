"""
Core pipeline components for Knowledge Graph extraction.

This module contains the main pipeline components for processing scientific papers
into knowledge graphs with both text and visual extraction capabilities.
"""

from .pipeline_orchestrator import MasterKGOrchestrator
from .text_kg_extractor import ChunkKGExtractor
from .visual_kg_extractor import VisualTripleExtractor
from .figure_detection import FigureDetector
from .visual_kg_formatter import VisualKGFormatter
from .pdf_converter import DoclingConverter

__all__ = [
    'MasterKGOrchestrator',
    'ChunkKGExtractor', 
    'VisualTripleExtractor',
    'FigureDetector',
    'VisualKGFormatter',
    'DoclingConverter'
]