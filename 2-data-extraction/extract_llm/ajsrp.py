# AJSRP pinpointer + cleaning
import re
from typing import List, Pattern, Optional
from utils import _join_pages

# ============================================================
# 1) AJSRP boilerplate patterns (KEEP AS STRINGS + COMPILE)
# ============================================================

AJSRP_BLOCK_PATTERNS: List[str] = [
    # Open access / license block (often appears as a footer chunk)
    r"This article is an open\s*access article distributed.*?(?:\n\s*\n|$)",
    r"under the terms and\s*conditions of the Creative Commons.*?(?:\n\s*\n|$)",
    # Publisher rights block
    r"\d{4}\s*©\s*AISRP.*?all\s*rights\s*reserved\.(?:\n\s*\n|$)",
]

AJSRP_LINE_PATTERNS: List[str] = [
    # Journal header lines
    r"^Arab Journal of Sciences\s*&\s*Research Publishing\s*\(AJSRP\).*$",
    r"^https?://journals\.ajsrp\.com/\S*\s*$",
    r"^ISSN:\s*2518-5780\s*\(Online\).*$",
    r"^ISSN:\s*2518-5780\s*\(Print\).*$",
    r"^ISSN:\s*2518-5780.*$",

    # Pagination line like "Vol 11, Issue 3 (2025) ٠ P: 69 - 4"
    r"^.*Vol\s*\d+,\s*Issue\s*\d+\s*\(\d{4}\)\s*.*P:\s*\d+.*$",

    # Dates / metadata labels (keep content in regions if you want, but usually noise)
    r"^\s*Received:\s*$",
    r"^\s*Revised:\s*$",
    r"^\s*Accepted:\s*$",
    r"^\s*Published:\s*$",
    r"^\s*\*?\s*Corresponding author:\s*$",
    r"^\s*Citation:\s*.*$",

    # Standalone page numbers like 54, 38, 74, etc.
    r"^\s*[0-9\u0660-\u0669\u06F0-\u06F9]+\s*\.?\s*$",

    # Open access markers
    r"^\s*°\s*Open Access\s*$",
    r"^\s*\*\s*NCO\s*ND\s*$",
]

def compile_patterns(patterns: List[str], flags: int) -> List[Pattern]:
    return [re.compile(p, flags) for p in patterns]

AJSRP_BLOCK_RX: List[Pattern] = compile_patterns(AJSRP_BLOCK_PATTERNS, re.IGNORECASE | re.DOTALL)
AJSRP_LINE_RX: List[Pattern]  = compile_patterns(AJSRP_LINE_PATTERNS,  re.IGNORECASE | re.MULTILINE)

def ajsrp_strip_boilerplate(clean_text: str) -> str:
    """Assumes text already normalized by _join_pages / _basic_cleanup pipeline."""
    text = clean_text
    for rx in AJSRP_BLOCK_RX:
        text = rx.sub("", text)
    for rx in AJSRP_LINE_RX:
        text = rx.sub("", text)

    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# ============================================================
# 2) CUES + REGEXES
# ============================================================

EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
URL_RE   = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# High-precision headers (AJSRP shows both English and Arabic versions)
ABSTRACT_HDR_AR = ["المستخلص", "الملخص", "ملخص", "الخلاصة"]
ABSTRACT_HDR_EN = ["abstract"]

KEYWORDS_HDR_AR = ["الكلمات المفتاحية", "كلمات مفتاحية", "الكلمات الدالة", "كلمات دالة"]
KEYWORDS_HDR_EN = ["keywords", "key words", "index terms"]

# Often present after keywords: INTRODUCTION / المقدمة
INTRO_HDR_AR = ["المقدمة", "مقدمة"]
INTRO_HDR_EN = ["introduction"]

# Author markers that appear in AJSRP
# (not always present, but harmless)
AUTHOR_MARKERS_AR = ["أ.", "د.", "دكتور", "المؤلف", "المؤلفون"]
AUTHOR_MARKERS_EN = ["ms.", "mr.", "dr.", "prof.", "author", "authors", "eng."]

# Fallback author cues (affiliations)
AR_AUTHOR_CUES = ["جامعة", "كلية", "قسم", "وزارة", "المملكة", "السودان", "اليمن"]
EN_AUTHOR_CUES = ["university", "faculty", "department", "ministry", "ksa", "yemen", "sudan"]

# Regex safety
ABSTRACT_RX = re.compile(r"^\s*abstract\s*[:：]?\s*$", re.IGNORECASE)
KEYWORDS_RX = re.compile(r"^\s*keywords?\s*[:：]?\s*$", re.IGNORECASE)


def _prep_cues(*lists: List[str]) -> List[str]:
    """Lowercase + remove duplicates while preserving order."""
    seen = set()
    out: List[str] = []
    for L in lists:
        for x in L:
            k = x.lower()
            if k not in seen:
                seen.add(k)
                out.append(k)
    return out


