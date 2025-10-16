#!/usr/bin/env python3
"""
GUI Launcher for HexToImage application.

This script provides an easy way to launch the GUI interface.
"""

import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import main

if __name__ == "__main__":
    main()
