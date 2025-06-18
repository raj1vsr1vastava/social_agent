#!/usr/bin/env python3
"""
Social Agent - Main entry point for the WhatsApp conversation analysis system.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli.basic import cli

if __name__ == "__main__":
    cli()
