"""
File extraction and export module.
This module provides functionality to extract detected files and save them to disk.
"""

import os
import shutil
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from .hex_reader import HexData
from .analyzers import AnalysisResult, DetectedFile, reconstruct_binary_data


@dataclass
class ExtractionResult:
    """Result of file extraction operation."""
    source_file: str
    output_directory: str
    extracted_files: List[Dict[str, any]]
    total_extracted: int
    failed_extractions: List[Dict[str, str]]
    success_rate: float


def create_output_directory(output_dir: str = "result", clean_existing: bool = False) -> str:
    """
    Create output directory for extracted files.
    
    Args:
        output_dir (str): Directory name to create
        clean_existing (bool): Whether to clean existing directory
    
    Returns:
        str: Absolute path to created directory
    
    Raises:
        OSError: If directory cannot be created
    """
    abs_output_dir = os.path.abspath(output_dir)
    
    if os.path.exists(abs_output_dir):
        if clean_existing:
            shutil.rmtree(abs_output_dir)
            os.makedirs(abs_output_dir)
        # If directory exists and we're not cleaning, just use it
    else:
        os.makedirs(abs_output_dir)
    
    return abs_output_dir


def generate_filename(detected_file: DetectedFile, file_number: int, use_original_extension: bool = True) -> str:
    """
    Generate filename for extracted file.
    
    Args:
        detected_file (DetectedFile): Detected file information
        file_number (int): Sequential file number
        use_original_extension (bool): Whether to use the detected file extension
    
    Returns:
        str: Generated filename
    """
    if use_original_extension:
        extension = detected_file.signature.extension
    else:
        extension = "bin"
    
    # Format: file-001.jpg, file-002.png, etc.
    return f"file-{file_number:03d}.{extension}"


def extract_file_data(hex_data: HexData, detected_file: DetectedFile) -> Optional[bytes]:
    """
    Extract binary data for a specific detected file.
    
    Args:
        hex_data (HexData): Source hex data
        detected_file (DetectedFile): File to extract
    
    Returns:
        Optional[bytes]: Extracted file data, or None if extraction failed
    """
    try:
        # Reconstruct complete binary data
        binary_data = reconstruct_binary_data(hex_data)
        
        start_pos = detected_file.start_offset
        end_pos = detected_file.end_offset
        
        if end_pos is None:
            # If no end position, extract from start to end of data
            extracted_data = binary_data[start_pos:]
        else:
            # Extract specific range
            extracted_data = binary_data[start_pos:end_pos]
        
        # Validate minimum size
        if len(extracted_data) < detected_file.signature.min_size:
            return None
        
        return extracted_data
        
    except Exception:
        return None


