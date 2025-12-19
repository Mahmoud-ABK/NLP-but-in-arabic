from enum import Enum
from typing import List, Any, Dict

from pydantic import BaseModel, Field
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


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

from typing import Dict, Any
from pydantic import ValidationError

REQUIRED_KEYS = {
    "title_ar": "",
    "title_en": "",
    "abstract_ar": "",
    "abstract_en": "",
    "general_field": "Education",  # safe default, change if you want
    "authors": [],
}

def _normalize_result(raw: Any) -> Dict[str, Any]:
    """
    Normalize LLM output into a complete, safe dict.
    """
    if not isinstance(raw, dict):
        raw = {}

    out: Dict[str, Any] = {}

    for key, default in REQUIRED_KEYS.items():
        val = raw.get(key, default)

        # null / missing
        if val is None:
            val = default

        # type enforcement
        if key == "authors":
            if not isinstance(val, list):
                val = []
            else:
                # ensure list[str]
                val = [str(x).strip() for x in val if str(x).strip()]

        elif key == "general_field":
            if not isinstance(val, str) or not val.strip():
                val = default
            else:
                val = val.strip()

        else:
            # string fields
            if not isinstance(val, str):
                val = ""
            val = val.strip()

        out[key] = val

    return out

def extract_article_metadata(text: str) -> ArticleMetadata:
    try:
        raw = chain.invoke({"text": text})
    except Exception:
        raw = {}

    normalized = _normalize_result(raw)

    try:
        return ArticleMetadata(**normalized)
    except ValidationError as e:
        # Absolute last-resort fallback (should be rare)
        safe = {k: v for k, v in REQUIRED_KEYS.items()}
        return ArticleMetadata(**safe)

