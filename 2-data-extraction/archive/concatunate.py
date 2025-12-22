#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd

# Paths to your CSV files
file1 = "02-extracted-pages.csv"
file2 = "2-step2.csv"

def print_headers(path):
    try:
        df = pd.read_csv(path, nrows=0)  # load only header row
        print(f"\nHeaders for {path}:")
        print(list(df.columns))
    except Exception as e:
        print(f"Error reading {path}: {e}")

print_headers(file1)
print_headers(file2)


# In[3]:


import pandas as pd

# Load the two CSVs
df_main = pd.read_csv("02-extracted-pages.csv")
df_tokens = pd.read_csv("2-step2.csv")

# Select only the needed columns
df_tokens_small = df_tokens[[
    "article_id",
    "page1_token_count",
    "page2_token_count"
]]

# Merge on article_id
df_merged = df_main.merge(df_tokens_small, on="article_id", how="left")

# Save the updated CSV
df_merged.to_csv("02-extracted-pages-with-tokens.csv", index=False)

print("Done! New file created: 02-extracted-pages-with-tokens.csv")


# In[4]:


for col in df_merged.columns:
    print(f"{col:<20}  {df_merged[col].isnull().sum():>10}")




# In[5]:


count_missing = df_merged[df_merged["title"].isnull() & df_merged["title_en"].isnull()].shape[0]
print("entries missing title_en and title:", count_missing)


# In[6]:


print("Unique values in general_field:")
print(df_merged["general_field"].dropna().unique())

print("\nUnique values in field:")
print(df_merged["field"].dropna().unique())


# In[4]:


import pandas as pd
df = pd.read_csv("02-extracted-pages-with-tokens.csv")
print(df["source"].dropna().unique())


# # extract field 

# In[8]:


"""
pip install langchain langchain-openai pydantic

Server:
  llama.cpp running at http://localhost:6000/v1
  model alias: qwen-extractor-1
"""

from enum import Enum
from typing import List, Any, Dict

from pydantic import BaseModel, Field
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser



# In[9]:


sample = """
   Association of Arab Universities Journal for Education and

Psychology
Volume 23 | Issue 2 Article 1
2025

لمهارات البحث الإجرائي وصعوبات تنفيذه من خلال إعدادهم
‎The Level of Acquisition of Action Research‏ .لمشروع التخرجح
‎Skills and Difficulties in its preperarions Through Graduation‏
‎Project Among College of Education Students at Sultan Qaboos‏
‎University‏

نور النجار
‎nour.najar@seciauni.org‏ ,كلية التربية,. جامعة السلطان ‎pools‏ عمان

Follow this and additional works at: https://digitalcommons.aaru.edu.jo/aaru_jep

Digibalrt of the Education Commons
Commons

Network ‏ا‎

Recommended Citation

النجار, نور )2025( "درجة اكتساب طلبة كلية ‎av yall‏ بجامعة السلطان قابوس لمهارات البحث الإجرائي وص 992ب

‎The Level of Acquisition of Action Research Skills and Difficulties in‏ .تنفيذه من خلال إعدادهم لمشروع التخرج
‎its preperarions Through Graduation Project Among College of Education Students at Sultan Qaboos‏
‎University,’ Association of Arab Universities Journal for Education and Psychology. Vol. 23: Iss. 2, Article‏
.1

‎Available at: https://digitalcommons.aaru.edu.jo/aaru_jep/vol23/iss2/1

‎This Article is brought to you for free and open access by Arab Journals Platform. It has been accepted for
inclusion in Association of Arab Universities Journal for Education and Psychology by an authorized editor. The
journal is hosted on Digital Commons, an Elsevier platform. For more information, please contact
marah@aaru.edu.jo,rakan@aaru.edu.jo .

مجلة اتحاد الجامعات العربية للتربية وعلم النفس 0 0 ...ممم المجلد الثالث والعشرون - العدد الثاني - 8٠؟5١؟‏

‎day‏ اكتساب طلبة ‎dS‏ التربية بجامعة السلطان قابوس لمهارات البحث
الإجرائي وصعوبات تنفيذه من خلال إعدادهم لمشروع التخرج

‏د. نور النجار ”
الملخص
هدفت هذه الدراسة إلى الكشف عن درحة اكتساب طلبة كلية التربية بجامعة السلطان قابوس
لمهارات البحث الإحرائي» وصعوبات تنفيذه من خلال تطبيقهم لمشروع التخرج» استخدم للجمع البيانات
أداتان: الأولى معايير التقييم لمشروع التخرج المعدة من قبل كلية التربية بجامعة السلطان قابوس» وتكونت
العينة لحذه الأداة من ‎UG Wh Kee‏ التربية بيجامعة السلطان قابوس» والأداة الثانية كانت عبارة
مقابلات ‎cre Ved‏ وقد أظهرت نتائج الاستبانة ‎of‏ اكتساب طلبة ‎als‏ التربية لمهارات البحث
الإحرائي جاءت جميعها بمستوى مرتفع عدا مهارة توثيق المراجع» وعلى الرغم من وحود درحات مرتفعة
لاكتسابهم تلك المهارات إلا أن نتائج المقابلات كشفت عن عدد من الصعوبات التي واحهتهم في تنفيذ
مشروع التخرج من أهمها: تيار الموضوع؛ وصياغة الأسئلة البحثية» وتطبيق الأدوات» وتحليل البيانات»
وقلة المصادر والدراسات السابقة» وكتابة البحثء كما أظهرت النتائج عدم وحود فروق ‎ONS‏ ذلالة
إحصائية بين متوسطات الذكور والإناث في اكتساب مهارات البحث الإحرائي» ‎lay‏ أظهرت النتائج
وجود فروق ذات دلالة إحصائية ترجع لنوعية البرنامج (بكالوريوس» ودبلوم تأهيل تربوي) لصالح برنامج
دبلوم التأهيل التربوي. ‎By‏ ضوء تلك النتائج توصي الباحثتان بتدريب طلبة مؤسسات التعليم العاللي على
القيام بالبحث الإجرائي في عدد من المقررات وعدم اقتصاره على مقرر واحد ‎badd‏ وتقدهم ورش تدريبية
لمدرسي مقرر مشروع التخرج عن أفضل الممارسات التدريسية في تدريس البحث الإجرائي.
الكلمات المفتاحية: كلية التربية» البحث الإجرائي» جامعة السلطان قابوس» الصعوبات» مشروع
‎cel‏

‏* أستاذ مساعد, قسم المناهج والتدريس» كلية التربية» جامعة السلطان قابوس» عمان.

‎١
    """


