import pandas as pd
import streamlit as st

st.title("Cascade AI Copilot 🚀")

st.write("Upload an Excel file to begin analysis")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    st.subheader("Sheets in file:")
    st.write(xls.sheet_names)
    selected_sheet = st.selectbox("Select a sheet to analyze", xls.sheet_names)

    df = pd.read_excel(xls, sheet_name=selected_sheet)

    st.subheader("Preview of selected sheet:")
    st.dataframe(df.head(10))

print("hello")
