import re
from pyarabic.araby import strip_tashkeel, strip_tatweel, normalize_alef, normalize_teh

#This function normalises text , removes ocr noise and removes non arabic text blocs
def clean_page(text: str) -> str:
    if not isinstance(text, str): 
        return ""
    
    # 1. Basic Arabic Normalization
    text = strip_tashkeel(text)
    text = strip_tatweel(text)
    text = normalize_alef(text)
    text = normalize_teh(text)

    # 2. Fix English/Mixed Hyphenation (e.g., "docu- \n ment" or "الخصا- \n ئص")
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)

    # 3. Layout Cleanup
    text = text.replace('|', ' ')
    text = re.sub(r'_{3,}', ' ', text)
    text = re.sub(r'-{3,}', ' ', text)
    # Remove lines that are only numbers (page numbers)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

    # 4. Filter only "Garbage" characters, but KEEP English and Arabic
    # This keeps: Arabic, English, Numbers, and common punctuation
    allowed_chars = r'[^\w\s\u0600-\u06FF\.,:;\-\(\)\[\]/@\+\*]'
    text = re.sub(allowed_chars, ' ', text)

    # 5. REMOVE PURE ENGLISH BLOCKS (The "Catch")
    # We split by double newline to identify paragraphs/blocks
    blocks = re.split(r'\n\s*\n', text)
    filtered_blocks = []

    for block in blocks:
        # Check if the block contains any Arabic characters
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', block))
        
        if has_arabic:
            # If it has Arabic, we keep the whole block 
            # (This preserves English citations/names inside Arabic text)
            filtered_blocks.append(block)
        else:
            # If it has NO Arabic, we check if it's "Metadata" (short) or an "Abstract" (long)
            # We discard long pure English blocks (like the Abstract/English title)
            # We keep very short blocks like "Doi: 10.123/..." or years
            if len(block.strip()) < 50:
                filtered_blocks.append(block)

    text = "\n\n".join(filtered_blocks)

    # 6. Final Whitespace Management
    text = re.sub(r'[ \t]+', ' ', text) # Collapse horizontal spaces
    text = re.sub(r'\n\s*\n*', '\n', text) # Collapse multiple newlines to single

    return text.strip()


import re
import pandas as pd
arabic_pattern = re.compile(r'[\u0600-\u06FF]')
#move non arabic strings to authors_en

def move_non_arabic(row):
    authors = row.get("authors","")
    if not authors:
        return pd.Series({"authors": None, "authors_en": None})

    # Join all names to check for any Arabic letter
    if arabic_pattern.search(str(authors)):
        return pd.Series({"authors": authors, "authors_en": None})
    else:
        return pd.Series({"authors": None, "authors_en": authors})

import re
import pandas as pd

# =============================================================================
# SHARED HELPERS (Logic used by both functions)
# =============================================================================

def _generate_skeleton_pattern(word):
    """Generates a regex matching the consonant skeleton of a word."""
    # Noise = vowels, spaces, tatweel, common punctuation
    noise_class = r"[اوي\s_\-\.\+\*]*"
    pattern = ""
    for char in word:
        if char in "اأإآوي ": 
            pattern += noise_class
        elif char == 'ة':
            pattern += r"[هتة]" + noise_class
        else:
            pattern += re.escape(char) + r"+?" + noise_class
    return pattern

