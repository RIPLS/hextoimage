# HexToImage

A Python tool designed to analyze files of any type by examining their hexadecimal content to detect and extract embedded images. Its main purpose is to help recover images from backup or data dump files. When images are found, they are listed, and the user can preview them directly within the tool.

## 🚀 Download the latest version

[![GitHub release](https://img.shields.io/github/v/release/RIPLS/hextoimage?sort=semver&color=blue)](https://github.com/RIPLS/hextoimage/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/RIPLS/hextoimage/total?color=brightgreen)](https://github.com/RIPLS/hextoimage/releases)

👉 **[Download for Windows (.exe)](https://github.com/USER/REPO/releases/download/v1.0.0/file-v1.0.0-windows-x64.exe)**

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
├── build.py                # Script to build executables
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

### Running the Executable

- **Windows**: Double-click `HexToImage.exe` or run from command line

### Distribution

The entire `HexToImage-{VERSION}` folder can be distributed to users. They don't need Python or any dependencies installed - it's fully portable!

## Building Executables

You can create a standalone Windows executable that doesn't require Python to be installed on the target machine.

### Quick Start Commands

**Windows (Command Prompt or PowerShell):**
```bash
build.bat
```

**Manual (any platform):**
```bash
python3 build.py
```

### Prerequisites

1. Install build dependencies:
```bash
pip install -r requirements.txt
# or specifically: pip install PyInstaller
```

2. Ensure you have `assets/icon.png` (used for the application icon)

## Development Status

- ✅ Basic hex reading functionality
- ✅ File signature detection for common formats
- ✅ UI with file detection and extraction 
- ✅ CLI interface with analysis and extraction features
- ⏳ Additional file format support (planned)
- ⏳ Advanced image visualization features (planned)

## Requirements

- Python 3.7 or higher (for development)
- Standard library (tkinter for GUI)
- **Pillow (REQUIRED for image preview)** - `pip install Pillow`
- **PyInstaller (for building executables)** - `pip install PyInstaller`

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
python3 gui_launcher.py
```

## Contributing

This is a personal learning project, but suggestions and improvements are welcome!

## License

MIT License
