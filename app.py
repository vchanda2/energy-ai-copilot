import streamlit as st
import pandas as pd

st.title("Cascade AI Copilot 🚀")

st.write("Upload an Excel file to begin analysis")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    st.subheader("Sheets in file:")
    st.write(xls.sheet_names)

print("hello")
