import re
from textwrap import dedent

import pandas as pd
import streamlit as st
import plotly.express as px

from scipy import stats
from babel.numbers import format_currency
from extras import load_remote_products


@st.cache_data
def load_data():
    return load_remote_products()


def compare_price_ratio(df):
    # get prices from LKPP marketplace as baseline
    lkpp_prices = df[df["source"] == "LKPP"]["price"]

    # to show the metric widget
    def price_ratio(label: str, prices: pd.Series):
        if len(prices) > 0:
            ratio = lkpp_prices.mean() / prices.mean()
            st.metric(
                label,
                ratio.round(2),
                delta=format_currency(prices.mean(), "IDR", locale="en_US"),
                delta_color="off",
            )
        else:
            st.metric(
                label,
                "No data",
                delta_color="off",
            )

    # metric sections
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.metric(
            "Average LKPP price",
            format_currency(lkpp_prices.mean(), "IDR", locale="en_US"),
        )

    with col2:
        tokped_prices = df[df["source"] == "Tokopedia"]["price"]
        price_ratio("Price ratio (Tokopedia)", tokped_prices)

    with col3:
        lazada_prices = df[df["source"] == "Lazada"]["price"]
        price_ratio("Price ratio (Lazada)", lazada_prices)


def compare_stats(df: pd.DataFrame):
    # get prices from LKPP marketplace as baseline
    lkpp_prices = df[df["source"] == "LKPP"]["price"]
    lkpp_mean = lkpp_prices.mean()

    # to print t-test result
    def ttest_result(prices: pd.Series):
        if len(prices) > 0:
            mean_price = prices.mean()
            ttest_res = stats.ttest_ind(prices, lkpp_prices)

            significance = (
                "there was a " if ttest_res.pvalue < 0.05 else "there was no "
            )
            ttest_paragraph = dedent(f"""
            There are {len(prices)} products and the average price is {format_currency(mean_price, 'IDR', locale='en_US')}.
            Compared to the average price in LKPP with {len(lkpp_prices)} products and an average price of {format_currency(lkpp_mean, 'IDR', locale='en_US')},
            {significance} statistically significant (p-value=**{ttest_res.pvalue:.4f}**) difference between the LKPP and this marketplace average price.
            """)

            st.markdown(ttest_paragraph)
        else:
            st.markdown("No data.")

    # T-test result by marketplace
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tokopedia")
        tokped_prices = df[df["source"] == "Tokopedia"]["price"]
        ttest_result(tokped_prices)

    with col2:
        st.subheader("Lazada")
        lazada_prices = df[df["source"] == "Lazada"]["price"]
        ttest_result(lazada_prices)


def main():
    st.title("💸 Compare Price")

    df = load_data()

    # search bar
    search_product_name = st.text_input("Product name (regex)")
    st.markdown("")
    st.markdown("")

    # subset data
    subset_df = df[
        df["product_name"].str.contains(
            search_product_name, regex=True, flags=re.IGNORECASE
        )
    ]

    # price ratio key stats
    compare_price_ratio(subset_df)
    st.markdown("")

    # statistical test
    compare_stats(subset_df)

    # price histogram
    fig_price = px.histogram(subset_df, x="price", color="source", marginal="box")
    fig_price.update_layout(barmode="overlay")
    fig_price.update_traces(opacity=0.75)

    st.subheader("Price Histogram")
    st.plotly_chart(fig_price, key="histogram_compare")

    # show filtered data table
    st.subheader("Matched Data")
    st.dataframe(subset_df)


# bootstrap
main()
