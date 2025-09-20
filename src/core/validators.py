from typing import Optional


def validate_jpeg_format(binary_data: bytes, start_pos: int, end_pos: Optional[int]) -> float:
    """
    Validate JPEG format with advanced header analysis.
    
    Args:
        binary_data (bytes): Complete binary data
        start_pos (int): Start position of detected file
        end_pos (Optional[int]): End position of detected file (if known)
    
    Returns:
        float: Confidence score (0.0 to 1.0)
    """
    confidence = 1.0
    
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


def validate_webp_format(binary_data: bytes, start_pos: int, end_pos: Optional[int]) -> float:
    """
    Validate WEBP format by checking RIFF container structure.
    
    Args:
        binary_data (bytes): Complete binary data
        start_pos (int): Start position of detected file
        end_pos (Optional[int]): End position of detected file (if known)
    
    Returns:
        float: Confidence score (0.0 to 1.0)
    """
    confidence = 1.0
    
    # WEBP validation: ensure RIFF is followed by WEBP
    if start_pos + 12 <= len(binary_data):
        riff_header = binary_data[start_pos:start_pos + 12]
        if len(riff_header) >= 12:
            if riff_header[8:12] != b'WEBP':
                confidence *= 0.1  # Very low confidence if not WEBP after RIFF
        else:
            confidence *= 0.2
    else:
        confidence *= 0.2
    
    return confidence


def validate_gif_format(binary_data: bytes, start_pos: int, end_pos: Optional[int]) -> float:
    """
    Validate GIF format by checking version information.
    
    Args:
        binary_data (bytes): Complete binary data
        start_pos (int): Start position of detected file
        end_pos (Optional[int]): End position of detected file (if known)
    
    Returns:
        float: Confidence score (0.0 to 1.0)
    """
    confidence = 1.0
    
    # GIF validation: check for proper GIF header
    if start_pos + 6 <= len(binary_data):
        gif_header = binary_data[start_pos:start_pos + 6]
        if gif_header not in [b'GIF87a', b'GIF89a']:
            confidence *= 0.3  # Lower confidence for incomplete GIF header
    else:
        confidence *= 0.2
    
    return confidence


def validate_png_format(binary_data: bytes, start_pos: int, end_pos: Optional[int]) -> float:
    """
    Validate PNG format by checking PNG signature and IHDR chunk.
    
    Args:
        binary_data (bytes): Complete binary data
        start_pos (int): Start position of detected file
        end_pos (Optional[int]): End position of detected file (if known)
    
    Returns:
        float: Confidence score (0.0 to 1.0)
    """
    confidence = 1.0
    
    # PNG validation: check for IHDR chunk after PNG signature
    if start_pos + 16 <= len(binary_data):
        # PNG signature is 8 bytes, then should come IHDR chunk
        ihdr_chunk = binary_data[start_pos + 8:start_pos + 16]
        if len(ihdr_chunk) >= 8:
            # Check if IHDR chunk follows (4 bytes length + "IHDR")
            if ihdr_chunk[4:8] != b'IHDR':
                confidence *= 0.4  # Lower confidence if IHDR not found
        else:
            confidence *= 0.3
    else:
        confidence *= 0.2
    
    return confidence


def validate_tiff_format(binary_data: bytes, start_pos: int, end_pos: Optional[int]) -> float:
    """
    Validate TIFF format by checking byte order and magic number.
    
    Args:
        binary_data (bytes): Complete binary data
        start_pos (int): Start position of detected file
        end_pos (Optional[int]): End position of detected file (if known)
    
    Returns:
        float: Confidence score (0.0 to 1.0)
    """
    confidence = 1.0
    
    # TIFF validation: check for proper TIFF header structure
    if start_pos + 8 <= len(binary_data):
        tiff_header = binary_data[start_pos:start_pos + 8]
        
        # Check for little-endian (II*\x00) or big-endian (MM\x00*) TIFF
        if len(tiff_header) >= 4:
            if tiff_header[:4] == b'II*\x00':
                # Little-endian TIFF - check IFD offset
                if len(tiff_header) >= 8:
                    # IFD offset should be reasonable (usually 8 or higher)
                    ifd_offset = int.from_bytes(tiff_header[4:8], byteorder='little')
                    if ifd_offset < 8 or ifd_offset > len(binary_data) - start_pos:
                        confidence *= 0.5  # Lower confidence for invalid IFD offset
                else:
                    confidence *= 0.3
            elif tiff_header[:4] == b'MM\x00*':
                # Big-endian TIFF - check IFD offset
                if len(tiff_header) >= 8:
                    ifd_offset = int.from_bytes(tiff_header[4:8], byteorder='big')
                    if ifd_offset < 8 or ifd_offset > len(binary_data) - start_pos:
                        confidence *= 0.5  # Lower confidence for invalid IFD offset
                else:
                    confidence *= 0.3
            else:
                confidence *= 0.2  # Unknown TIFF variant
        else:
            confidence *= 0.2
    else:
        confidence *= 0.2
    
    return confidence


# Registry mapping file types to their validation functions
VALIDATOR_REGISTRY = {
    'JPEG': validate_jpeg_format,
    'WEBP': validate_webp_format,
    'GIF': validate_gif_format,
    'PNG': validate_png_format,
    'TIFF': validate_tiff_format,
}


def get_validator(file_type: str):
    """
    Get the validation function for a specific file type.
    
    Args:
        file_type (str): File type name (e.g., 'JPEG', 'PNG')
    
    Returns:
        Callable or None: Validation function or None if not found
    """
    return VALIDATOR_REGISTRY.get(file_type)


def validate_format(file_type: str, binary_data: bytes, start_pos: int, end_pos: Optional[int]) -> float:
    """
    Generic validation function that dispatches to the appropriate validator.
    
    Args:
        file_type (str): File type name
        binary_data (bytes): Complete binary data
        start_pos (int): Start position of detected file
        end_pos (Optional[int]): End position of detected file (if known)
    
    Returns:
        float: Confidence score (1.0 if no validator found, otherwise validator result)
    """
    validator = get_validator(file_type)
    if validator:
        return validator(binary_data, start_pos, end_pos)
    return 1.0  # Default confidence if no validator exists
