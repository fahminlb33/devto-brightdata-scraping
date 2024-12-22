import nltk
import streamlit as st

# --- initialize Streamlit app
pg = st.navigation(
    [
        st.Page("dashboard.py", title="Dashboard", icon=":material/home:"),
        st.Page("keywords.py", title="Keyword Explorer", icon=":material/search:"),
        st.Page("cluster.py", title="Product Cloud", icon=":material/cloud:"),
        st.Page(
            "compare_price.py", title="Compare Price", icon=":material/attach_money:"
        ),
    ]
)

st.set_page_config(page_title="Bright Data Hackathon")

# --- download NLTK data
if "app_init" not in st.session_state or not st.session_state["app_init"]:
    nltk.download(["punkt"])
    st.session_state["app_init"] = True

# bootstrap
pg.run()
