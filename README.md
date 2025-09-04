# HexToImage

A Python tool to read files and display their content as hexadecimal data, with plans for future image visualization capabilities.

## Features

- Read any file format and convert to hexadecimal representation
- Clean, organized output with offset, hex values, and ASCII representation
- Modular architecture supporting both CLI and future GUI interfaces
- Built with Python 3.7+ using only standard library

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
```bash
python3 src/cli/main.py <file_path>
```

## Development Status

- ✅ Basic hex reading functionality
- 🔄 Currently refactoring to modular architecture
- ⏳ CLI interface (in progress)
- ⏳ GUI interface (planned)
- ⏳ Image visualization features (planned)

## Requirements

- Python 3.7 or higher
- No external dependencies (uses standard library only)

## Installation

Clone the repository:
```bash
git clone <your-repo-url>
cd hextoimage
```

## Contributing

This is a personal learning project, but suggestions and improvements are welcome!

## License

MIT License (or your preferred license)
