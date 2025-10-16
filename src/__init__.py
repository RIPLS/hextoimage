"""
HexToImage - A tool for analyzing hex data and extracting embedded files.

This package provides functionality to:
- Read and analyze binary files as hex data
- Detect embedded files by their signatures
- Extract detected files to disk
- Format hex data for display
"""

__version__ = "1.0.0"
__author__ = "Luis Suarez"

# Main API exports
from src.core.hex_reader import read_file_as_hex_data, get_hex_summary
from src.core.analyzers import analyze_file_content, get_supported_file_types
from src.core.exporters import extract_detected_files