#!/usr/bin/env python3
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.hex_reader import read_file_as_hex_data, get_hex_summary
from src.core.formatters import format_hex_data, format_hex_summary
from src.core.analyzers import analyze_file_content, get_supported_file_types
from src.core.exporters import extract_detected_files, create_extraction_report


def print_usage():
    """Print usage instructions."""
    print("Usage: python3 src/cli/main.py <file_path> [options]")
    print("Example: python3 src/cli/main.py example.txt")
    print("Options:")
    print("  --analyze, -a    Show file analysis (detect embedded files)")
    print("  --summary, -s    Show hex data summary")
    print("  --extract, -e    Extract detected files to 'result' folder")
    print("  --help, -h       Show this help message")


def print_error(message: str):
    """Print error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def format_analysis_results(analysis):
    """Format analysis results for display."""
    lines = [
        "=" * 60,
        "FILE ANALYSIS RESULTS",
        "=" * 60,
        f"Source file: {analysis.source_file}",
        f"Total file size: {analysis.total_size:,} bytes",
        f"Files detected: {len(analysis.detected_files)}",
        ""
    ]
    
    if analysis.analysis_summary:
        lines.append("SUMMARY BY FILE TYPE:")
        lines.append("-" * 30)
        for file_type, count in analysis.analysis_summary.items():
            lines.append(f"  {file_type}: {count} file(s)")
        lines.append("")
    
    if analysis.detected_files:
        lines.append("DETAILED DETECTION RESULTS:")
        lines.append("-" * 40)
        
        for i, detected in enumerate(analysis.detected_files, 1):
            size_info = f"{detected.size:,} bytes" if detected.size else "unknown size"
            confidence_info = f"{detected.confidence:.2f}"
            
            lines.extend([
                f"File {i}: {detected.file_type} (.{detected.signature.extension})",
                f"  Position: {detected.start_offset:,} - {detected.end_offset:,}" if detected.end_offset else f"  Position: {detected.start_offset:,} - end",
                f"  Size: {size_info}",
                f"  Confidence: {confidence_info}",
                f"  Description: {detected.signature.description}",
                ""
            ])
    else:
        lines.extend([
            "No embedded files detected.",
            f"Supported file types: {', '.join(get_supported_file_types())}",
            ""
        ])
    
    lines.append("=" * 60)
    return '\n'.join(lines)


def parse_arguments():
    """Parse command line arguments."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    # Check for help
    if sys.argv[1] in ['--help', '-h']:
        print_usage()
        sys.exit(0)
    
    file_path = sys.argv[1]
    show_analysis = False
    show_summary = False
    extract_files = False
    
    # Parse options
    for arg in sys.argv[2:]:
        if arg in ['--analyze', '-a']:
            show_analysis = True
        elif arg in ['--summary', '-s']:
            show_summary = True
        elif arg in ['--extract', '-e']:
            extract_files = True
        elif arg in ['--help', '-h']:
            print_usage()
            sys.exit(0)
        else:
            print_error(f"Unknown option: {arg}")
            print_usage()
            sys.exit(1)
    
    return file_path, show_analysis, show_summary, extract_files


def main():
    """Main CLI function."""
    # Parse command line arguments
    file_path, show_analysis, show_summary, extract_files = parse_arguments()
    
    try:
        # Read file as hex data
        hex_data = read_file_as_hex_data(file_path)
        
        if hex_data is None:
            print_error("Failed to read file")
            sys.exit(1)
        
        # Always show basic hex output (unless only analysis is requested)
        if not show_analysis or show_summary:
            formatted_output = format_hex_data(hex_data)
            print(formatted_output)
        
        # Show summary if requested
        if show_summary:
            summary = get_hex_summary(hex_data)
            print("\n" + format_hex_summary(summary))
        
        # Show analysis if requested
        if show_analysis:
            print("\nAnalyzing file for embedded files...")
            analysis = analyze_file_content(hex_data)
            print(format_analysis_results(analysis))
        
        # Extract files if requested
        if extract_files:
            print("\nAnalyzing file for extraction...")
            analysis = analyze_file_content(hex_data)
            
            if analysis.detected_files:
                print(f"Found {len(analysis.detected_files)} files to extract...")
                extraction_result = extract_detected_files(hex_data, analysis, output_dir="result", clean_existing=True)
                print(create_extraction_report(extraction_result))
            else:
                print("No files detected for extraction.")
                print(f"Supported file types: {', '.join(get_supported_file_types())}")
        
        # If no options specified, show basic hex output (already done above)
        
    except FileNotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except IsADirectoryError as e:
        print_error(str(e))
        sys.exit(1)
    except PermissionError as e:
        print_error(str(e))
        sys.exit(1)
    except IOError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()