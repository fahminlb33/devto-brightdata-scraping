import string

import nltk
import pandas as pd

USER_AGENT = "Mozilla/5.0"
FILE_URLS = {
    "products": "https://blob.kodesiana.com/kodesiana-public-assets/devto/bright-data-web-scraping-hackathon-2024/combined.jsonl",
    "embeddings": "https://blob.kodesiana.com/kodesiana-public-assets/devto/bright-data-web-scraping-hackathon-2024/embedding_small.jsonl",
}


def load_remote_products():
    return pd.read_json(
        FILE_URLS["products"], lines=True, storage_options={"User-Agent": USER_AGENT}
    )


def load_remote_embeddings():
    return pd.read_json(
        FILE_URLS["embeddings"],
        lines=True,
        storage_options={"User-Agent": USER_AGENT},
    )


def clean_tokenize(s: str):
    # case folding
    text = s.lower()

    # punctuation removal
    translator = str.maketrans("", "", string.punctuation)
    text = text.translate(translator)

    # tokenization
    return nltk.tokenize.word_tokenize(text)
