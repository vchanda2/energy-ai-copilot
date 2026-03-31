import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.title("Energy AI Copilot 🚀")
st.write("Upload an Excel file to begin analysis")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])


def parse_task1_sheet(uploaded_file, sheet_name):
    # Read the raw sheet without headers to find the data section
    raw_df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)

    data_row_idx = None
    for i in range(len(raw_df)):
        row_text = " ".join(
            raw_df.iloc[i].astype(str).tolist()
        )  # Convert row to string for searching
        if "Data:" in row_text:
            data_row_idx = i
            break

    if data_row_idx is None:
        return None, None

    header_row_idx = data_row_idx + 1
    value_start_row = data_row_idx + 2

    headers = raw_df.iloc[
        header_row_idx
    ].tolist()  # Extract headers from the identified header row
    data_df = raw_df.iloc[
        value_start_row:
    ].copy()  # Extract data starting from the row after headers
    data_df.columns = headers  # Set the correct column names

    # Keep only useful columns
    # data_df = data_df[["Date & Time", "Motor Amps"]].copy() # Manual specification of columns
    time_col, amp_col = detect_columns(data_df)  # Auto-detect columns based on keywords
    if time_col is None or amp_col is None:
        st.error("Could not detect required columns.")
        st.stop()  # Stop execution if required columns are not found

    data_df = data_df[[time_col, amp_col]].copy()  # Keep only the detected columns
    data_df.columns = ["Date & Time", "Motor Amps"]  # Standardize column

    # sort by time
    data_df = data_df.sort_values(by="Date & Time").reset_index(
        drop=True
    )  # Sort data by time to ensure chronological order and reset index after sorting with drop=True to avoid adding the old index as a column

    # Clean types
    data_df["Date & Time"] = pd.to_datetime(
        data_df["Date & Time"], errors="coerce"
    )  # Convert to datetime, coercing errors to NaT
    data_df["Motor Amps"] = pd.to_numeric(data_df["Motor Amps"], errors="coerce")

    # Drop bad rows
    data_df = data_df.dropna(subset=["Date & Time", "Motor Amps"]).reset_index(
        drop=True
    )

    return raw_df, data_df


# Add function for auto detection of timestamp and amp columns instead of hardcoding
def detect_columns(df):
    time_col = None
    amp_col = None

    for col in df.columns:
        col_lower = str(col).lower()
        if "time" in col_lower or "date" in col_lower:
            time_col = col
        if "amp" in col_lower or "current" in col_lower:
            amp_col = col
    return time_col, amp_col


if uploaded_file:  #  If a file is uploaded, process it
    xls = pd.ExcelFile(uploaded_file)  #

    st.subheader("Sheets in file")
    st.write(xls.sheet_names)

    selected_sheet = st.selectbox(
        "Select a sheet", xls.sheet_names
    )  # Allow user to select a sheet from the uploaded file

    if selected_sheet == "Task 1 - Data Analysis":
        raw_df, cleaned_df = parse_task1_sheet(uploaded_file, selected_sheet)

        # data validation
        st.subheader("Data Validation")
        st.write("Total rows:", len(cleaned_df))
        st.write("Missing values:", cleaned_df.isnull().sum().to_dict())

        st.write("Time sorted:", cleaned_df["Date & Time"].is_monotonic_increasing)

        st.write(
            "Motor Amps range:",
            cleaned_df["Motor Amps"].min(),
            "to",
            cleaned_df["Motor Amps"].max(),
        )

        st.subheader("Parsed Task 1 Data")
        st.dataframe(cleaned_df.head(10))

        st.subheader("Columns")
        st.write(cleaned_df.columns.tolist())

        st.subheader("Shape")
        st.write({"rows": cleaned_df.shape[0], "columns": cleaned_df.shape[1]})

        st.subheader("Basic Stats")
        st.write(cleaned_df["Motor Amps"].describe())

        st.subheader("Motor Amps vs Time")

        fig, ax = plt.subplots()
        ax.plot(cleaned_df["Date & Time"], cleaned_df["Motor Amps"])

        ax.set_xlabel("Time")
        ax.set_ylabel("Motor Amps")

        ax.set_title("Motor Amps Over Time")

        plt.xticks(rotation=45)

        st.pyplot(fig)  # Display the plot in Streamlit
    else:
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        st.subheader("Preview")
        st.dataframe(df.head(10))