# In[10]:


sample_ajsp = """
المجلة العببية ‎[pi‏

الإصدار السابع — العدد ستة وستون
تاريخ الإصدار: 2 - نيسان - 2024م

www.ajsp.net

ISSN: 2663-5798 || Arab Journal for Scientific Publishing

INTE” Gam By Few ‏سم حك ون سد بسب‎ GSD _

"المشكلات السلوكية لدى طلبة ذوي صعوبات التعلم المحددة في المدارس الاساسية داخل القدس
من وجهة نظر المعلمين"

إعداد الباحثة:

أ. نفيسة سعيدة
الجامعة العربية الأمربكية

Arab Journal for Scientific Publishing (AJSP) ISSN: 2663-5798

دتمل

الإصدار السابع — العدد ستة وستون
تاريخ الإصدار: 2 - نيسان - 2024م

www.ajsp.net

ISSN: 2663-5798 || Arab Journal for Scientific Publishing

IN! TRNAS Foe oe tty Aes ge SB ‏نود‎ CO) _ ©

الملخص:

هدفت الدراسة التعرف إلى المشكلات السلوكية ‎Gal‏ طلبة ذوي صعويات التعلم المحددة في المدارس الاساسية داخل القدس من
‎Ages‏ نظر المعلمين» والتعرف إلى دور المتغيرات الجنس» وسنوات الخبرة» والمؤهل العلمي في استجابات المعلمين نحو المشكلات
السلوكية لدى طلبة ذوي صعوبات التعلم المحددة في المدارس الاساسية داخل القدس» وقد تكون مجتمع الدراسة من جميع معلمي
المدارس الأساسية في مدينة القدس والبالغ عددهم (1761)» وتكونت عينة الدراسة من (119) معلماً ومعلمة اختيرت بالطريقة الغرضية
الهادفة» ولتحقيق أهداف الدراسة استخدمت الباحثة المنهج الوصفي بصورته التحليلية » واستخدام الاستبانة كأداة للدراسة» ويعد تحليل
النتائج باستخدام برنامج الرزم الإحصائية للعلوم الاجتماعية ‎(SPSS)‏ أظهرت النتائج أن المتوسطات الحسابية والانحرافات المعيارية
للمشكلات السلوكية لدى طلبة ذوي صعويات التعلم المحددة في المدارس الاساسية داخل القدس من ‎Ages‏ نظر المعلمين تراوحت ما
بين (3.61-2.88) إذ كانت النسبة المئوبة للاستجابة لها تتراوح ما ‎cas‏ )%57.6-%72.2(« فقد أتى المجال الأول السلوك المتعلق
بالنشاط الزائد في الترتيب الأول ويمتوسط حسابي مقداره (3.61) ونسبة مئوية )%72.2( وهي درجة كبيرة ‎Lele‏ في المرتبة الثانية
المتعلق بالسلوك العدواني ‎cla‏ المجال الرابع وبمتوسط حسابي مقداره )3.35( ونسبة مئوية )%67-0( » وقد أتى المجال الثاني السلوك
الاجتماعي المنحرف في المرتبة الثالثة ويمتوسط حسابي (3.14) وبنسبة مئوية )%62.8( ‎٠‏ في ‎Gus‏ جاء المجال الثالث والمتعلق
بالعادات الغريبة واللزمات العصبية في المرتبة الأخيرة وبمتوسط حسابي )2-88( ونسبة مئوية )%57.6( ‎Lele‏ الدرجة الكلية فقد حصلت
على متوسط حسابي )3.26( ونسبة مئوية (7665.2) وهي درجة متوسطة» ‎aly‏ تظهر فروق دالة إحصائياً في استجابات المعلمين نحو
المشكلات السلوكية لدى طلبة ذوي صعوبات التعلم المحددة في المدارس الاساسية داخل القدس تعزى لمتغيري الجنس والمؤهل العلمي»
‎Ley‏ ظهرت فروق في متغير سنوات الخدمة ولصالح أكثر من )10( سنوات وأوصت الدراسة بتفعيل دور الإرشاد التربوي في المدارس
الأساسية في مدينة القدس في تنفيذ أنشطة إرشادية من شأنها تقليل حدة النشاط الزائد لدى الطلبة من ذوي صعويات التعلم المحددة؛
وعقد دورات تدريبية للمعلمين الجدد حول مهارات التعامل مع المشكلات الصفية ومنها المشكلات السلوكية لذوي صعويات التعلم
المحددة.

الكلمات المفتاحية: المشكلات السلوكية؛ صعويات التعلم المحددة» المدارس الأساسية.

6.

المقدمه:

تعتبر صعويات التعلم المحددة مهمة في الوقت الحاضر في مجال التعليم العادي والتعليم الخاص على حد سواء»ء وتلقى اهتماما
كبيرا من مختلف مجالات العلوم سواء الطبية, النفسية» والتربودة الاجتماعية, وهذا الاهتمام طبيعى» حيث تشكل هذه المجموعة شريحة
تشمل جميع ‎OU‏ التعليم الخاص.

ونتيجة لتزايد ظهور الصعويات التعليمية المحددة ‎(cal‏ الأطفال في الآونة ‎Bud)‏ حرص بعض التريوبين والأخصائيين على ‎ESI‏
‏عن ‎Ghul‏ الكامنة وراء هذه المشاكل أو الصعوباتء؛ واكتشاف العوامل والآثار التي تؤدي بشكل مباشر أو غير مباشر إلى هذه

الصعوية. فقد مر مفهوم صعويات التعلم المحددة بتطور من ‎Gus‏ المصطلح وذلك نتيجة الجهود المستمرة في دراسته» وانتشر واستخدم
في المجالات التعليمية» وقد ظهر مصطلح صعويات التعلم المحددة نتيجة لما لاحظه اختصاصيو التوعية في الخمسينات والستينات»

Arab Journal for Scientific Publishing (AJSP) ISSN: 2663-5798   """


