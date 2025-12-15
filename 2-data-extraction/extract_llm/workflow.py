import pandas as pd
from llm_call import extract_article_metadata , ArticleMetadata
from pinpoint_dispatcher import pinpoint
import pandas as pd
from pathlib import Path
#================================================================


"""
Below is a deterministic workflow loop that:

    -iterate each row

    -call pinpoint(page1, page2, source)

    -send the returned text to extract_article_metadata()

    -get back an ArticleMetadata

    -only fill columns that are currently missing (skip if already filled)

    -save back to CSV


"""
import json
from pathlib import Path
import pandas as pd

from llm_call import extract_article_metadata
from pinpoint_dispatcher import pinpoint


# ==========================================================
# Paths
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent
SRC_CSV = BASE_DIR / "02-extracted-pages-with-tokens.csv"
OUT_CSV = BASE_DIR / "03-extracted-pages-with-tokens.filled.csv"


# ==========================================================
# Helpers
# ==========================================================
def _is_missing(x) -> bool:
    """
    Correct missing detector:
    - None
    - NaN
    - <NA> (pandas string dtype)
    - empty string
    """
    if pd.isna(x):
        return True
    if isinstance(x, str) and x.strip() == "":
        return True
    return False

def _short(v, max_len=30):
    if v is None or pd.isna(v):
        return v
    s = str(v)
    return s if len(s) <= max_len else s[:max_len] + "…"

TEXT_COLS = [
    "title",
    "title_en",
    "abstract_ar",
    "abstract_en",
    "authors",
    "authors_en",
    "general_field",
    "field",
    "publish_date",
    "source",
]


def load_or_create_out(df_src: pd.DataFrame) -> pd.DataFrame:
    """
    Load output CSV if it exists, otherwise create a new one
    with the same schema and correct dtypes.
    """
    if OUT_CSV.exists():
        print(f"[INFO] Loading existing output CSV: {OUT_CSV}")
        df_out = pd.read_csv(OUT_CSV)
    else:
        print("[INFO] Output CSV not found → creating new one")
        df_out = pd.DataFrame(columns=df_src.columns)

    # Ensure identical columns & order
    for col in df_src.columns:
        if col not in df_out.columns:
            df_out[col] = pd.NA
    df_out = df_out[df_src.columns]

    # Force string dtype for text columns
    for c in TEXT_COLS:
        if c in df_out.columns:
            df_out[c] = df_out[c].astype("string")

    return df_out


def already_processed(df_out: pd.DataFrame, article_id) -> bool:
    if "article_id" not in df_out.columns:
        return False
    if _is_missing(article_id):
        return False
    return (df_out["article_id"] == article_id).any()


# ==========================================================
# Main
# ==========================================================
def main():
    print("[INFO] Starting workflow")

    # ---------- Load source ----------
    print(f"[INFO] Loading source CSV: {SRC_CSV}")
    df_src = pd.read_csv(SRC_CSV)

    # Force string dtype in source
    for c in TEXT_COLS:
        if c in df_src.columns:
            df_src[c] = df_src[c].astype("string")

    df_out = load_or_create_out(df_src)

    TARGET_COLS = [
        "title",
        "title_en",
        "abstract_ar",
        "abstract_en",
        "general_field",
        "authors",
    ]

    # ---------- TEST MODE: first row only !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!        ----------
    for i, row in df_src.head(1).iterrows():
        article_id = row.get("article_id")
        print("\n" + "=" * 70)
        print(f"[ROW] Processing index={i} | article_id={article_id}")

        if already_processed(df_out, article_id):
            print("[SKIP] Article already processed → skipping")
            continue

        out_row = row.copy()

        # ---------- Missing analysis ----------
        print("[CHECK] Field completeness:")
        needs_llm = False
        for col in TARGET_COLS:
            missing = _is_missing(out_row.get(col))
            print(f"   - {col:12} → {repr(_short(out_row.get(col)))} | missing={missing}")
            if missing:
                needs_llm = True

        print(f"[DECISION] needs_llm = {needs_llm}")

        # ---------- Pinpoint ----------
        if needs_llm:
            source = out_row.get("source")
            page1 = out_row.get("page1", "") or ""
            page2 = out_row.get("page2", "") or ""

            print(f"[PINPOINT] source={repr(source)}")
            pinned = pinpoint(page1=page1, page2=page2, source=source)

            if not pinned:
                print("[WARN] Pinpointer returned None → appending raw row")
            else:
                print(f"[PINPOINT] Extracted text length = {len(pinned)}")
                print("[LLM] Calling LLM… this may take a while")

                meta = extract_article_metadata(pinned)
                print("[LLM] LLM returned metadata")

                # ---------- Fill fields ----------
                if _is_missing(out_row.get("title")):
                    out_row["title"] = meta.title_ar
                if _is_missing(out_row.get("title_en")):
                    out_row["title_en"] = meta.title_en

                if _is_missing(out_row.get("abstract_ar")):
                    out_row["abstract_ar"] = meta.abstract_ar
                if _is_missing(out_row.get("abstract_en")):
                    out_row["abstract_en"] = meta.abstract_en

                if _is_missing(out_row.get("general_field")):
                    out_row["general_field"] = getattr(
                        meta.general_field, "value", meta.general_field
                    )

                if _is_missing(out_row.get("authors")):
                    out_row["authors"] = json.dumps(
                        meta.authors, ensure_ascii=False
                    )

                print("[FILL] Missing fields filled from LLM")

        # ---------- Append + checkpoint ----------
        df_out = pd.concat(
            [df_out, out_row.to_frame().T],
            ignore_index=True
        )
        df_out.to_csv(OUT_CSV, index=False)
        print(f"[SAVE] Row appended → checkpoint written to {OUT_CSV}")

    print("\n[INFO] Workflow finished successfully")


if __name__ == "__main__":
    main()
