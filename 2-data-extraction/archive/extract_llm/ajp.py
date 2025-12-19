import re
from typing import List, Pattern, Optional
from utils import _join_pages

# -------------------------
# Author cues (fallback)
# -------------------------
AR_AUTHOR_CUES = ["جامعة", "كلية", "قسم", "أستاذ", "د.", "دكتور", "المؤلف", "المؤلفون", "باحث"]
EN_AUTHOR_CUES = ["university", "college", "department", "author", "authors", "prof", "dr."]

# -------------------------
# Abstract / keywords cues
# Keep only header-like cues here (high precision).
# "هدفت/نتائج/منهج..." are content cues; they can cause false positives as anchors.
# -------------------------
ABSTRACT_HDR_AR = ["الملخص", "ملخص", "الخلاصة", "مستخلص"]
ABSTRACT_HDR_EN = ["abstract", "summary"]

KEYWORDS_HDR_AR = ["الكلمات المفتاحية", "كلمات مفتاحية", "الكلمات الدالة", "كلمات دالة"]
KEYWORDS_HDR_EN = ["keywords", "key words", "index terms"]

# -------------------------
# Compiled regexes (compile once)
# -------------------------
EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# For safety with English word boundaries
ABSTRACT_RX = re.compile(r"\babstract\b", re.IGNORECASE)
KEYWORDS_RX = re.compile(r"\bkeywords?\b", re.IGNORECASE)

# AJP boilerplate patterns (compile once)
AJP_BLOCK_PATTERNS = [
    re.compile(r"Follow this and additional works at:.*?Recommended Citation", re.IGNORECASE | re.DOTALL),
    re.compile(r"Recommended Citation.*?Available at:\s*https?://\S+", re.IGNORECASE | re.DOTALL),
    re.compile(r"This Article is brought to you.*?(?:\n\s*\n|$)", re.IGNORECASE | re.DOTALL),
    re.compile(r"It has been accepted for.*?(?:\n\s*\n|$)", re.IGNORECASE | re.DOTALL),
]

AJP_LINE_PATTERNS = [
    re.compile(r"^Association of Arab Universities Journal for Education and\s*Psychology\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^Volume\s+\d+\s*\|\s*Issue\s+\d+\s*Article\s+\d+\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*\d{4}\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^مجلة اتحاد الجامعات العربية للتربية وعلم النفس.*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^.*المجلد.*العدد.*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*[0-9\u0660-\u0669\u06F0-\u06F9]+\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*Available at:\s*https?://\S+\s*$", re.IGNORECASE | re.MULTILINE),
]

RUNNING_HEADER_RX = re.compile(r"^[^\n]{20,200}(?:\.\.\.|؛).*$", re.MULTILINE)


def ajp_strip_boilerplate(clean_text: str) -> str:
    """Assumes text is already cleaned/normalized by your _basic_cleanup/_join_pages pipeline."""
    text = clean_text

    for rx in AJP_BLOCK_PATTERNS:
        text = rx.sub("", text)

    for rx in AJP_LINE_PATTERNS:
        text = rx.sub("", text)

    # remove common running header line on page 2
    text = RUNNING_HEADER_RX.sub("", text)

    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _prep_cues(*lists: List[str]) -> List[str]:
    """Lowercase + remove duplicates while preserving order."""
    seen = set()
    out = []
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


def AJP_pinpoint_imp(page1: str, page2: str, max_chars: int = 9000) -> str:
    """
    Deterministic AJP pinpointer (optimized):
    - join+clean (via _join_pages)
    - strip AJP boilerplate
    - single pass over lines to detect anchors (abstract/keywords/emails/author-cues)
    - deterministic slicing into regions
    """
    text = _join_pages(page1, page2)
    text = ajp_strip_boilerplate(text)

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    # Prepare cues once
    abs_cues = _prep_cues(ABSTRACT_HDR_AR, ABSTRACT_HDR_EN)
    key_cues = _prep_cues(KEYWORDS_HDR_AR, KEYWORDS_HDR_EN)
    author_cues = _prep_cues(AR_AUTHOR_CUES, EN_AUTHOR_CUES)

    abs_idx: Optional[int] = None
    key_idx: Optional[int] = None
    email_idxs: List[int] = []
    authorcue_idxs: List[int] = []

    # ---- Single pass ----
    for i, ln in enumerate(lines):
        ln_low = ln.lower()

        # abstract header
        if abs_idx is None:
            if any(ln_low.startswith(c) for c in abs_cues) or ABSTRACT_RX.search(ln):
                abs_idx = i

        # keywords header
        if key_idx is None:
            if any(ln_low.startswith(c) for c in key_cues) or KEYWORDS_RX.search(ln):
                key_idx = i

        # emails
        if EMAIL_RE.search(ln):
            email_idxs.append(i)

        # author cues (fallback)
        # note: we keep this lightweight; no regex needed
        if any(c in ln_low for c in author_cues):
            authorcue_idxs.append(i)

    # ABSTRACT_REGION
    abstract_region = ""
    if abs_idx is not None:
        end = key_idx if (key_idx is not None and key_idx > abs_idx) else len(lines)
        abstract_region = _slice_lines(lines, abs_idx, end)

    # KEYWORDS_REGION (keywords line + next line)
    keywords_region = ""
    if key_idx is not None:
        keywords_region = _slice_lines(lines, key_idx, min(len(lines), key_idx + 2))

    # AUTHORS_REGION (emails first, else author cues)
    if email_idxs:
        authors_region = _region_from_indices(lines, email_idxs, radius=2)
    else:
        # Author cues can be noisy; tighten:
        # Only consider cues in the first ~40 lines (typical metadata zone)
        authorcue_idxs_top = [i for i in authorcue_idxs if i <= 40]
        authors_region = _region_from_indices(lines, authorcue_idxs_top, radius=1)

    # TITLE_REGION (top until earliest of email/abstract; else top 25)
    cut_candidates = []
    if email_idxs:
        cut_candidates.append(email_idxs[0])  # already in ascending order
    if abs_idx is not None:
        cut_candidates.append(abs_idx)
    cutoff = min(cut_candidates) if cut_candidates else min(len(lines), 25)

    title_region_lines = lines[:cutoff]
    title_region_lines = [ln for ln in title_region_lines if not URL_RE.search(ln)]
    title_region = "\n".join(title_region_lines[:30]).strip()

    llm_text = (
        "TITLE_REGION:\n" + title_region +
        "\n\nAUTHORS_REGION:\n" + authors_region +
        "\n\nABSTRACT_REGION:\n" + abstract_region +
        "\n\nKEYWORDS_REGION:\n" + keywords_region
    ).strip()

    return llm_text[:max_chars]
