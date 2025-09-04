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


def format_hex_line_compact(hex_line: HexLine) -> str:
    """
    Format a HexLine in compact format (no ASCII, shorter).
    
    Args:
        hex_line (HexLine): The hex line to format
    
    Returns:
        str: Compact formatted string
    """
    hex_offset = f"{hex_line.offset:08x}"
    hex_repr = ' '.join(f"{byte:02x}" for byte in hex_line.hex_bytes)
    return f"{hex_offset}: {hex_repr}"


def format_hex_data_compact(hex_data: HexData) -> str:
    """
    Format HexData in compact format.
    
    Args:
        hex_data (HexData): The hex data to format
    
    Returns:
        str: Compact formatted string
    """
    lines = [f"File: {hex_data.file_path} ({hex_data.file_size} bytes)"]
    
    for hex_line in hex_data.lines:
        lines.append(format_hex_line_compact(hex_line))
    
    return '\n'.join(lines)


def format_for_terminal(hex_data: HexData, show_summary: bool = False) -> str:
    """
    Format hex data optimized for terminal display.
    
    Args:
        hex_data (HexData): The hex data to format
        show_summary (bool): Whether to include summary at the end
    
    Returns:
        str: Terminal-optimized formatted string
    """
    result = format_hex_data(hex_data)
    
    if show_summary:
        from .hex_reader import get_hex_summary
        summary = get_hex_summary(hex_data)
        result += "\n\n" + format_hex_summary(summary)
    
    return result


def format_bytes_as_hex_string(data: bytes, separator: str = " ") -> str:
    """
    Format raw bytes as a hex string.
    
    Args:
        data (bytes): Raw bytes to format
        separator (str): Separator between hex values
    
    Returns:
        str: Hex string representation
    """
    return separator.join(f"{byte:02x}" for byte in data)


def format_file_header_info(hex_data: HexData, num_lines: int = 5) -> str:
    """
    Format just the file header information (first few lines).
    
    Args:
        hex_data (HexData): The hex data to format
        num_lines (int): Number of lines to show from the beginning
    
    Returns:
        str: Formatted header information
    """
    lines = [
        f"File: {hex_data.file_path}",
        f"Size: {hex_data.file_size} bytes",
        f"Showing first {min(num_lines, len(hex_data.lines))} lines:",
        "-" * 60
    ]
    
    for hex_line in hex_data.lines[:num_lines]:
        lines.append(format_hex_line(hex_line))
    
    if len(hex_data.lines) > num_lines:
        lines.append(f"... ({len(hex_data.lines) - num_lines} more lines)")
    
    return '\n'.join(lines)
