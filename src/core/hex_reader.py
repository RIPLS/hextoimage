"""
Core hex reading functionality.
This module provides functions to read files and convert them to hexadecimal data structures.
"""

import os
from typing import List, Dict, Optional, NamedTuple


class HexLine(NamedTuple):
    """Represents a single line of hex output."""
    offset: int
    hex_bytes: List[int]
    ascii_repr: str
    raw_bytes: bytes


class HexData(NamedTuple):
    """Complete hex data structure for a file."""
    file_path: str
    file_size: int
    lines: List[HexLine]
    total_bytes_read: int


def read_file_as_hex_data(file_path: str, bytes_per_line: int = 16) -> Optional[HexData]:
    """
    Read a file and return its content as structured hex data.
    
    Args:
        file_path (str): Path to the file to read
        bytes_per_line (int): Number of bytes to process per line (default: 16)
    
    Returns:
        HexData: Structured hex data, or None if error occurred

    """
    # Validate file exists and is readable
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")
    
    if not os.path.isfile(file_path):
        raise IsADirectoryError(f"'{file_path}' is not a file.")
    
    try:
        file_size = os.path.getsize(file_path)
        lines = []
        offset = 0
        
        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(bytes_per_line)
                if not chunk:
                    break
                
                # Convert bytes to list of integers
                hex_bytes = list(chunk)
                
                # Create ASCII representation (printable chars only)
                ascii_repr = ''.join(
                    chr(byte) if 32 <= byte <= 126 else '.'
                    for byte in chunk
                )
                
                # Create hex line
                hex_line = HexLine(
                    offset=offset,
                    hex_bytes=hex_bytes,
                    ascii_repr=ascii_repr,
                    raw_bytes=chunk
                )
                
                lines.append(hex_line)
                offset += len(chunk)
        
        return HexData(
            file_path=file_path,
            file_size=file_size,
            lines=lines,
            total_bytes_read=offset
        )
        
    except PermissionError as e:
        raise PermissionError(f"Permission denied reading file '{file_path}': {e}")
    except IOError as e:
        raise IOError(f"Error reading file '{file_path}': {e}")




def get_hex_summary(hex_data: HexData) -> Dict[str, any]:
    """
    Get a summary of hex data for analysis.
    
    Args:
        hex_data (HexData): The hex data to analyze
    
    Returns:
        Dict: Summary information
    """
    if not hex_data.lines:
        return {
            'file_path': hex_data.file_path,
            'file_size': hex_data.file_size,
            'total_lines': 0,
            'unique_bytes': set(),
            'byte_frequency': {},
            'printable_chars': 0,
            'non_printable_chars': 0
        }
    
    # Collect all bytes
    all_bytes = []
    printable_count = 0
    non_printable_count = 0
    
    for line in hex_data.lines:
        all_bytes.extend(line.hex_bytes)
        for byte in line.hex_bytes:
            if 32 <= byte <= 126:
                printable_count += 1
            else:
                non_printable_count += 1
    
    # Calculate frequency
    byte_frequency = {}
    for byte in all_bytes:
        byte_frequency[byte] = byte_frequency.get(byte, 0) + 1
    
    return {
        'file_path': hex_data.file_path,
        'file_size': hex_data.file_size,
        'total_lines': len(hex_data.lines),
        'unique_bytes': set(all_bytes),
        'byte_frequency': byte_frequency,
        'printable_chars': printable_count,
        'non_printable_chars': non_printable_count
    }
