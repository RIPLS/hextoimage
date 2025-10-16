#!/usr/bin/env python3
"""
Build script for creating HexToImage GUI executable for Windows.

This script:
1. Reads the version from src/__init__.py
2. Creates a build output directory with the version
3. Generates the standalone executable using PyInstaller
"""

import subprocess
import sys
import os
import re
from pathlib import Path


def get_version():
    """Extract version from src/__init__.py"""
    init_file = Path(__file__).parent / "src" / "__init__.py"
    
    if not init_file.exists():
        print("ERROR: src/__init__.py not found")
        sys.exit(1)
    
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Match __version__ = "X.Y.Z"
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        print("ERROR: Could not find __version__ in src/__init__.py")
        sys.exit(1)
    
    version = match.group(1)
    print(f"[OK] Found version: {version}")
    return version


def build_executable(version):
    """Build the GUI executable using PyInstaller for Windows"""
    
    # Create output directory
    output_dir = Path(__file__).parent / "dist" / f"HexToImage-{version}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    
    # Check if icon file exists
    icon_path = Path(__file__).parent / "assets" / "icon.png"
    if not icon_path.exists():
        print(f"ERROR: Icon file not found at {icon_path}")
        sys.exit(1)
    
    print(f"[OK] Icon file found: {icon_path}")
    
    # Check if spec file exists
    spec_file = Path(__file__).parent / "hextoimage.spec"
    if not spec_file.exists():
        print(f"ERROR: Spec file not found at {spec_file}")
        sys.exit(1)
    
    print(f"[OK] Spec file found: {spec_file}")
    
    # PyInstaller command for Windows
    # Using custom .spec file for better module inclusion
    pyinstaller_cmd = [
        "pyinstaller",
        "--clean",  # Clean previous build
        f"--distpath={output_dir / 'bin'}",
        f"--workpath={output_dir / 'build' / 'work'}",
        str(spec_file)
    ]
    
    print(f"\nRunning PyInstaller...")
    print(f"   Creating standalone executable for Windows\n")
    
    try:
        result = subprocess.run(pyinstaller_cmd, check=True, cwd=Path(__file__).parent)
        print(f"\n[OK] Build successful!")
        exe_path = output_dir / 'bin' / 'HexToImage.exe'
        print(f"Executable location: {exe_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Build failed with error code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\nERROR: PyInstaller not found. Install it with: pip install pyinstaller")
        return False


def cleanup_pyinstaller_artifacts(version):
    """Remove temporary PyInstaller build files"""
    output_dir = Path(__file__).parent / "dist" / f"HexToImage-{version}"
    
    # Keep only the bin directory with the executable
    for item in output_dir.iterdir():
        if item.name not in ['bin']:
            print(f"Removing: {item}")
            if item.is_dir():
                import shutil
                shutil.rmtree(item)
            else:
                item.unlink()


def create_readme(version, output_dir):
    """Create a README for the release"""
    readme_content = f"""# HexToImage {version} - Windows Executable

## About

This folder contains the standalone executable for HexToImage GUI for Windows.

### System Requirements

- Windows 7 or later (32-bit or 64-bit)
- No Python installation required
- No external dependencies required

## Usage

1. Extract the folder to your desired location
2. Run `HexToImage.exe` by double-clicking it, or from command line:
   ```
   HexToImage.exe
   ```

## Features

- Analyze files of any type by examining their hexadecimal content
- Detect and extract embedded images from files
- Modern GUI interface with hex viewer
- Image preview functionality
- Universal file support (any file type, any format)

## Features Included

- **File Analysis**: Scan any file for embedded images
- **Detection**: Identifies JPEG, PNG, GIF, WEBP, and TIFF formats
- **Preview**: View detected images directly in the application
- **Hex Viewer**: Examine hexadecimal content in detail

## Supported File Types for Detection

- JPEG / JPG
- PNG
- GIF
- WEBP
- TIFF

## First Run

When you launch the application for the first time, Windows may show a security warning. This is normal for unsigned executables. Click "Run anyway" to proceed.

## No Installation Required

This is a portable executable - no installer needed. You can:
- Run it directly from this folder
- Copy it to any location
- Run it from a USB drive
- Distribute it to other users

## For More Information

Visit the main project repository for documentation and source code.

---
Version: {version}
Built with Python and PyInstaller
"""
    
    readme_file = output_dir / "README.md"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    print(f"Created: {readme_file}")


def main():
    """Main build process"""
    print("=" * 60)
    print("HexToImage - Build Windows Executable")
    print("=" * 60 + "\n")
    
    # Get version
    version = get_version()
    
    # Build executable
    output_dir = Path(__file__).parent / "dist" / f"HexToImage-{version}"
    success = build_executable(version)
    
    if not success:
        sys.exit(1)
    
    # Cleanup temporary files
    print(f"\nCleaning up temporary files...")
    cleanup_pyinstaller_artifacts(version)
    
    # Create README
    print(f"\nCreating documentation...")
    create_readme(version, output_dir)
    
    print(f"\n" + "=" * 60)
    print(f"[OK] Build Complete!")
    print(f"=" * 60)
    print(f"\nRelease package: {output_dir}")
    print(f"Executable: {output_dir / 'bin' / 'HexToImage.exe'}")
    print(f"\nReady to distribute!\n")


if __name__ == "__main__":
    main()