def _prepare_extraction_context(row):
    """
    Prepares text (merging/normalization) and compiles regex patterns.
    Returns a dictionary containing the context needed for extraction.
    """
    # 1. Text Merging
    p1 = str(row.get('page1', '')).strip()
    p2 = str(row.get('page2', '')).strip()

    if len(p1) > 20 and len(p2) > 20:
        header_chunk = p1[:40].split('\n')[0].strip()[:20]
        if header_chunk:
            safe_header = re.escape(header_chunk)
            match = re.search(fr"^{safe_header}.*?\n", p2, re.IGNORECASE)
            if match:
                p2 = p2[match.end():].strip()

    full_text = p1 + " \n " + p2
    
    # 2. Normalization for Search Index
    search_text = full_text.lower()
    search_text = re.sub(r'[أإآا]', 'ا', search_text)
    search_text = re.sub(r'[ةه]', 'ه', search_text)
    search_text = re.sub(r'[يىئ]', 'ي', search_text)

    # 3. Pattern Definitions
    abs_roots = ["ملخص", "مستخلص", "خلاصة", "موجز"]
    kw_roots  = ["كلمات", "مفتاحية", "دالة", "رئيسية"]
    stop_roots = ["مقدمة", "تمهيد", "Introduction", "Correspondence", "المراجع"]

    # Compile Abstract Regex
    abs_regex = r"(?:" + "|".join([_generate_skeleton_pattern(w) for w in abs_roots]) + r")"
    
    # Compile Keyword Start Regex
    kalimat_pat = _generate_skeleton_pattern("كلمات")
    second_part_pat = r"(?:" + "|".join([_generate_skeleton_pattern(w) for w in ["مفتاحية", "دالة", "رئيسية"]]) + r")"
    kw_start_pattern = fr"(?:{kalimat_pat}.{{0,15}}{second_part_pat}|Keywords|Key\s*words)"

    # Compile Stop Pattern
    stop_words_simple = [r"Doi", r"1\.", r"\*", r"First", r"I\."]
    stop_pattern = r"(?:" + "|".join([_generate_skeleton_pattern(w) for w in stop_roots] + stop_words_simple) + r")"

    return {
        "full_text": full_text,
        "search_text": search_text,
        "abs_regex": abs_regex,
        "kw_start_pattern": kw_start_pattern,
        "stop_pattern": stop_pattern
    }

# =============================================================================
# FUNCTION 1: EXTRACT ABSTRACT
# =============================================================================

def extract_abstract(row):
    """
    Extracts the Abstract using root-based search.
    Includes a FALLBACK if no 'Abstract' header is found, searching for 
    start-of-abstract verbs (e.g., 'The study aimed', 'هدفت الدراسة').
    """
    ctx = _prepare_extraction_context(row)
    
    extracted_abstract = None
    candidates = []

    # =========================================================================
    # STRATEGY 1: Standard Header Search (Abstract, Mulakhas...)
    # =========================================================================
    for match in re.finditer(ctx['abs_regex'], ctx['search_text']):
        start_idx = match.end()
        
        # Define search window (look ahead ~3000 chars)
        window = ctx['search_text'][start_idx : start_idx + 3000]
        
        # Stop at Keyword Start OR Section Stop
        stopper = re.search(fr"({ctx['kw_start_pattern']}|{ctx['stop_pattern']})", window)
        
        if stopper:
            end_idx = start_idx + stopper.start()
        else:
            end_idx = start_idx + min(len(window), 1000)
            
        candidate = ctx['full_text'][start_idx:end_idx].strip()
        candidate = re.sub(r"^[:\-\.]+\s*", "", candidate) # Clean leading punctuation
        
        # Validation: Must contain Arabic and be of reasonable length
        if len(candidate) > 50 and re.search(r'[\u0600-\u06FF]', candidate):
            candidates.append(candidate)
            
    if candidates:
        # If headers found, return the longest candidate
        extracted_abstract = max(candidates, key=len)
        extracted_abstract = re.sub(r'\s+', ' ', extracted_abstract).strip()
        return extracted_abstract

    # =========================================================================
    # STRATEGY 2: Fallback - Purpose Statement Search (No Header Found)
    # =========================================================================
    # If we are here, no "Mulakhas" or "Abstract" header was found.
    # We look for verbs like: هدفت، استهدفت، تهدف، سعت، يهدف
    
    # 1. Define Verb Roots (H-D-F, S-A-Y, etc.)
    # We use specific conjugated forms to avoid matching random words like "Target" (noun)
    fallback_verbs = [
        "هدفت", "استهدفت", "تهدف", "يهدف", "هدف",   # H-D-F variations
        "سعت", "تسعى", "يسعى",                       # S-A-Y (Strive) variations
        "تناولت", "تتناول",                          # T-N-W-L (Deal with)
        "ركزت", "تركز",                              # R-K-Z (Focus)
        "تكمن",                                      # T-K-M-N (Reside/Lie in - common in 'problem statements')
        "aims", "aimed", "objective", "purpose"      # English Fallbacks
    ]
    
    # Generate root-based patterns for these verbs
    fallback_regex_list = [_generate_skeleton_pattern(w) for w in fallback_verbs]
    fallback_pattern = r"(?:\b" + r"|\b".join(fallback_regex_list) + r")"
    
    # Search for the FIRST occurrence of a purpose verb
    # We assume the abstract starts roughly here if no header exists.
    fallback_match = re.search(fallback_pattern, ctx['search_text'])
    
    if fallback_match:
        start_idx = fallback_match.start() # Start extracting FROM the verb
        
        # Define Window
        window = ctx['search_text'][start_idx : start_idx + 3000]
        
        # Stop at Keyword Start OR Section Stop
        # Note: We must ensure we don't stop immediately if the "stop word" is part of the sentence
        # (unlikely for strict stops like "Introduction" or "Keywords")
        stopper = re.search(fr"({ctx['kw_start_pattern']}|{ctx['stop_pattern']})", window)
        
        if stopper:
            end_idx = start_idx + stopper.start()
        else:
            end_idx = start_idx + min(len(window), 1000)
            
        candidate = ctx['full_text'][start_idx:end_idx].strip()
        
        # Heuristic: Fallbacks often catch body text by mistake. 
        # We assume Abstracts appear EARLY. If start_idx is huge (> 3000), it's likely body text.
        # Also, valid abstracts usually mention "Study", "Research", "Paper" nearby.
        if start_idx < 3000 and len(candidate) > 50:
             extracted_abstract = candidate
             extracted_abstract = re.sub(r'\s+', ' ', extracted_abstract).strip()

    return extracted_abstract

