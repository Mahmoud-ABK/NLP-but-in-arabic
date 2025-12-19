# ARPD pinpointer + cleaning (full code cell)
import re
from typing import List, Pattern, Optional
from utils import _join_pages
# ============================================================
# REQUIRED: you must already have this in your project
#   - _join_pages(page1, page2) -> str   (your normalization/cleanup)
# ============================================================
# def _join_pages(page1: str, page2: str) -> str:
#     ...

# -------------------------
# Regex helpers (compile once)
# -------------------------
EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
URL_RE   = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# -------------------------
# ARPD anchors (high precision headers)
# -------------------------
ABSTRACT_HDR_AR = [
    "ملخص البحث", "المستخلص", "الملخص", "ملخص", "الخلاصة", "مستخلص"
]
ABSTRACT_HDR_EN = ["abstract"]

KEYWORDS_HDR_AR = [
    "الكلمات المفتاحية", "الكلمات الدالة", "كلمات مفتاحية", "كلمات دالة"
]
KEYWORDS_HDR_EN = ["keywords", "key words", "index terms"]

INTRO_HDR_AR = ["مقدمة", "المقدمة", "تمهيد"]
INTRO_HDR_EN = ["introduction"]

# -------------------------
# ARPD author cues (fallback)
# -------------------------
AR_AUTHOR_CUES = [
    "إعداد", "اعداد", "بقلم", "الباحث", "الباحثة",
    "د/", "د.", "أ.د", "أ.م.د", "أستاذ", "أستاذة",
    "جامعة", "كلية", "قسم"
]
EN_AUTHOR_CUES = ["by", "author", "researcher", "prof", "dr.", "university", "college", "department"]

# -------------------------
# Boilerplate / headers / footers patterns
# Keep your strings, then compile (like you asked)
# -------------------------
ARPD_BLOCK_PATTERNS: List[str] = [
    # Some sources repeat header blocks twice; these patterns remove known directory/index blocks
    r"المجلة\s+معرفة\s+على\s+دوريات\s+بنك\s+المعرفة\s+المصرى.*?(?:\n\s*\n|$)",
    r"دار\s+المنظومة.*?(?:\n\s*\n|$)",
]

ARPD_LINE_PATTERNS: List[str] = [
    # Egyptian journal repeating headers
    r"^المجلة\s+المصرية\s+للتربية\s+العلمية.*$",
    r"^\s*رقم\s+الإيداع\s*:.*$",
    r"^\s*E\.\s*ISSN\s*:.*$",
    r"^\s*ISSN\s*:.*$",
    r"^\s*Edu\s*Search\s*$",
    r"^\s*دار\s+المنظومة\s*$",
    r"^\s*المجلة\s+معرفة\s+على\s+دوريات\s+بنك\s+المعرفة\s+المصرىء.*$",

    # Common noisy numeric-only lines
    r"^\s*[0-9\u0660-\u0669\u06F0-\u06F9]+\s*\.?\s*$",

    # URL-only lines
    r"^\s*(https?://\S+|www\.\S+)\s*$",

    # Occasional Arabic publication meta lines (very OCR-variable, keep broad)
    r"^جامعة.*$",
]

def _compile(patterns: List[str], flags: int) -> List[Pattern]:
    return [re.compile(p, flags) for p in patterns]

ARPD_BLOCK_RX = _compile(ARPD_BLOCK_PATTERNS, re.IGNORECASE | re.DOTALL)
ARPD_LINE_RX  = _compile(ARPD_LINE_PATTERNS,  re.IGNORECASE | re.MULTILINE)

# -------------------------
# Utility
# -------------------------
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

def arpd_strip_boilerplate(clean_text: str) -> str:
    """
    Remove repeated journal headers/footers and indexing boilerplate.
    Assumes prior normalization by _join_pages.
    """
    text = clean_text

    for rx in ARPD_BLOCK_RX:
        text = rx.sub("", text)

    for rx in ARPD_LINE_RX:
        text = rx.sub("", text)

    # collapse blank lines
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