# In[11]:


import re
import unicodedata

def clean_text_for_llm(text: str) -> str:
    if not isinstance(text, str):
        return text

    # 1) Unicode normalization (VERY important)
    text = unicodedata.normalize("NFKC", text)

    # 2) Remove invisible / directional characters (category Cf)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")

    # 3) Remove decorative punctuation & symbols
    text = re.sub(
        r"[•●▪♦■★☆※…—–―‐-⁃⁄⁎⁑⁂⁕⁖⁗⁘⁙⁚⁛⁜⁝⁞]",
        "",
        text,
    )

    # 4) Normalize repeated punctuation
    text = re.sub(r"\.{3,}", ".", text)
    text = re.sub(r"[=]{2,}", "", text)
    text = re.sub(r"[_~^`]+", "", text)

    # 5) Normalize quotes
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[‘’]", "'", text)

    # 6) Normalize whitespace
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# In[12]:


#prompt 1 : 4-5 min
class GeneralField(str, Enum):
    ART = "Art"
    AGRICULTURAL = "Agricultural"
    ARABIC = "Arabic"
    BUSINESS = "Business"
    EDUCATION = "Education"
    Engineering = "Engineering"
    MEDICAL = "Medical"
    MUSIC = "Music"
    SCIENCE = "Science"
    SOCIAL_SCIENCE = "Social Science"
    COMPUTER_SCIENCE = "Computer Science"
    HISTORY = "History"
    PSYCHOLOGY = "Psychology"