def save_extracted_file(file_data: bytes, output_path: str) -> bool:
    """
    Save extracted file data to disk.
    
    Args:
        file_data (bytes): Binary data to save
        output_path (str): Full path where to save the file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_path, 'wb') as f:
            f.write(file_data)
        return True
    except Exception:
        return False


def extract_detected_files(
    hex_data: HexData, 
    analysis_result: AnalysisResult,
    output_dir: str = "result",
    clean_existing: bool = False,
    file_types: Optional[List[str]] = None,
    min_confidence: float = 0.5
) -> ExtractionResult:
    """
    Extract all detected files to specified directory.
    
    Args:
        hex_data (HexData): Source hex data
        analysis_result (AnalysisResult): Analysis results containing detected files
        output_dir (str): Output directory name
        clean_existing (bool): Whether to clean existing output directory
        file_types (Optional[List[str]]): Specific file types to extract (None = all)
        min_confidence (float): Minimum confidence score to extract (0.0 to 1.0)
    
    Returns:
        ExtractionResult: Results of extraction operation
    """
    # Create output directory
    abs_output_dir = create_output_directory(output_dir, clean_existing)
    
    extracted_files = []
    failed_extractions = []
    file_counter = 1
    
    for detected_file in analysis_result.detected_files:
        # Filter by file type if specified
        if file_types and detected_file.file_type not in file_types:
            continue
        
        # Filter by confidence score
        if detected_file.confidence < min_confidence:
            failed_extractions.append({
                'file_number': file_counter,
                'file_type': detected_file.file_type,
                'reason': f'Low confidence score: {detected_file.confidence:.2f} < {min_confidence:.2f}'
            })
            file_counter += 1
            continue
        
        try:
            # Extract file data
            file_data = extract_file_data(hex_data, detected_file)
            
            if file_data is None:
                failed_extractions.append({
                    'file_number': file_counter,
                    'file_type': detected_file.file_type,
                    'reason': 'Failed to extract data or file too small'
                })
                continue
            
            # Generate filename
            filename = generate_filename(detected_file, file_counter)
            output_path = os.path.join(abs_output_dir, filename)
            
            # Save file
            if save_extracted_file(file_data, output_path):
                extracted_files.append({
                    'file_number': file_counter,
                    'filename': filename,
                    'file_type': detected_file.file_type,
                    'extension': detected_file.signature.extension,
                    'size': len(file_data),
                    'original_position': f"{detected_file.start_offset}-{detected_file.end_offset}",
                    'confidence': detected_file.confidence,
                    'output_path': output_path
                })
            else:
                failed_extractions.append({
                    'file_number': file_counter,
                    'file_type': detected_file.file_type,
                    'reason': 'Failed to save file to disk'
                })
            
        except Exception as e:
            failed_extractions.append({
                'file_number': file_counter,
                'file_type': detected_file.file_type,
                'reason': f'Unexpected error: {str(e)}'
            })
        
        file_counter += 1
    
    # Calculate success rate
    total_attempted = len(extracted_files) + len(failed_extractions)
    success_rate = len(extracted_files) / total_attempted if total_attempted > 0 else 0.0
    
    return ExtractionResult(
        source_file=analysis_result.source_file,
        output_directory=abs_output_dir,
        extracted_files=extracted_files,
        total_extracted=len(extracted_files),
        failed_extractions=failed_extractions,
        success_rate=success_rate
    )


def create_extraction_report(extraction_result: ExtractionResult) -> str:
    """
    Create a detailed report of the extraction operation.
    
    Args:
        extraction_result (ExtractionResult): Results to report on
    
    Returns:
        str: Formatted extraction report
    """
    lines = [
        "=" * 60,
        "FILE EXTRACTION REPORT",
        "=" * 60,
        f"Source file: {extraction_result.source_file}",
        f"Output directory: {extraction_result.output_directory}",
        f"Files extracted: {extraction_result.total_extracted}",
        f"Failed extractions: {len(extraction_result.failed_extractions)}",
        f"Success rate: {extraction_result.success_rate:.1%}",
        ""
    ]
    
    if extraction_result.extracted_files:
        lines.append("SUCCESSFULLY EXTRACTED FILES:")
        lines.append("-" * 40)
        
        for extracted in extraction_result.extracted_files:
            lines.extend([
                f"File {extracted['file_number']:03d}: {extracted['filename']}",
                f"  Type: {extracted['file_type']} (.{extracted['extension']})",
                f"  Size: {extracted['size']:,} bytes",
                f"  Original position: {extracted['original_position']}",
                f"  Confidence: {extracted['confidence']:.2f}",
                f"  Saved to: {extracted['output_path']}",
                ""
            ])
    
    if extraction_result.failed_extractions:
        lines.append("FAILED EXTRACTIONS:")
        lines.append("-" * 20)
        
        for failed in extraction_result.failed_extractions:
            lines.extend([
                f"File {failed['file_number']:03d}: {failed['file_type']}",
                f"  Reason: {failed['reason']}",
                ""
            ])
    
    lines.append("=" * 60)
    return '\n'.join(lines)