# =============================================================================
# FUNCTION 2: EXTRACT KEYWORDS
# =============================================================================

def extract_keywords(row):
    """
    Extracts Keywords using strict line constraints.
    """
    ctx = _prepare_extraction_context(row)
    
    extracted_keywords = None
    kw_candidates = []
    
    for match in re.finditer(ctx['kw_start_pattern'], ctx['search_text']):
        start_idx = match.end()
        
        # 1. Determine the "Active Line"
        # Check if header is followed immediately by a newline (e.g. "Keywords:\n")
        immediate_chunk = ctx['search_text'][start_idx : start_idx + 5]
        
        if '\n' in immediate_chunk:
            newline_pos = ctx['search_text'].find('\n', start_idx)
            start_idx = newline_pos + 1
        
        # 2. Find the END of this specific line
        next_newline = ctx['search_text'].find('\n', start_idx)
        if next_newline == -1:
            next_newline = len(ctx['search_text'])
            
        # Strict window: ONLY up to the next newline
        window_end = next_newline
        line_content = ctx['search_text'][start_idx : window_end]
        
        # 3. Check for Stop Marker within the line
        pre_char = ctx['search_text'][match.start()-1] if match.start() > 0 else ""
        
        # Construct stop pattern specifically for this line check
        current_stop_pat = ctx['stop_pattern'] + r"|" + ctx['abs_regex']
        if pre_char == '(':
            current_stop_pat += r"|\)"

        stopper = re.search(current_stop_pat, line_content)
        
        if stopper:
            final_end_idx = start_idx + stopper.start()
        else:
            final_end_idx = window_end
            
        # Extract from full_text
        raw_kw = ctx['full_text'][start_idx:final_end_idx].strip()
        raw_kw = re.sub(r"^[:\-\.]+\s*", "", raw_kw)
        
        if len(raw_kw) > 3:
            kw_candidates.append(raw_kw)
            
    if kw_candidates:
        # Use the last candidate as it's typically the one closest to the body/abstract
        best_raw_kw = kw_candidates[-1] 
        
        # Splitting Logic
        tokens = re.split(r'[،,;؛\|\•]', best_raw_kw)
        clean_list = []
        for t in tokens:
            t = t.strip().strip('.-:()[]')
            # Sanity check: Keyword phrase shouldn't be a full paragraph
            if len(t) > 2 and not t.isdigit() and len(t) < 100:
                clean_list.append(t)
        
        # Fallback: If only one token found but it has spaces, check if it's a space-delimited list
        if len(clean_list) == 1 and len(clean_list[0].split()) > 4:
            pass # Return as a single block rather than splitting erroneously
             
        if clean_list:
            extracted_keywords = clean_list

    return extracted_keywords
