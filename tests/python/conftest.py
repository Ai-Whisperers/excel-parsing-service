"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
from pathlib import Path

# Add python-layer to path
python_layer = Path(__file__).parent.parent.parent / "python-layer"
sys.path.insert(0, str(python_layer))
