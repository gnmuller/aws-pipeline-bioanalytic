import streamlit as st
import pandas as pd
import io

from data.make_synth_data import FIELDNAMES


def validate_input_columns(df: pd.DataFrame, expected: list[str]) -> tuple[bool, str | None]:
    actual = list(df.columns)
    missing = [c for c in expected if c not in actual]
    extra = [c for c in actual if c not in expected]
    if len(actual) != len(expected) or missing or extra:
        parts = []
        if len(actual) != len(expected):
            parts.append(f"Expected {len(expected)} columns, got {len(actual)}.")
        if missing:
            parts.append(f"Missing: {', '.join(missing)}.")
        if extra:
            parts.append(f"Unexpected: {', '.join(extra)}.")
        return False, " ".join(parts)
    return True, None


# Set up the page
st.set_page_config(page_title="Bioanalytical Data Handler", layout="centered")

st.title("Bioanalytical Data Handler")
st.write("Upload a CSV file, we'll process it with our database, and give you an Excel file back.")

# File upload box
uploaded_file = st.file_uploader("Pick a CSV file", type="csv")

if uploaded_file is not None:
    df_input = pd.read_csv(uploaded_file)
    columns_ok, columns_error = validate_input_columns(df_input, FIELDNAMES)

    if not columns_ok:
        st.error(f"CSV columns do not match the database schema. {columns_error}")
    else:
        st.write("**File preview:**")
        st.dataframe(df_input.head())

        if st.button("Process this file"):
            st.write("🔄 Running your data through the system...")

            # THIS IS WHERE YOUR PROCESSING WORK GOES
            # For now, we'll just keep the data and add a made-up field

            df_output = df_input.copy()
            df_output["was_processed"] = True

            output_buffer = io.BytesIO()
            df_output.to_excel(output_buffer, index=False, sheet_name="Results")
            output_buffer.seek(0)

            st.download_button(
                label="📥 Download your Excel file",
                data=output_buffer.getvalue(),
                file_name="output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.success("Done! Your file is ready.")
