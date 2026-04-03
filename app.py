import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import math

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

        # Add user inputs
        st.subheader("Engineering Assumptions")

        col1, col2, col3 = st.columns(3)
        with col1:
            voltage = st.number_input(
                "Voltage (V)", min_value=0.0, max_value=10000.0, value=480.0, step=0.1
            )
        with col2:
            power_factor = st.number_input(
                "Power Factor", min_value=0.0, max_value=1.0, value=0.85, step=0.01
            )
        with col3:
            efficiency = st.number_input(
                "Motor Efficiency)", min_value=0.1, max_value=1.0, value=0.9, step=0.01
            )

        # Compute key metrics for current
        st.subheader("Key Metrics")
        max_amps = cleaned_df["Motor Amps"].max()
        avg_amps = cleaned_df["Motor Amps"].mean()
        row_for_max_amps = cleaned_df.loc[cleaned_df["Motor Amps"].idxmax()]
        time_of_max_amps = row_for_max_amps["Date & Time"]
        st.write(f"Max Motor Amps: {max_amps:.2f}")
        st.write(f"Average Motor Amps: {avg_amps:.2f}")
        st.write(f"Time of Max Load: {time_of_max_amps}")

        # Compute key power and energy metrics
        peak_kw = math.sqrt(3) * voltage * max_amps * power_factor * efficiency / 1000
        avg_kw = math.sqrt(3) * voltage * avg_amps * power_factor * efficiency / 1000

        amps_threshold = 1.0

        total_time_in_dataset = (
            cleaned_df["Date & Time"].max() - cleaned_df["Date & Time"].min()
        ).total_seconds() / 3600  # compute dataset time span in hours

        # compute mediam time step per sample
        time_diff_hours = cleaned_df["Date & Time"].diff().dt.total_seconds() / 3600
        median_step_hours = time_diff_hours.median()

        # compute running hours in dataset based on amps threshold
        running_mask = cleaned_df["Motor Amps"] > amps_threshold
        running_hours = (
            running_mask.sum() * median_step_hours
        )  # estimate running hours based on count of samples above threshold and median time step between samples

        # Fraction of time in hours motor is on within the dataset
        fraction_time_on = running_hours / total_time_in_dataset

        # Estimated annual operating hours
        estimated_annual_hours = fraction_time_on * 24 * 365

        # Estimated annual energy consumption in kWh
        estimated_annual_kwh = avg_kw * estimated_annual_hours

        st.subheader("Estimated Power & Energy Metrics")
        st.write(f"Estimated Peak Power: {peak_kw:.2f} kW")
        st.write(f"Estimated Average Power: {avg_kw:.2f} kW")
        st.write(
            f"Estimated Annual Operating Hours: {estimated_annual_hours:.2f} hours"
        )
        st.write(f"Estimated Annual Energy Consumption: {estimated_annual_kwh:.2f} kWh")

        # Add assumptions
        st.subheader("Assumptions Made")

        st.write(
            "Power and energy are estimated using a simplified 3 phase motor power formula. "
            "The calculation assumes the motor operates at the user-input voltage, power factor, and efficiency. "
            " Motor is considered 'on' when amps exceed a threshold of 1 amp.\n "
            " Median time step between samples is used to estimate running hours from the count of samples above the threshold."
        )

        # Plot amps over time and highlight max point
        st.subheader("Motor Amps vs Time")
        fig, ax = plt.subplots()
        ax.plot(cleaned_df["Date & Time"], cleaned_df["Motor Amps"])
        ax.scatter(time_of_max_amps, max_amps, color="red", label="Peak")
        ax.set_xlabel("Time")
        ax.set_ylabel("Motor Amps")
        ax.set_title("Motor Amps Over Time")
        ax.legend()
        plt.xticks(rotation=45)
        st.pyplot(fig)  # Display the plot in Streamlit

        # Interpretation
        st.subheader("Quick Insight")
        st.write(
            f"The motor reaches a peak load of {max_amps:.2f} at {time_of_max_amps}. "
            f"The average operating load is {avg_amps:.2f} amps."
        )

        # Archived data preview and stats
        # st.subheader("Parsed Task 1 Data")
        # st.dataframe(cleaned_df.head(10))

        # st.subheader("Columns")
        # st.write(cleaned_df.columns.tolist())

        # st.subheader("Shape")
        # st.write({"rows": cleaned_df.shape[0], "columns": cleaned_df.shape[1]})

        # st.subheader("Basic Stats")
        # st.write(cleaned_df["Motor Amps"].describe())

    else:
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        st.subheader("Preview")
        st.dataframe(df.head(10))
