import pandas as pd
import streamlit as st


# Cacheado: o CSV é lido uma vez só, e não a cada interação com os widgets
@st.cache_data(max_entries=1)
def load_data(path="data/clean/dataset.csv"):
    """Lê o dataset já tratado (exportado ao final do notebook de EDA)."""
    return pd.read_csv(path)
