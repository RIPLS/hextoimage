# HexToImage

A Python tool designed to analyze files of any type by examining their hexadecimal content to detect and extract embedded images. Its main purpose is to help recover images from backup or data dump files. When images are found, they are listed, and the user can preview them directly within the tool.

## Features

- **Universal File Support**: 
  - Analyze ANY file type without restrictions
  - Binary data files and unknown formats

- **Analysis**:
  - Detect embedded files by their signatures (JPEG, PNG, GIF, WEBP, TIFF)
  - File entropy and pattern analysis
  - Enhanced hex viewer with structure analysis

- **Command Line Interface**: For batch processing and automation
- **Modular Architecture**: Clean separation of core/cli/gui components
- **Built with Python 3.7+**: Standard library + optional Pillow for image previews

## Project Structure

```
hextoimage/
├── README.md
├── requirements.txt
├── src/
│   ├── core/           # Core hex reading logic
│   ├── cli/            # Command line interface
│   └── gui/            # Future graphical interface
├── tests/              # Test files
└── hex_reader.py       # Legacy script (to be refactored)
```

## Usage

### Graphical Interface (Recommended)
```bash
# Launch the GUI
python3 gui_launcher.py

# Or directly
python3 src/gui/main_window.py
```

### Command Line Interface
```bash
# Basic hex output
python3 src/cli/main.py <file_path>

# Analyze for embedded files
python3 src/cli/main.py <file_path> --analyze

# Extract detected files
python3 src/cli/main.py <file_path> --extract

# Show hex summary
python3 src/cli/main.py <file_path> --summary
```

## Development Status

- ✅ Basic hex reading functionality
- ✅ Modular architecture with core/cli/gui separation
- ✅ CLI interface with analysis and extraction features
- ✅ Modern GUI interface with file preview
- ✅ File signature detection for common formats
- ⏳ Additional file format support (planned)
- ⏳ Advanced image visualization features (planned)

## Requirements

- Python 3.7 or higher
- Standard library (tkinter for GUI)
- **Pillow (REQUIRED for image preview)** - `pip install Pillow`

## Installation

Clone the repository:
```bash
git clone <your-repo-url>
cd hextoimage
```

Install required dependencies:
```bash
pip install -r requirements.txt
```

Test the installation:
```bash
python3 test_gui.py
```

## Contributing

This is a personal learning project, but suggestions and improvements are welcome!

## License

MIT License
