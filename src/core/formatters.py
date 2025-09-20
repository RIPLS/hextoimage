"""
Formatting functions for hex data presentation.
This module handles all formatting and display logic for hex data.
"""

from typing import Dict, Any
from .hex_reader import HexData, HexLine


def format_hex_line(hex_line: HexLine, bytes_per_line: int = 16) -> str:
    """
    Format a HexLine into a string representation.
    
    Args:
        hex_line (HexLine): The hex line to format
        bytes_per_line (int): Expected bytes per line for padding
    
    Returns:
        str: Formatted string representation
    """
    # Format offset as 8-digit hex
    hex_offset = f"{hex_line.offset:08x}"
    
    # Convert bytes to hex representation
    hex_repr = ' '.join(f"{byte:02x}" for byte in hex_line.hex_bytes)
    
    # Pad hex representation to maintain alignment
    hex_repr = hex_repr.ljust(bytes_per_line * 3 - 1)
    
    # Format complete line
    return f"{hex_offset}  {hex_repr}  |{hex_line.ascii_repr}|"


def format_hex_data(hex_data: HexData) -> str:
    """
    Format complete HexData into a string representation.
    
    Args:
        hex_data (HexData): The hex data to format
    
    Returns:
        str: Complete formatted string
    """
    lines = [
        f"Reading file: {hex_data.file_path}",
        f"File size: {hex_data.file_size} bytes",
        "-" * 80
    ]
    
    # Add formatted hex lines
    for hex_line in hex_data.lines:
        lines.append(format_hex_line(hex_line))
    
    lines.extend([
        "-" * 80,
        f"Total bytes read: {hex_data.total_bytes_read}"
    ])
    
    return '\n'.join(lines)


def format_hex_summary(summary: Dict[str, Any]) -> str:
    """
    Format hex summary data into a readable string.
    
    Args:
        summary (Dict): Summary data from get_hex_summary()
    
    Returns:
        str: Formatted summary string
    """
    lines = [
        "=" * 50,
        "HEX DATA SUMMARY",
        "=" * 50,
        f"File: {summary['file_path']}",
        f"Size: {summary['file_size']} bytes",
        f"Lines: {summary['total_lines']}",
        f"Unique bytes: {len(summary['unique_bytes'])}",
        f"Printable chars: {summary['printable_chars']}",
        f"Non-printable chars: {summary['non_printable_chars']}",
        "",
        "Most frequent bytes:"
    ]
    
    # Show top 10 most frequent bytes
    if summary['byte_frequency']:
        sorted_bytes = sorted(
            summary['byte_frequency'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        for byte_val, count in sorted_bytes:
            percentage = (count / summary['file_size']) * 100
            char_repr = chr(byte_val) if 32 <= byte_val <= 126 else '.'
            lines.append(f"  0x{byte_val:02x} ('{char_repr}'): {count:,} times ({percentage:.1f}%)")
    
    lines.append("=" * 50)
    return '\n'.join(lines)