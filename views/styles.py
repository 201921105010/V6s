import streamlit as st
from config import GLOBAL_CSS


def configure_page():
    st.set_page_config(page_title="成品整机管理系统 V7.0 Pro", layout="wide", page_icon="🏭")


def apply_global_styles():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
