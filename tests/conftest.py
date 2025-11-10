"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys

# Add implementation directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '03-Implementation'))
