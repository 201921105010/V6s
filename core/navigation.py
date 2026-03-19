import streamlit as st


def go_page(name):
    st.session_state.page = name


def go_home():
    st.session_state.page = 'home'
