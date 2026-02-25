import sys
import os
from pathlib import Path

def get_resource_path(*relative_parts):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    Usage: get_resource_path('resources', 'icons', 'dashboard.png')
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    else:
        # Development mode
        # Path(__file__) is src/core/resource_utils.py
        # parent is src/core
        # parent.parent is src
        # parent.parent.parent is the project root
        base_path = Path(__file__).parent.parent.parent

    # Combine parts and return string
    path = base_path.joinpath(*relative_parts)
    return str(path)
