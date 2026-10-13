import unicodedata
from typing import Dict, Any, List

def inspect_text(text: str) -> dict:
    """
    Inspects and normalizes text for adversarial evasion techniques (arXiv:2504.09559).
    - Preserves original input for forensic auditing.
    - Normalizes compatibility characters via NFKC.
    - Identifies suspicious invisible/control/format characters (Cf, Cc, Cs).
    - Returns audit details and flags whether review is warranted.
    """
    # Keep the original for comparison and auditing.
    original = text

    # Normalize equivalent Unicode representations.
    normalized = unicodedata.normalize("NFKC", text)

    # Detect invisible formatting/control characters.
    suspicious_chars = []
    for char in original:
        category = unicodedata.category(char)
        # Cf = Other, format (e.g., zero-width spaces U+200B, bidi controls U+202E)
        # Cc = Other, control (excluding standard whitespaces: \t, \n, \r)
        # Cs = Other, surrogate
        if category in {"Cf", "Cs"} or (category == "Cc" and char not in {"\t", "\n", "\r"}):
            suspicious_chars.append({
                "codepoint": f"U+{ord(char):04X}",
                "category": category,
            })

    return {
        "original": original,
        "normalized": normalized,
        "suspicious_characters": suspicious_chars,
        "needs_review": bool(suspicious_chars),
    }

def detect_mixed_scripts(text: str) -> bool:
    """
    Checks for mixed-script homoglyph attacks (e.g. Cyrillic letters mixed with Latin).
    """
    scripts = set()
    for char in text:
        if char.isalpha():
            name = unicodedata.name(char, "")
            if "CYRILLIC" in name:
                scripts.add("CYRILLIC")
            elif "LATIN" in name:
                scripts.add("LATIN")
            elif "GREEK" in name:
                scripts.add("GREEK")
    return len(scripts) > 1
