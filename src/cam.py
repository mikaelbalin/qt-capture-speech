#!/usr/bin/env python3
"""
Legacy entry point - redirects to main.py
"""

import sys
import os

# Add current directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    sys.exit(main())
