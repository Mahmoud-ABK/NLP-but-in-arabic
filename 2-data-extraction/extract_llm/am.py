# AM (Manarah) pinpointer + cleaning (full code cell)
import re
from typing import List, Pattern, Optional
from utils import _join_pages

# ============================================================
# 1) AM boilerplate patterns (KEEP AS STRINGS + COMPILE)
#    Notes from your examples:
#    - "Manarah, ... Series, Vol..., No..., 2025 (255)" (English)
#    - Arabic running header lines with authors + title
#    - Received/Revised/Accepted/Published blocks
#    - Open access/license sometimes (optional)
# ============================================================

AM_BLOCK_PATTERNS: List[str] = [
    # If your AM source sometimes contains license blocks (safe to remove when present)
    r"This article is an open\s*access article distributed.*?(?:\n\s*\n|$)",
    r"under the terms and\s*conditions of the Creative Commons.*?(?:\n\s*\n|$)",
]

AM_LINE_PATTERNS: List[str] = [
    # English footer/header line
    r"^Manarah,\s*.*?Series,\s*Vol\.\s*\d+,\s*No\.\s*\d+,\s*\d{4}\s*\(\s*[0-9\u0660-\u0669\u06F0-\u06F9]+\s*\)\s*$",

    # DOI line variants
    r"^\s*DOI\s*:?\s*https?://\S+\s*$",
    r"^\s*DOL\s*:?\s*https?://\S+\s*$",  # OCR confusion

    # Dates labels (sometimes appear alone)
    r"^\s*Received\s*:\s*$",
    r"^\s*Revised\s*:\s*$",
    r"^\s*Accepted\s*:\s*$",
    r"^\s*Published\s*:\s*$",
    r"^\s*\*+\s*Corresponding\s*Author\s*:?\s*$",

    # Standalone page numbers
    r"^\s*[0-9\u0660-\u0669\u06F0-\u06F9]+\s*\.?\s*$",
]

def compile_patterns(patterns: List[str], flags: int) -> List[Pattern]:
    return [re.compile(p, flags) for p in patterns]

AM_BLOCK_RX: List[Pattern] = compile_patterns(AM_BLOCK_PATTERNS, re.IGNORECASE | re.DOTALL)
AM_LINE_RX: List[Pattern]  = compile_patterns(AM_LINE_PATTERNS,  re.IGNORECASE | re.MULTILINE)

# Additional helpful regexes for AM
EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
URL_RE   = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
DOI_RE   = re.compile(r"\bdoi\s*:?\s*(https?://\S+)", re.IGNORECASE)

# AM sometimes has "Received: ... Abstract" on SAME LINE
RECEIVED_INLINE_ABS_RE = re.compile(r"^\s*Received\s*:\s*\d{2}/\d{2}/\d{4}\s*Abstract\b", re.IGNORECASE)

# Strong metadata anchors
ABSTRACT_HDR_AR = ["ملخص", "المستخلص", "الملخص", "الخلاصة"]
ABSTRACT_HDR_EN = ["abstract"]
KEYWORDS_HDR_AR = ["الكلمات المفتاحية", "الكلمات الدالة", "كلمات مفتاحية", "كلمات دالة"]
KEYWORDS_HDR_EN = ["keywords", "key words", "index terms"]
INTRO_HDR_AR = ["المقدمة", "مقدمة"]
INTRO_HDR_EN = ["introduction"]

# Author cues (your idea + AM specifics)
AR_AUTHOR_CUES = ["جامعة", "كلية", "قسم", "أستاذ", "د.", "دكتور", "باحث", "باحثة"]
EN_AUTHOR_CUES = ["university", "college", "school", "department", "researcher", "prof", "dr.", "eng."]


def am_strip_boilerplate(clean_text: str) -> str:
    """Assumes text already normalized by _join_pages / _basic_cleanup pipeline."""
    text = clean_text

    for rx in AM_BLOCK_RX:
        text = rx.sub("", text)

    for rx in AM_LINE_RX:
        text = rx.sub("", text)

    # Remove URL-only lines
    text = re.sub(r"^\s*(https?://\S+|www\.\S+)\s*$", "", text, flags=re.IGNORECASE | re.MULTILINE)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


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


