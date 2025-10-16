"""
Core functionality for hex reading and file analysis.

"""

from .hex_reader import read_file_as_hex_data, get_hex_summary, HexData, HexLine
from .analyzers import analyze_file_content, detect_file_signatures, get_supported_file_types
from .exporters import extract_detected_files, create_extraction_report
from .formatters import format_hex_data, format_hex_summary
from .signatures import SIGNATURE_REGISTRY
