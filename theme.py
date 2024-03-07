import streamlit as st

def set_theme():
  
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #000000;
            color: #d6ff4b;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
            color: #d6ff4b;
        }
        .stButton button {
            background-color: #055483;
            color: #d6ff4b;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )