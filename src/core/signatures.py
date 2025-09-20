from typing import Dict, Optional, Callable
from .validators import (
    validate_jpeg_format,
    validate_webp_format,
    validate_gif_format,
    validate_png_format,
    validate_tiff_format
)

class FileSignature:
    """
    Represents a file type signature with start/end patterns.
    
    Attributes:
        file_type (str): Human-readable file type name (e.g., 'JPEG', 'PNG')
        extension (str): File extension without dot (e.g., 'jpg', 'png')
        start_pattern (bytes): Binary pattern that marks file beginning
        end_pattern (Optional[bytes]): Binary pattern that marks file end (if applicable)
        description (str): Human-readable description
        min_size (int): Minimum valid file size in bytes (helps filter false positives)
        validator (Callable): Advanced validation function for this format
    """
    file_type: str
    extension: str
    start_pattern: bytes
    end_pattern: Optional[bytes] = None
    description: str = ""
    min_size: int = 0
    validator: Optional[Callable[[bytes, int, Optional[int]], float]] = None

# Registry of known file signatures
SIGNATURE_REGISTRY: Dict[str, FileSignature] = {
    'JPEG': FileSignature(
        file_type='JPEG',
        extension='jpg',
        start_pattern=b'\xFF\xD8\xFF',  # All JPEG files start with FF D8 FF
        end_pattern=b'\xFF\xD9',
        description='JPEG Image File (JFIF/Exif/Generic)',
        min_size=100,  # Minimum realistic JPEG size
        validator=validate_jpeg_format
    ),
    'PNG': FileSignature(
        file_type='PNG',
        extension='png',
        start_pattern=b'\x89PNG\r\n\x1a\n',
        end_pattern=b'IEND\xaeB`\x82',
        description='Portable Network Graphics Image',
        min_size=50,  # Minimum realistic PNG size
        validator=validate_png_format
    ),
    'GIF': FileSignature(
        file_type='GIF',
        extension='gif',
        start_pattern=b'GIF8',  # GIF87a or GIF89a
        end_pattern=b'\x00\x3B',  # GIF trailer
        description='Graphics Interchange Format Image',
        min_size=35,  # Minimum GIF size (header + minimal data)
        validator=validate_gif_format
    ),
    'WEBP': FileSignature(
        file_type='WEBP',
        extension='webp',
        start_pattern=b'RIFF',  # RIFF container format
        end_pattern=None,  # WEBP uses RIFF chunks, no single end marker
        description='WebP Image Format',
        min_size=20,  # Minimum WEBP size
        validator=validate_webp_format
    ),
    'TIFF': FileSignature(
        file_type='TIFF',
        extension='tiff',
        start_pattern=b'II*\x00',  # Little-endian TIFF (also supports b'MM\x00*' for big-endian)
        end_pattern=None,  # TIFF doesn't have a standard end marker
        description='Tagged Image File Format',
        min_size=26,  # Minimum TIFF size
        validator=validate_tiff_format
    )
    # 'PDF': FileSignature(
    #     file_type='PDF',
    #     extension='pdf',
    #     start_pattern=b'%PDF',
    #     end_pattern=b'%%EOF',
    #     description='Portable Document Format',
    #     min_size=200
    # ),
    # 'ZIP': FileSignature(
    #     file_type='ZIP',
    #     extension='zip',
    #     start_pattern=b'PK\x03\x04',
    #     end_pattern=b'PK\x05\x06',
    #     description='ZIP Archive',
    #     min_size=30
    # )
}