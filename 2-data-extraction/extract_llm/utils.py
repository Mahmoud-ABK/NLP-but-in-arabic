import re
import unicodedata
from dataclasses import dataclass
from typing import List, Dict, Tuple, Callable


# =========================
# Core utilities (shared)
# =========================

def _normalize_unicode_and_strip_invisibles(text: str) -> str:
    """NFKC normalize + remove invisible formatting chars (category Cf)."""
    text = unicodedata.normalize("NFKC", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    return text

def _basic_cleanup(text: str) -> str:
    """Light OCR cleanup that is safe for Arabic + English."""
    if not isinstance(text, str):
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _normalize_unicode_and_strip_invisibles(text)

    # Remove decorative punctuation/symbols
    text = re.sub(r"[•●▪♦■★☆※…—–―‐-⁃⁄⁎⁑⁂⁕⁖⁗⁘⁙⁚⁛⁜⁝⁞]", " ", text)

    # Normalize repeated punctuation
    text = re.sub(r"\.{3,}", ".", text)
    text = re.sub(r"[=]{2,}", " ", text)
    text = re.sub(r"[_~^`]+", " ", text)

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def _join_pages(page1: str, page2: str) -> str:
    p1 = _basic_cleanup(page1 or "")
    p2 = _basic_cleanup(page2 or "")
    if p1 and p2:
        return p1 + "\n\n===== PAGE 2 =====\n\n" + p2
    return p1 or p2