def AM_pinpoint_imp(page1: str, page2: str, max_chars: int = 9000) -> str:
    """
    Deterministic AM (Manarah) pinpointer:
      - join+clean (via _join_pages)
      - strip Manarah boilerplate
      - single pass over lines to detect:
          abstract / keywords / intro / emails / DOI / author cues
      - slice into labeled regions for your LLM
    """
    text = _join_pages(page1, page2)
    text = am_strip_boilerplate(text)

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    abs_cues   = _prep_cues(ABSTRACT_HDR_AR, ABSTRACT_HDR_EN)
    key_cues   = _prep_cues(KEYWORDS_HDR_AR, KEYWORDS_HDR_EN)
    intro_cues = _prep_cues(INTRO_HDR_AR, INTRO_HDR_EN)
    auth_cues  = _prep_cues(AR_AUTHOR_CUES, EN_AUTHOR_CUES)

    abs_idx: Optional[int] = None
    key_idx: Optional[int] = None
    intro_idx: Optional[int] = None
    doi_idx: Optional[int] = None

    email_idxs: List[int] = []
    authorhint_idxs: List[int] = []
    received_inline_abs_idx: Optional[int] = None

    # ---- Single pass ----
    for i, ln in enumerate(lines):
        lo = ln.lower()

        # A) special case: "Received: dd/mm/yyyy Abstract" same line
        if received_inline_abs_idx is None and RECEIVED_INLINE_ABS_RE.search(ln):
            received_inline_abs_idx = i
            # treat as abstract header as well
            if abs_idx is None:
                abs_idx = i

        # B) abstract header (Arabic "ملخص" or English "Abstract")
        if abs_idx is None and any(lo.startswith(c) for c in abs_cues):
            abs_idx = i

        # C) keywords header
        if key_idx is None and any(lo.startswith(c) for c in key_cues):
            key_idx = i

        # D) intro header (stop marker)
        if intro_idx is None and any(lo.startswith(c) for c in intro_cues):
            intro_idx = i

        # E) DOI / link
        if doi_idx is None and ("doi" in lo or "10." in lo):
            if DOI_RE.search(ln) or "doi.org" in lo:
                doi_idx = i

        # F) emails
        if EMAIL_RE.search(ln):
            email_idxs.append(i)

        # G) author cues (only care near top)
        if i <= 70 and any(c in lo for c in auth_cues):
            authorhint_idxs.append(i)

    # ABSTRACT_REGION:
    abstract_region = ""
    if abs_idx is not None:
        # end priority: keywords > intro > cap
        if key_idx is not None and key_idx > abs_idx:
            end = key_idx
        elif intro_idx is not None and intro_idx > abs_idx:
            end = intro_idx
        else:
            end = min(len(lines), abs_idx + 80)
        abstract_region = _slice_lines(lines, abs_idx, end)

        # If the header is "Received: ... Abstract", remove the leading "Received..." part
        if received_inline_abs_idx == abs_idx:
            # keep line but remove "Received: dd/mm/yyyy" prefix
            abstract_region = re.sub(r"^\s*Received\s*:\s*\d{2}/\d{2}/\d{4}\s*", "", abstract_region, flags=re.IGNORECASE)

    # KEYWORDS_REGION:
    keywords_region = ""
    if key_idx is not None:
        keywords_region = _slice_lines(lines, key_idx, min(len(lines), key_idx + 3))

    # AUTHORS_REGION:
    # Priority: emails region, else use top-zone author hints
    if email_idxs:
        authors_region = _region_from_indices(lines, email_idxs, radius=3)
    elif authorhint_idxs:
        # pick a compact window around the earliest author hint
        start = max(0, authorhint_idxs[0] - 3)
        authors_region = _slice_lines(lines, start, min(len(lines), start + 20))
        # remove URL-only lines if any slipped
        authors_region = "\n".join([ln for ln in authors_region.split("\n") if not URL_RE.search(ln)]).strip()
    else:
        authors_region = ""

    # TITLE_REGION:
    # Stop at earliest of author/email/abstract; else top ~30
    cut_candidates: List[int] = []
    if authorhint_idxs:
        cut_candidates.append(authorhint_idxs[0])
    if email_idxs:
        cut_candidates.append(email_idxs[0])
    if abs_idx is not None:
        cut_candidates.append(abs_idx)

    cutoff = min(cut_candidates) if cut_candidates else min(len(lines), 30)

    title_region_lines = lines[:cutoff]

    # Remove obvious noise inside title region
    title_region_lines = [ln for ln in title_region_lines if not URL_RE.search(ln)]
    title_region_lines = [ln for ln in title_region_lines if not DOI_RE.search(ln)]
    title_region = "\n".join(title_region_lines[:45]).strip()

    llm_text = (
        "TITLE_REGION:\n" + title_region +
        "\n\nAUTHORS_REGION:\n" + authors_region +
        "\n\nABSTRACT_REGION:\n" + abstract_region +
        "\n\nKEYWORDS_REGION:\n" + keywords_region
    ).strip()

    return llm_text[:max_chars]
