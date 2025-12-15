#ajsp optimized pinpointer test
import re
from typing import List, Pattern, Optional
from utils import _join_pages

# ============================================================
# 1) AJSP boilerplate patterns (KEEP AS STRINGS + COMPILE)
# ============================================================

AJSP_BLOCK_PATTERNS: List[str] = [
    # repeated journal footer/header blocks
    r"Arab Journal for Scientific Publishing\s*\(AJSP\)\s*ISSN:\s*2663-5798.*?(?:\n\s*\n|$)",
]

AJSP_LINE_PATTERNS: List[str] = [
    r"^المجلة\s+الع(?:ب|ر)بية\s+للنشر.*$",
    r"^ISSN:\s*2663-5798\s*\|\|\s*Arab Journal for Scientific Publishing.*$",
    r"^Arab Journal for Scientific Publishing\s*\(AJSP\)\s*ISSN:\s*2663-5798.*$",
    r"^www\.ajsp\.net\s*$",
    r"^https?://doi\.org/\S+\s*$",
    r"^الإصدار.*$",
    r"^العدد.*$",
    r"^تاريخ الإصدار.*$",
    r"^\s*[0-9\u0660-\u0669\u06F0-\u06F9]+\s*\.?\s*$",  # page numbers like 13, 54, 6.
]

def compile_patterns(patterns: List[str], flags: int) -> List[Pattern]:
    return [re.compile(p, flags) for p in patterns]

AJSP_BLOCK_RX: List[Pattern] = compile_patterns(AJSP_BLOCK_PATTERNS, re.IGNORECASE | re.DOTALL)
AJSP_LINE_RX: List[Pattern]  = compile_patterns(AJSP_LINE_PATTERNS,  re.IGNORECASE | re.MULTILINE)

def ajsp_strip_boilerplate(clean_text: str) -> str:
    """Assumes text already normalized by _join_pages / _basic_cleanup pipeline."""
    text = clean_text
    for rx in AJSP_BLOCK_RX:
        text = rx.sub("", text)
    for rx in AJSP_LINE_RX:
        text = rx.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# ============================================================
# 2) CUES + REGEXES
# ============================================================

EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
URL_RE   = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# Abstract/keywords headers (high precision)
ABSTRACT_HDR_AR = ["الملخص", "ملخص", "الخلاصة", "مستخلص"]
ABSTRACT_HDR_EN = ["abstract"]

KEYWORDS_HDR_AR = ["الكلمات المفتاحية", "كلمات مفتاحية", "الكلمات الدالة", "كلمات دالة"]
KEYWORDS_HDR_EN = ["keywords", "key words", "index terms"]

# Intro headers (stop markers)
INTRO_HDR_AR = ["المقدمة", "مقدمة"]
INTRO_HDR_EN = ["introduction"]

# Strong author markers (AJSP-specific)
AUTHOR_MARKERS_AR = ["إعداد الباحثة", "إعداد الباحث", "إعداد", "الباحثة", "الباحث", "الكاتبة", "الكاتب"]
AUTHOR_MARKERS_EN = ["researchers", "researcher", "author", "authors"]

# Fallback author cues (lower precision)
AR_AUTHOR_CUES = ["جامعة", "كلية", "قسم", "أستاذ", "دكتور", "المؤلف", "المؤلفون", "باحث"]
EN_AUTHOR_CUES = ["university", "college", "department", "faculty", "prof"]


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
# 3) AJSP PINPOINTER (DETERMINISTIC)
# ============================================================

def AJSP_pinpoint_imp(page1: str, page2: str, max_chars: int = 9000) -> str:
    """
    Deterministic AJSP pinpointer:
      - join+clean (via _join_pages)
      - strip AJSP boilerplate
      - single pass over lines to detect anchors (abstract/keywords/intro/emails/author-markers)
      - slice into labeled regions for the LLM
    """
    text = _join_pages(page1, page2)
    text = ajsp_strip_boilerplate(text)

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
    author_marker_idxs: List[int] = []
    authorcue_idxs: List[int] = []

    # ---- Single pass ----
    for i, ln in enumerate(lines):
        lo = ln.lower()

        if abs_idx is None and any(lo.startswith(c) for c in abs_cues):
            abs_idx = i
        if key_idx is None and any(lo.startswith(c) for c in key_cues):
            key_idx = i
        if intro_idx is None and any(lo.startswith(c) for c in intro_cues):
            intro_idx = i

        if EMAIL_RE.search(ln):
            email_idxs.append(i)

        # author marker lines (higher precision)
        if any(m in lo for m in author_mark):
            author_marker_idxs.append(i)

        # author cue fallback (lower precision)
        if any(c in lo for c in author_cues):
            authorcue_idxs.append(i)

    # ABSTRACT_REGION: end priority = keywords > intro > hard cap
    abstract_region = ""
    if abs_idx is not None:
        if key_idx is not None and key_idx > abs_idx:
            end = key_idx
        elif intro_idx is not None and intro_idx > abs_idx:
            end = intro_idx
        else:
            end = min(len(lines), abs_idx + 60)  # cap if missing markers
        abstract_region = _slice_lines(lines, abs_idx, end)

    # KEYWORDS_REGION (keywords line + next line)
    keywords_region = ""
    if key_idx is not None:
        keywords_region = _slice_lines(lines, key_idx, min(len(lines), key_idx + 2))

    # AUTHORS_REGION: emails > explicit markers > cues in top metadata area
    if email_idxs:
        authors_region = _region_from_indices(lines, email_idxs, radius=2)
    elif author_marker_idxs:
        start = author_marker_idxs[0]
        authors_region = _slice_lines(lines, start, min(len(lines), start + 10))
    else:
        top = [i for i in authorcue_idxs if i <= 50]
        authors_region = _region_from_indices(lines, top, radius=1)

    # TITLE_REGION: stop at earliest of author marker, email, abstract, doi
    doi_idxs = [i for i, ln in enumerate(lines) if "doi.org" in ln.lower()]
    cut_candidates: List[int] = []
    if author_marker_idxs:
        cut_candidates.append(author_marker_idxs[0])
    if email_idxs:
        cut_candidates.append(email_idxs[0])
    if abs_idx is not None:
        cut_candidates.append(abs_idx)
    if doi_idxs:
        cut_candidates.append(doi_idxs[0])

    cutoff = min(cut_candidates) if cut_candidates else min(len(lines), 25)

    title_region_lines = lines[:cutoff]
    title_region_lines = [ln for ln in title_region_lines if not URL_RE.search(ln)]
    title_region = "\n".join(title_region_lines[:35]).strip()

    llm_text = (
        "TITLE_REGION:\n" + title_region +
        "\n\nAUTHORS_REGION:\n" + authors_region +
        "\n\nABSTRACT_REGION:\n" + abstract_region +
        "\n\nKEYWORDS_REGION:\n" + keywords_region
    ).strip()

    return llm_text[:max_chars]
