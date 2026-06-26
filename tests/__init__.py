"""Test suite for AI Recruiter."""

import sys
from pathlib import Path

# Add parent directory and package root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "ai_recruiter"))
sys.path.insert(0, str(root_dir))