class ArticleMetadata(BaseModel):
    # Non-optional: always filled
    title_ar: str = Field(..., description="Arabic title (extracted or translated).")
    title_en: str = Field(..., description="English title (extracted or translated).")
    abstract_ar: str = Field(..., description="Arabic abstract (extracted or translated).")
    abstract_en: str = Field(..., description="English abstract (extracted or translated).")

    # Non-optional: must be one of enum values
    general_field: GeneralField = Field(
        ...,
        description=(
            "One of: Art, Agricultural, Arabic, Business, Education, "
            "Engineering, Medical, Music, Science, Social Science, "
            "Computer Science, History , Psychology."
        ),
    )
    # Authors can be empty list if not found (still non-optional)
    authors: List[str] = Field(
        default_factory=list,
        description="List of author names (in original script, Arabic or Latin).",
    )


llm = ChatOpenAI(
    base_url="http://localhost:6000/v1",
    api_key="no-key",
    model="qwen-extractor-1",
    temperature=0,
)

parser = JsonOutputParser(pydantic_object=ArticleMetadata)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an information extraction + normalization model.

Input text is mostly Arabic with some English mixed in.

You MUST output ALL fields in the schema (no nulls, no missing keys).

Extraction rules:
1) If title_ar is present in the text, copy it exactly.
   If title_ar is NOT present but title_en is present, TRANSLATE title_en to Arabic and put it in title_ar.
   If neither title is present, GENERATE a short informative title in BOTH languages based on the text.

2) If title_en is present, copy it exactly.
   If not present but title_ar is present, TRANSLATE title_ar to English.
   If neither is present, generate both (as above).

3) For abstract_ar / abstract_en:
   - If present, copy exactly.
   - If missing in one language but present in the other, TRANSLATE.
   - If neither abstract is present, write a concise abstract (5-10 sentences) in BOTH languages based on the text.

4) authors:
   - Extract author names if explicitly present 
   - Keep names exactly as written (Arabic or Latin).
   - If not found, return [].

5) general_field:
    - Classify the article into EXACTLY ONE of the following values: Art, Agricultural, Arabic, Business, Education, Engineering, Medical, Music, Science, Social Science, Computer Science, History, Psychology.
    - Choose the closest dominant field and never invent new labels.

IMPORTANT:
- Output MUST follow the format instructions exactly.
- Return only valid JSON, no extra text.

{format_instructions}
""",
        ),
        ("human", 'Text:\n"""\n{text}\n"""'),
    ]
).partial(format_instructions=parser.get_format_instructions())

chain = prompt | llm | parser


def extract_article_metadata(text: str) -> ArticleMetadata:
    text = clean_text_for_llm(text)
    result: Dict[str, Any] = chain.invoke({"text": text})
    return ArticleMetadata(**result)



# In[13]:


#prompt 2 : 4-5 min
class GeneralField(str, Enum):
    ART = "Art"
    AGRICULTURAL = "Agricultural"
    ARABIC = "Arabic"
    BUSINESS = "Business"
    EDUCATION = "Education"
    Engineering = "Engineering"
    MEDICAL = "Medical"
    MUSIC = "Music"
    SCIENCE = "Science"
    SOCIAL_SCIENCE = "Social Science"
    COMPUTER_SCIENCE = "Computer Science"
    HISTORY = "History"
    PSYCHOLOGY = "Psychology"



class ArticleMetadata(BaseModel):
    # Non-optional: always filled
    title_ar: str = Field(..., description="Arabic title (extracted or translated).")
    title_en: str = Field(..., description="English title (extracted or translated).")
    abstract_ar: str = Field(..., description="Arabic abstract (extracted or translated).")
    abstract_en: str = Field(..., description="English abstract (extracted or translated).")

    # Non-optional: must be one of enum values
    general_field: GeneralField = Field(
        ...,
        description=(
            "One of: Art, Agricultural, Arabic, Business, Education, "
            "Engineering, Medical, Music, Science, Social Science, "
            "Computer Science, History , Psychology."
        ),
    )
    # Authors can be empty list if not found (still non-optional)
    authors: List[str] = Field(
        default_factory=list,
        description="List of author names (in original script, Arabic or Latin).",
    )


llm = ChatOpenAI(
    base_url="http://localhost:6000/v1",
    api_key="no-key",
    model="qwen-extractor-1",
    temperature=0.2,
)

parser = JsonOutputParser(pydantic_object=ArticleMetadata)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an information extraction + normalization model.
Input text is mostly Arabic with some English mixed in.
You MUST output ALL fields in the schema (no nulls, no missing keys).
IMPORTANT:
- Output MUST follow the format instructions exactly.
- Return only valid JSON, no extra text.

{format_instructions}
""",
        ),
        ("human", 'Text:\n"""\n{text}\n"""'),
    ]
).partial(format_instructions=parser.get_format_instructions())