# -------------------------
# Main pinpointer
# -------------------------
def ARPD_pinpoint_imp(page1: str, page2: str, max_chars: int = 9000) -> str:
    """
    Deterministic ARPD pinpointer:
      - join+clean (_join_pages)
      - strip boilerplate (ARPD-specific)
      - single pass line scanning for anchors:
          abstract / keywords / intro / emails / author-cues
      - slice TITLE/AUTHORS/ABSTRACT/KEYWORDS regions for LLM
    """
    text = _join_pages(page1, page2)
    text = arpd_strip_boilerplate(text)

    # ARPD OCR: mostly \n as universal separator => line-based
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    abs_cues   = _prep_cues(ABSTRACT_HDR_AR, ABSTRACT_HDR_EN)
    key_cues   = _prep_cues(KEYWORDS_HDR_AR, KEYWORDS_HDR_EN)
    intro_cues = _prep_cues(INTRO_HDR_AR, INTRO_HDR_EN)
    auth_cues  = _prep_cues(AR_AUTHOR_CUES, EN_AUTHOR_CUES)

    abs_idx: Optional[int] = None
    key_idx: Optional[int] = None
    intro_idx: Optional[int] = None

    email_idxs: List[int] = []
    authorhint_idxs: List[int] = []

    # ---- Single pass ----
    for i, ln in enumerate(lines):
        lo = ln.lower()

        # abstract header
        if abs_idx is None and any(lo.startswith(c) for c in abs_cues):
            abs_idx = i

        # keywords header
        if key_idx is None and any(lo.startswith(c) for c in key_cues):
            key_idx = i

        # intro header (stop marker)
        if intro_idx is None and any(lo.startswith(c) for c in intro_cues):
            intro_idx = i

        # emails
        if EMAIL_RE.search(ln):
            email_idxs.append(i)

        # author cues (only care near top zone)
        if i <= 80 and any(c in lo for c in auth_cues):
            authorhint_idxs.append(i)

    # -------------------------
    # ABSTRACT_REGION
    # -------------------------
    abstract_region = ""
    if abs_idx is not None:
        # end priority: keywords > intro > cap
        if key_idx is not None and key_idx > abs_idx:
            end = key_idx
        elif intro_idx is not None and intro_idx > abs_idx:
            end = intro_idx
        else:
            # If no explicit stop marker, take a reasonable chunk
            end = min(len(lines), abs_idx + 90)

        abstract_region = _slice_lines(lines, abs_idx, end)

    # -------------------------
    # KEYWORDS_REGION
    # -------------------------
    keywords_region = ""
    if key_idx is not None:
        keywords_region = _slice_lines(lines, key_idx, min(len(lines), key_idx + 3))

    # -------------------------
    # AUTHORS_REGION
    # -------------------------
    if email_idxs:
        authors_region = _region_from_indices(lines, email_idxs, radius=3)
    elif authorhint_idxs:
        # compact metadata window around first author cue
        s = max(0, authorhint_idxs[0] - 4)
        e = min(len(lines), s + 25)
        authors_region = _slice_lines(lines, s, e)
        authors_region = "\n".join([x for x in authors_region.split("\n") if not URL_RE.search(x)]).strip()
    else:
        authors_region = ""

    # -------------------------
    # TITLE_REGION
    # -------------------------
    # Stop at earliest of (author/email/abstract), else top ~35 lines
    cut_candidates: List[int] = []
    if authorhint_idxs:
        cut_candidates.append(authorhint_idxs[0])
    if email_idxs:
        cut_candidates.append(email_idxs[0])
    if abs_idx is not None:
        cut_candidates.append(abs_idx)

    cutoff = min(cut_candidates) if cut_candidates else min(len(lines), 35)

    title_region_lines = lines[:cutoff]
    title_region_lines = [ln for ln in title_region_lines if not URL_RE.search(ln)]
    title_region = "\n".join(title_region_lines[:50]).strip()

    llm_text = (
        "TITLE_REGION:\n" + title_region +
        "\n\nAUTHORS_REGION:\n" + authors_region +
        "\n\nABSTRACT_REGION:\n" + abstract_region +
        "\n\nKEYWORDS_REGION:\n" + keywords_region
    ).strip()

    return llm_text[:max_chars]
