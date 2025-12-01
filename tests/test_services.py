import os
import pytest
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.services import parser

def test_parse_txt(tmp_path):
    # Create a dummy txt file
    d = tmp_path / "test_resume.txt"
    d.write_text("This is a test resume.", encoding="utf-8")
    
    text = parser.parse_resume(str(d))
    assert "This is a test resume." in text

def test_parse_unsupported(tmp_path):
    d = tmp_path / "test.xyz"
    d.write_text("content", encoding="utf-8")
    
    with pytest.raises(ValueError):
        parser.parse_resume(str(d))
