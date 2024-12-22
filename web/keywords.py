import itertools

import nltk
import pandas as pd
import streamlit as st
import plotly.express as px

from extras import load_remote_products, clean_tokenize


@st.cache_data
def load_data():
    return load_remote_products()


@st.cache_data
def get_ngram_frame(n_gram=2, subset=None):
    df = load_data()

    # filter by marketplace
    if subset is not None:
        df = df[df["source"] == subset]

    # extract n-grams
    product_name_corpus = itertools.chain(
        *[clean_tokenize(x) for x in df["product_name"].tolist()]
    )
    product_name_grams = list(nltk.ngrams(product_name_corpus, n_gram))

    # calculate token frequencies
    fdist = nltk.FreqDist(product_name_grams)
    gram_df = pd.DataFrame(
        {
            "gram": [" ".join(x) for x in fdist.keys()],
            "freq": [x for x in fdist.values()],
        }
    )

    gram_df["freq_pct"] = (gram_df["freq"] / gram_df["freq"].sum()) * 100

    return gram_df.sort_values("freq", ascending=False)


def main():
    st.title("🔍 Keyword Explorer")

    # optional filters
    col1, col2 = st.columns(2)

    # filter by marketplace
    with col1:
        marketplace = st.selectbox(
            "Select marketplace",
            ["LKPP", "Tokopedia", "Lazada"],
            index=None,
            placeholder="Select marketplace...",
        )

    # n-gram value
    with col2:
        ngram = st.slider(label="N-gram", min_value=1, max_value=5, value=2, step=1)

    # calculate n-gram
    df_gram = get_ngram_frame(ngram, marketplace)

    # top 20 n-gram frequency
    fig_ngram = px.bar(df_gram.nlargest(20, "freq"), x="freq", y="gram")
    fig_ngram.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=600)

    st.subheader("Top 20 N-Gram Frequency")
    st.plotly_chart(fig_ngram, key="ngram", use_container_width=True)

    # n-gram frequencies in table
    st.subheader("N-Gram Frequencies")
    st.dataframe(
        df_gram,
        use_container_width=True,
        column_config={
            "gram": st.column_config.TextColumn("Token"),
            "freq": st.column_config.NumberColumn("Frequency"),
            "freq_pct": st.column_config.NumberColumn(
                "Frequency (%)",
                min_value=0,
                max_value=100,
                format="%.5f%%",
            ),
        },
    )


# bootstrap
main()