import re
import pandas as pd

import re
import pandas as pd

def validate_author_name(name_candidate):
    """
    Validates if a string is a human name using negative lookups.
    Updated based on specific failure cases (Edaad, Locations, Degrees).
    """
    if not name_candidate or not isinstance(name_candidate, str):
        return False, ""

    name = name_candidate.strip()

    # --- 1. PRE-CLEANING (Aggressive) ---
    # Remove leading/trailing punctuation and OCR artifacts
    # e.g. ". د/" or ".." or "OO a"
    name = re.sub(r'^[\.\-/_:,\s\*]+', '', name)
    name = re.sub(r'[\.\-/_:,\s\*]+$', '', name)
    
    # Remove Academic Titles (English & Arabic)
    # Handle variations: Dr., Dr/, d., د., د/, أ.د, ا.د (Bare Alef)
    titles_re = r'^\s*(?:Co-Prof|Prof|Dr|Mr|Mrs|Ms|Eng|Assoc|Lecturer|Researcher|Student|Candidate|د\.|أ\.د|ا\.د|بروف|م\.|الذكتور|الاستاذ|الدكتور|الباحث|الطالب|المعلم|د\/|أ\/)\.?\s*'
    name = re.sub(titles_re, '', name, flags=re.IGNORECASE)

    # --- 2. INSTANT REJECTION RULES ---
    
    # Too short (<3 chars) or contains digits
    if len(name) < 3: return False, ""
    if re.search(r'\d', name): return False, "" 
    
    # Email/URL indicators
    if any(x in name.lower() for x in ['@', 'www.', '.com', '.edu', '.org', '.net']): return False, ""

    # --- 3. THE "BAD WORD" BLACKLIST ---
    
    bad_patterns = [
        # A. The "Preparation" Problem (Very common in your sample)
        r"^اعداد", r"^إعداد", r"^اعسداد", r"إشراف", r"تقديم", r"Prepared by",
        
        # B. Database/Repository Boilerplate
        r"This Article is brought", r"open access", r"rights reserved", r"Creative Commons",
        r"Edu Search", r"Dar Al Mandumah", r"دار المنظومة", r"معرفة", r"دوريات", r"المجلة",
        r"brought to you by", r"Digital Commons", r"Copyright",
        
        # C. Locations (Country names appearing alone)
        r"Kingdom", r"Republic", r"Saudi", r"Jordan", r"Oman", r"Egypt", r"Algeria", r"Yemen", r"Palestine", r"Kuwait",
        r"المملكة", r"الجمهورية", r"السعودية", r"الاردن", r"عمان", r"مصر", r"الجزائر", r"السودان", r"اليمن", r"فلسطين", r"الكويت", r"العراق",
        
        # D. Affiliations (University/College)
        r"University", r"College", r"Department", r"Faculty", r"Ministry", r"School", r"Institute", r"Deanship",
        r"جامعة", r"كلية", r"قسم", r"وزارة", r"معهد", r"عمادة", r"رئاسة", r"الجامعة", r"للدراسات",
        
        # E. Academic Degrees / Roles (Appearing as names)
        r"Master", r"PhD", r"Thesis", r"Dissertation",
        r"ماجستير", r"دكتوراه", r"رسالة", r"اطروحة", r"طالب", r"مدرس", r"معلم", r"مدير",
        
        # F. Journal Metadata
        r"Journal", r"Vol", r"Issue", r"No\.", r"pp\.", r"Page", r"ISSN",
        r"مجلد", r"عدد", r"صفحة", r"طبعة",
        
        # G. Abstract/Sentence Starters
        r"The researcher", r"The study", r"This paper", r"found that", r"aimed to", r"concluded",
        r"الباحث", r"الدراسة", r"هدفت", r"توصلت", r"نتائج", r"تناول", r"ملخص", r"مقدمة", r"مشكلة",
        r"The Degree", r"The Level", r"The Impact", r"The Effect", r"Developing",
        r"درجة", r"أثر", r"فاعلية", r"مستوى", r"واقع", r"تطوير", r"بناء"
    ]
    
    # Compile blacklist
    blacklist_regex = r"(?:" + "|".join(bad_patterns) + r")"
    if re.search(blacklist_regex, name, re.IGNORECASE):
        return False, ""

    # --- 4. LINGUISTIC / LOGIC CHECKS ---

    # Rule: Lowercase English Check (e.g. "teachers", "motor")
    if re.match(r'^[a-z]', name): 
        return False, ""

    # Rule: Structure Check
    tokens = name.split()
    
    # Mixed English/Arabic in one name is usually an error (e.g. "The Ability ل")
    has_eng = bool(re.search(r'[a-zA-Z]', name))
    has_ara = bool(re.search(r'[\u0600-\u06FF]', name))
    if has_eng and has_ara:
        return False, ""

    # Length Check: Names rarely exceed 5 words.
    if len(tokens) > 5: return False, ""
    
    # Single letter check (Too many initials = broken OCR)
    single_letters = [t for t in tokens if len(t) == 1]
    if len(single_letters) > 2: return False, ""

    return True, name