chain = prompt | llm | parser


def extract_article_metadata(text: str) -> ArticleMetadata:
    text = clean_text_for_llm(text)
    result: Dict[str, Any] = chain.invoke({"text": text})
    return ArticleMetadata(**result)



# In[14]:


import requests

def count_tokens(text: str) -> int:
    resp = requests.post(
        "http://localhost:6000/tokenize",
        json={"content": text},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return len(data["tokens"])

print ("basic prompt token counting:" ,    count_tokens(prompt.format_prompt(text="").to_string())  )


# In[15]:


# Example
raw_text = sample  # Replace with your actual text
clean_text = clean_text_for_llm(raw_text)
messages = prompt.format_messages(text=clean_text)
full_prompt_cleaned = "\n\n".join(m.content for m in messages)
full_tokens = count_tokens(full_prompt_cleaned)
print("Prompt count_cleaned:", full_tokens)


raw_text = sample  # Replace with your actual text
messages = prompt.format_messages(text=raw_text)
full_prompt = "\n\n".join(m.content for m in messages)
full_tokens_not_cleaned = count_tokens(full_prompt)
print("Prompt count_uncleaned:", full_tokens_not_cleaned)

print ("Difference in tokens due to cleaning:", full_tokens_not_cleaned - full_tokens)



# # pinpointing sections
# 

# In[16]:


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




# In[17]:


import re
from typing import List, Optional, Tuple

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


# In[18]:


#ajsp optimized pinpointer test
import re
from typing import List, Pattern, Optional

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


# In[19]:


# AJSRP pinpointer + cleaning
import re
from typing import List, Pattern, Optional


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


# In[20]:


def AJP_pinpoint(page1: str, page2: str) -> str:
    return AJP_pinpoint_imp(page1, page2)

def AJSP_pinpoint(page1: str, page2: str) -> str:

    return AJSP_pinpoint_imp(page1, page2)

def ajsrp_pinpoint(page1: str, page2: str) -> str:
    # page 2 is unnecessary for AJSRP
    return AJSRP_pinpoint_imp(page1, "")

def AM_pinpoint(page1: str, page2: str) -> str:
    # TODO: tailor to AM tendencies
    return default_pinpoint(page1, page2)

def ARPD_pinpoint(page1: str, page2: str) -> str:
    # TODO: tailor to ARPD tendencies
    return default_pinpoint(page1, page2)


# =========================
# Dispatcher: pinpoint()
# =========================

_PINPOINTERS: Dict[str, Callable[[str, str], str]] = {
    "AJP": AJP_pinpoint,
    "AJSP": AJSP_pinpoint,
    "ajsrp": ajsrp_pinpoint,
    "AM": AM_pinpoint,
    "ARPD": ARPD_pinpoint,
}

def pinpoint(page1: str, page2: str, source: str) -> str:
    """
    Main entry point.
    Routes to a source-specific pinpointer based on `source`.
    If source is unknown, uses default_pinpoint.
    """
    src = (source or "").strip()
    fn = _PINPOINTERS.get(src, None)
    if fn is None:
        return None
    return fn(page1, page2)


# In[7]:


df_am = df[df["source"] == "ARPD"]
print ()
print (df_am.loc[df_am.index[2], "page1"])
print(df_am.loc[df_am.index[2], "page2"])


# In[21]:


print (count_tokens(AJSP_pinpoint_imp(sample_ajsp, "")))
print (count_tokens(sample_ajsp))


# # executing final output

# In[51]:


meta = extract_article_metadata(AJP_pinpoint_imp(sample_ajsp, ""))
print(json.dumps(meta.model_dump(), ensure_ascii=False, indent=2))



# In[ ]:





# In[ ]:




