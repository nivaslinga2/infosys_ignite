import pytest
from app.guardrails.normalize import inspect_text, detect_mixed_scripts

def test_normalizes_compatibility_characters():
    result = inspect_text("ＡＢＣ")
    assert result["normalized"] == "ABC"

def test_detects_zero_width_formatting():
    result = inspect_text("hello\u200bworld")
    assert result["needs_review"] is True
    assert any(c["codepoint"] == "U+200B" for c in result["suspicious_characters"])

def test_preserves_original_text():
    text = "hello\u200bworld"
    result = inspect_text(text)
    assert result["original"] == text

def test_ordinary_text():
    result = inspect_text("Create a support ticket")
    assert result["needs_review"] is False
    assert len(result["suspicious_characters"]) == 0

def test_detects_bidirectional_override():
    # U+202E is RIGHT-TO-LEFT OVERRIDE used in bidi evasion
    result = inspect_text("test\u202ereverse")
    assert result["needs_review"] is True
    assert any(c["codepoint"] == "U+202E" for c in result["suspicious_characters"])

def test_detects_mixed_script_homoglyphs():
    # Cyrillic 'а' (U+0430) mixed with Latin 'dmin'
    mixed = "\u0430dmin"
    assert detect_mixed_scripts(mixed) is True
    assert detect_mixed_scripts("admin") is False