def extract_authors_heuristic(row):
    """
    Extracts author names using heuristics.
    SKIPS extraction if 'authors' field is already populated.
    """
    
    # 0. Short-Circuit
    existing = row.get('authors')
    if isinstance(existing, list) and len(existing) > 0: return existing
    if isinstance(existing, str) and len(existing.strip()) > 1 and existing.lower() != 'nan': return [existing]

    # 1. Preparation
    text = str(row.get('page1', ''))[:2500] 
    search_text = text.replace('ـ', '')
    search_text = re.sub(r'[أإآ]', 'ا', search_text)
    
    # 2. Define Boundaries
    stop_markers = [
        r"تاريخ تسلم", r"تاريخ استلام", r"تاريخ قبول", r"Received", r"Accepted",
        r"ملخص", r"مستخلص", r"Abstract", r"Summary",
        r"المقدمة", r"مقدمة", r"Introduction", r"Correspondence",
        r"This Article is brought", r"هدفت الدراسة", r"هدف البحث",
        r"rights reserved", r"Open Access", r"Creative Commons"
    ]
    
    stop_pattern = r"(?:" + "|".join(stop_markers) + r")"
    stop_match = re.search(stop_pattern, search_text, re.IGNORECASE)
    
    if stop_match:
        end_pos = stop_match.start()
        start_pos = max(0, end_pos - 500)
        candidate_zone = text[start_pos:end_pos]
    else:
        candidate_zone = text[:600]

    # 3. Extraction Strategies
    raw_text = ""

    # Strategy A: Asterisk Anchor (*)
    asterisk_match = re.search(r'\*\s*([^\*\n]+)$', candidate_zone, re.MULTILINE)
    
    if asterisk_match:
        raw_text = asterisk_match.group(1).strip()
    else:
        # Strategy B: Reverse Line Scan
        lines = [line.strip() for line in candidate_zone.split('\n') if line.strip()]
        for line in reversed(lines):
            is_valid_structure, _ = validate_author_name(line)
            if is_valid_structure:
                raw_text = line
                break

    # 4. Processing & Validation
    extracted_authors = []
    
    if raw_text:
        # Splitters: Added semicolon and made comma splitting stricter/safer
        splitters = r"(?:\s+و\s+|\s+and\s+|;|،|,|&)"
        tokens = re.split(splitters, raw_text)
        
        for t in tokens:
            t = t.strip().strip('*').strip()
            
            # Constraint: Truncate to first 4 words
            name_parts = t.split()
            if len(name_parts) > 4:
                t = " ".join(name_parts[:4])
            
            # Validation
            is_valid, cleaned_name = validate_author_name(t)
            
            if is_valid:
                extracted_authors.append(cleaned_name)

    return extracted_authors

