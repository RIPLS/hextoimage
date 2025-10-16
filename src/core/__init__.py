"""
Core functionality for hex reading and file analysis.

"""

from src.core.hex_reader import read_file_as_hex_data, get_hex_summary, HexData, HexLine
from src.core.analyzers import analyze_file_content, detect_file_signatures, get_supported_file_types
from src.core.exporters import extract_detected_files, create_extraction_report
from src.core.formatters import format_hex_data, format_hex_summary
from src.core.signatures import SIGNATURE_REGISTRY