def _slice_lines(lines: List[str], start: int, end: int) -> str:
    start = max(0, start)
    end = min(len(lines), end)
    if start >= end:
        return ""
    return "\n".join(lines[start:end]).strip()


def _region_from_indices(lines: List[str], idxs: List[int], radius: int = 2) -> str:
    if not idxs:
        return ""
    keep = set()
    for i in idxs:
        for j in range(max(0, i - radius), min(len(lines), i + radius + 1)):
            keep.add(j)
    return "\n".join(lines[i] for i in sorted(keep)).strip()


# ============================================================
# 3) AJSRP PINPOINTER (DETERMINISTIC)
# ============================================================

def AJSRP_pinpoint_imp(page1: str, page2: str, max_chars: int = 9000) -> str:
    """
    Deterministic AJSRP pinpointer:
      - join+clean (via _join_pages)
      - strip AJSRP boilerplate
      - single pass over lines to detect anchors:
          abstract / keywords / intro / emails
      - slice into labeled regions for the LLM
    """
    text = _join_pages(page1, page2)
    text = ajsrp_strip_boilerplate(text)

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    abs_cues    = _prep_cues(ABSTRACT_HDR_AR, ABSTRACT_HDR_EN)
    key_cues    = _prep_cues(KEYWORDS_HDR_AR, KEYWORDS_HDR_EN)
    intro_cues  = _prep_cues(INTRO_HDR_AR, INTRO_HDR_EN)
    author_mark = _prep_cues(AUTHOR_MARKERS_AR, AUTHOR_MARKERS_EN)
    author_cues = _prep_cues(AR_AUTHOR_CUES, EN_AUTHOR_CUES)

    abs_idx: Optional[int] = None
    key_idx: Optional[int] = None
    intro_idx: Optional[int] = None

    email_idxs: List[int] = []
    authorhint_idxs: List[int] = []  # helps slice authors even if no marker

    # ---- Single pass ----
    for i, ln in enumerate(lines):
        lo = ln.lower()

        # Abstract header: startswith cue OR matches "ABSTRACT:" style line
        if abs_idx is None:
            if any(lo.startswith(c) for c in abs_cues) or ABSTRACT_RX.match(ln):
                abs_idx = i

        # Keywords header
        if key_idx is None:
            if any(lo.startswith(c) for c in key_cues) or KEYWORDS_RX.match(ln):
                key_idx = i

        # Intro header (stop marker)
        if intro_idx is None and any(lo.startswith(c) for c in intro_cues):
            intro_idx = i

        # Emails
        if EMAIL_RE.search(ln):
            email_idxs.append(i)

        # Author hint lines near the top (names + affiliations)
        # AJSRP tends to have: Names -> Affiliation line (University | Country)
        if i <= 60:
            if any(m in lo for m in author_mark) or any(c in lo for c in author_cues):
                authorhint_idxs.append(i)

    # ABSTRACT_REGION: end priority = keywords > intro > cap
    abstract_region = ""
    if abs_idx is not None:
        if key_idx is not None and key_idx > abs_idx:
            end = key_idx
        elif intro_idx is not None and intro_idx > abs_idx:
            end = intro_idx
        else:
            end = min(len(lines), abs_idx + 80)  # AJSRP abstracts can be long
        abstract_region = _slice_lines(lines, abs_idx, end)

    # KEYWORDS_REGION: keywords line + next line(s)
    keywords_region = ""
    if key_idx is not None:
        keywords_region = _slice_lines(lines, key_idx, min(len(lines), key_idx + 3))

    # AUTHORS_REGION:
    # Priority: emails region > author hints in top zone
    if email_idxs:
        authors_region = _region_from_indices(lines, email_idxs, radius=3)
    else:
        # Take a tight top-zone window around first author hint
        if authorhint_idxs:
            start = max(0, authorhint_idxs[0] - 2)
            authors_region = _slice_lines(lines, start, min(len(lines), start + 18))
        else:
            authors_region = ""

    # TITLE_REGION:
    # Stop at earliest of: first author hint, email, abstract
    cut_candidates: List[int] = []
    if authorhint_idxs:
        cut_candidates.append(authorhint_idxs[0])
    if email_idxs:
        cut_candidates.append(email_idxs[0])
    if abs_idx is not None:
        cut_candidates.append(abs_idx)

    cutoff = min(cut_candidates) if cut_candidates else min(len(lines), 30)

    title_region_lines = lines[:cutoff]
    title_region_lines = [ln for ln in title_region_lines if not URL_RE.search(ln)]
    title_region = "\n".join(title_region_lines[:40]).strip()

    llm_text = (
        "TITLE_REGION:\n" + title_region +
        "\n\nAUTHORS_REGION:\n" + authors_region +
        "\n\nABSTRACT_REGION:\n" + abstract_region +
        "\n\nKEYWORDS_REGION:\n" + keywords_region
    ).strip()

    return llm_text[:max_chars]
