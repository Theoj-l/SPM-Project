"""
pytest configuration file to ensure proper module imports.

This file adds the backend directory to the Python path so that
'from app.services...' imports work correctly in test files.
"""
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
