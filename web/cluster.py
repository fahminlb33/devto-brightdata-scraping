from textwrap import wrap

import pandas as pd
import streamlit as st
import plotly.express as px

from sklearn.cluster import KMeans
from extras import load_remote_embeddings


@st.cache_data
def cluster(cluster_size: int) -> pd.DataFrame:
    df = load_remote_embeddings()

    # perform k-means clustering
    kmeans = KMeans(
        n_clusters=cluster_size,
    )
    kmeans.fit(df[["d1", "d2", "d3"]].values)

    # set clusters
    df["cluster"] = kmeans.labels_

    # break long product name into new line in Plotly
    df["product_name_wrap"] = df["product_name"].apply(
        lambda x: "<br>".join(wrap(x, width=30))
    )

    return df


def main():
    st.title("☁️ Product Cloud")

    # cluster size input and cluster the data
    cluster_size = st.slider("Number of clusters", 2, 100, 20, 1)
    df_cluster = cluster(cluster_size)

    # 3D cluster cloud
    fig_cluster = px.scatter_3d(
        df_cluster,
        x="d1",
        y="d2",
        z="d3",
        color="cluster",
        hover_data=["product_name_wrap"],
    )
    fig_cluster.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=600)
    st.plotly_chart(fig_cluster, key="cluster", use_container_width=True, theme=None)
    st.text("")
    st.text("")

    # cluster selector
    sel_cluster = st.slider(
        "Select cluster",
        df_cluster["cluster"].min(),
        df_cluster["cluster"].max(),
        value=df_cluster["cluster"].min(),
        step=1,
    )

    # product by cluster table
    show_cols = ["product_name", "source"]
    sel_cluster_data = df_cluster[df_cluster["cluster"] == sel_cluster][show_cols]

    st.subheader("Products by Cluster")
    st.dataframe(
        sel_cluster_data,
        use_container_width=True,
        column_config={
            "product_name": st.column_config.TextColumn("Product Name"),
            "source": st.column_config.TextColumn("Source"),
        },
    )


# bootstrap
main()
