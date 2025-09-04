"""
File analysis and signature detection module.
This module provides functionality to detect and analyze different file types
within binary data based on their signatures (magic numbers).
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, NamedTuple
from .hex_reader import HexData
from .signatures import FileSignature, SIGNATURE_REGISTRY

# Represents a detected file within the binary data.
@dataclass
class DetectedFile(NamedTuple):
    file_type: str
    start_offset: int
    end_offset: Optional[int]
    size: Optional[int]
    signature: FileSignature
    confidence: float = 1.0  # 0.0 to 1.0, where 1.0 is highest confidence

@dataclass
class AnalysisResult:
    source_file: str
    source_file_size: int
    detected_files: List[DetectedFile]
    analysis_summary: Dict[str, int]  # file_type -> count


def find_pattern_positions(data: bytes, pattern: bytes) -> List[int]:
    """
    Find all positions where a pattern occurs in the data.
    
    Args:
        data (bytes): Binary data to search in
        pattern (bytes): Pattern to search for
    
    Returns:
        List[int]: List of byte positions where pattern starts
    """
    positions = []
    start = 0
    
    while True:
        pos = data.find(pattern, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1
    
    return positions


def reconstruct_binary_data(hex_data: HexData) -> bytes:
    """
    Reconstruct complete binary data from HexData structure.
    
    Args:
        hex_data (HexData): Structured hex data
    
    Returns:
        bytes: Complete binary data
    """
    binary_data = bytearray()
    
    for line in hex_data.lines:
        binary_data.extend(line.raw_bytes)
    
    return bytes(binary_data)


def find_signature_positions(hex_data: HexData, signature: FileSignature) -> List[Tuple[int, Optional[int]]]:
    """
    Find all positions where a file signature occurs in the hex data.
    
    Args:
        hex_data (HexData): Hex data to search in
        signature (FileSignature): File signature to search for
    
    Returns:
        List[Tuple[int, Optional[int]]]: List of (start_pos, end_pos) tuples
        end_pos is None if end_pattern is not found or not defined
    """
    # Reconstruct binary data
    binary_data = reconstruct_binary_data(hex_data)
    
    # Find start positions
    start_positions = find_pattern_positions(binary_data, signature.start_pattern)
    
    # Special case for TIFF: also search for big-endian variant
    if signature.file_type == 'TIFF':
        big_endian_pattern = b'MM\x00*'  # Big-endian TIFF
        big_endian_positions = find_pattern_positions(binary_data, big_endian_pattern)
        start_positions.extend(big_endian_positions)
    
    # Special case for WEBP: need to verify it's actually WEBP after RIFF
    if signature.file_type == 'WEBP':
        webp_positions = []
        for pos in start_positions:
            # Check if "WEBP" follows after RIFF header (at position + 8)
            if pos + 12 <= len(binary_data) and binary_data[pos + 8:pos + 12] == b'WEBP':
                webp_positions.append(pos)
        start_positions = webp_positions
    
    if not start_positions:
        return []
    
    results = []
    
    for start_pos in start_positions:
        end_pos = None
        
        # If signature has end pattern, try to find it
        if signature.end_pattern:
            # Search for end pattern after start position
            search_start = start_pos + len(signature.start_pattern)
            end_pattern_pos = binary_data.find(signature.end_pattern, search_start)
            
            if end_pattern_pos != -1:
                # End position is after the end pattern
                end_pos = end_pattern_pos + len(signature.end_pattern)
        
        results.append((start_pos, end_pos))
    
    return results


# Validate a detected file and return confidence score.
def validate_detected_file(binary_data: bytes, start_pos: int, end_pos: Optional[int], signature: FileSignature) -> float:
    confidence = 1.0
    
    # Check minimum size requirement
    if end_pos is not None:
        file_size = end_pos - start_pos
        if file_size < signature.min_size:
            confidence *= 0.3  # Low confidence for too small files
    elif signature.min_size > 0:
        # If we don't have end position but have min_size requirement
        remaining_data = len(binary_data) - start_pos
        if remaining_data < signature.min_size:
            confidence *= 0.5
    
    # Additional validation for specific file types
    if signature.file_type == 'WEBP':
        # WEBP validation: ensure RIFF is followed by WEBP
        if start_pos + 12 <= len(binary_data):
            riff_header = binary_data[start_pos:start_pos + 12]
            if len(riff_header) >= 12:
                if riff_header[8:12] != b'WEBP':
                    confidence *= 0.1  # Very low confidence if not WEBP after RIFF
        else:
            confidence *= 0.2
    
    elif signature.file_type == 'GIF':
        # GIF validation: check for proper GIF header
        if start_pos + 6 <= len(binary_data):
            gif_header = binary_data[start_pos:start_pos + 6]
            if gif_header not in [b'GIF87a', b'GIF89a']:
                confidence *= 0.3  # Lower confidence for incomplete GIF header
        else:
            confidence *= 0.2
    
    elif signature.file_type == 'JPEG':
        # JPEG validation: check for proper JPEG variants
        if start_pos + 10 <= len(binary_data):
            jpeg_header = binary_data[start_pos:start_pos + 10]
            
            # Check for different JPEG variants
            if len(jpeg_header) >= 4:
                fourth_byte = jpeg_header[3]
                
                # JPEG/JFIF: FF D8 FF E0
                if fourth_byte == 0xE0 and start_pos + 14 <= len(binary_data):
                    if binary_data[start_pos + 6:start_pos + 10] == b'JFIF':
                        confidence *= 1.0  # High confidence for JFIF
                    else:
                        confidence *= 0.8  # Lower confidence if not JFIF after E0
                
                # JPEG/Exif: FF D8 FF E1
                elif fourth_byte == 0xE1 and start_pos + 10 <= len(binary_data):
                    if binary_data[start_pos + 10:start_pos + 14] == b'Exif':
                        confidence *= 1.0  # High confidence for Exif
                    else:
                        confidence *= 0.8  # Lower confidence if not Exif after E1
                
                # JPEG/SPIFF: FF D8 FF E8
                elif fourth_byte == 0xE8 and start_pos + 14 <= len(binary_data):
                    if binary_data[start_pos + 6:start_pos + 11] == b'SPIFF':
                        confidence *= 1.0  # High confidence for SPIFF
                    else:
                        confidence *= 0.7
                
                # Generic JPEG: FF D8 FF DB (quantization table)
                elif fourth_byte == 0xDB:
                    confidence *= 0.9  # Good confidence for quantization table
                
                # Generic JPEG: FF D8 FF C0 (start of frame)
                elif fourth_byte == 0xC0:
                    confidence *= 0.9  # Good confidence for start of frame
                
                # Other JPEG markers (C1, C2, etc.)
                elif 0xC0 <= fourth_byte <= 0xCF:
                    confidence *= 0.8  # Decent confidence for other SOF markers
                
                # Unknown fourth byte - might still be JPEG but lower confidence
                else:
                    confidence *= 0.6
            else:
                confidence *= 0.3  # Very low confidence if header too short
        else:
            confidence *= 0.2  # Low confidence if not enough data
    
    return confidence


def detect_file_signatures(hex_data: HexData, target_types: Optional[List[str]] = None) -> List[DetectedFile]:
    """
    Detect all file signatures in the hex data.
    
    Args:
        hex_data (HexData): Hex data to analyze
        target_types (Optional[List[str]]): Specific file types to look for.
                                          If None, searches for all known types.
    
    Returns:
        List[DetectedFile]: List of detected files
    """
    if target_types is None:
        target_types = list(SIGNATURE_REGISTRY.keys())
    
    detected_files = []
    binary_data = reconstruct_binary_data(hex_data)
    
    for file_type in target_types:
        if file_type not in SIGNATURE_REGISTRY:
            continue
        
        signature = SIGNATURE_REGISTRY[file_type]
        positions = find_signature_positions(hex_data, signature)
        
        for start_pos, end_pos in positions:
            # Calculate file size if we have end position
            file_size = None
            if end_pos is not None:
                file_size = end_pos - start_pos
            
            # Validate the detected file
            confidence = validate_detected_file(binary_data, start_pos, end_pos, signature)
            
            detected_file = DetectedFile(
                file_type=file_type,
                start_offset=start_pos,
                end_offset=end_pos,
                size=file_size,
                signature=signature,
                confidence=confidence
            )
            
            detected_files.append(detected_file)
    
    # Sort by start position
    detected_files.sort(key=lambda x: x.start_offset)
    
    return detected_files

# Perform complete file content analysis
def analyze_file_content(hex_data: HexData, target_types: Optional[List[str]] = None) -> AnalysisResult:
    detected_files = detect_file_signatures(hex_data, target_types)
    
    # Create summary
    summary = {}
    for detected_file in detected_files:
        file_type = detected_file.file_type
        summary[file_type] = summary.get(file_type, 0) + 1
    
    return AnalysisResult(
        source_file=hex_data.file_path,
        source_file_size=hex_data.file_size,
        detected_files=detected_files,
        analysis_summary=summary
    )


# Get list of supported file types
def get_supported_file_types() -> List[str]:
    return list(SIGNATURE_REGISTRY.keys())