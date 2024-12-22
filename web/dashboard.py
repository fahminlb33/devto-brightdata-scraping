import pandas as pd
import streamlit as st
import plotly.express as px

from babel.numbers import format_currency
from extras import load_remote_products


@st.cache_data
def load_data():
    return load_remote_products()


def show_dashboard(df: pd.DataFrame, exclude_outliers=False):
    # exclude outliers using IQR method
    if exclude_outliers:
        q1 = df["price"].quantile(0.25)
        q3 = df["price"].quantile(0.75)

        iqr = q3 - q1
        fence_low = q1 - 1.5 * iqr
        fence_high = q3 + 1.5 * iqr

        df = df.loc[(df["price"] > fence_low) & (df["price"] < fence_high)]

    # calculate means
    price_mean = df["price"].mean()
    price_median = df["price"].median()

    # section: key metrics
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        st.metric(label="Data samples", value=df.shape[0])

    with col2:
        st.metric(
            label="Mean price",
            value=format_currency(price_mean, "IDR", locale="en_US"),
        )

    with col3:
        st.metric(
            label="Median price",
            value=format_currency(price_median, "IDR", locale="en_US"),
        )

    # price histogram
    fig_price = px.histogram(df, x="price", marginal="box", title="Price Distribution")
    fig_price.update_layout(barmode="overlay")
    fig_price.update_traces(opacity=0.75)
    st.plotly_chart(fig_price, key="histogram_price")

    # brand popularity
    df_brand = df["brand"].value_counts().sort_values(ascending=False).reset_index()
    fig_brand = px.bar(
        df_brand, x="brand", y="count", text_auto=True, title="Brand Popularity"
    )
    st.plotly_chart(fig_brand, key="brand")

    # GPU popularity
    df_gpu = (
        df["graphics_card"].value_counts().sort_values(ascending=False).reset_index()
    )
    fig_gpu = px.bar(
        df_gpu, x="graphics_card", y="count", text_auto=True, title="GPU Popularity"
    )
    st.plotly_chart(fig_gpu, key="graphics_card")

    # total storage and type
    col1, col2 = st.columns([2, 1], gap="medium")

    with col1:
        df_storage = (
            df["storage_gb"].value_counts().sort_values(ascending=False).reset_index()
        )
        fig_storage = px.pie(
            df_storage, names="storage_gb", values="count", title="Storage"
        )
        st.plotly_chart(fig_storage, key="storage")

    with col2:
        df_storage_type = (
            df["storage_type"].value_counts().sort_values(ascending=False).reset_index()
        )
        fig_storage_type = px.pie(
            df_storage_type, names="storage_type", values="count", title="Storage Type"
        )
        fig_storage_type.update_layout(
            legend=dict(orientation="h", yanchor="bottom", xanchor="right", y=-0.1, x=1)
        )
        st.plotly_chart(fig_storage_type, key="storage_type")


def main():
    st.title("📈 Dashboard")

    df = load_data()

    # optional filters
    col1, col2 = st.columns(2)

    # filter by marketplace
    with col1:
        marketplace = st.selectbox(
            "Select marketplace",
            df["source"].unique(),
            index=None,
            placeholder="Select marketplace...",
        )

    # filter outliers
    with col2:
        st.text("")
        st.text("")
        exclude_outliers = st.checkbox("Exclude outliers?")

    # show dashboard
    if marketplace is not None:
        st.subheader(f"Marketplace: {marketplace}")
        show_dashboard(df[df["source"] == marketplace], exclude_outliers)
    else:
        st.subheader("Marketplace: All")
        show_dashboard(df, exclude_outliers)


# bootstrap
main()
