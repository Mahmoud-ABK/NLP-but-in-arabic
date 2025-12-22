# --- Step 1: Import necessary libraries ---
# pip install Tashaphyne
from tashaphyne.stemming import ArabicLightStemmer

# For stopwords (as mentioned before)
# pip install arabic-stopwords
import arabicstopwords.arabicstopwords as stp



# --- Step 4: Create the 'text_for_tfidf' column with custom processing ---

# Initialize the light stemmer
stemmer = ArabicLightStemmer()

def stem_text(text):
    """Applies light stemming to a string of text."""
    words = text.split()
    # Use the light_stem method from Tashaphyne
    stemmed_words = [stemmer.light_stem(word) for word in words]
    return ' '.join(stemmed_words)

def remove_stopwords(text):
    """Removes Arabic stopwords from a string of text."""
    words = text.split()
    filtered_words = [word for word in words if not stp.is_stop(word)]
    return ' '.join(filtered_words)
