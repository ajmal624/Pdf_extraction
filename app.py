import streamlit as st
import pdfplumber
import pandas as pd

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App (Dynamic Fields)")

uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        pdf_text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"

        pdf_data = {}

        for line in pdf_text.splitlines():
            line = line.strip()
            if ":" not in line:
                continue  # skip lines without ":"

            # Handle combined "File ID ... Due Date: ..."
            if "Due Date:" in line and "File ID" in line:
                parts = line.split("Due Date:")
                pdf_data["File ID"] = parts[0].replace("File ID", "").strip()
                pdf_data["Due Date"] = parts[1].strip()
                continue

            # Only split on the first ":" to avoid extra columns
            if ":" in line:
                field, value = line.split(":", 1)
                field = field.strip()
                value = value.strip()
                # Make sure field is not empty
                if field:
                    pdf_data[field] = value

        pdf_data["Filename"] = uploaded_file.name
        all_data.append(pdf_data)

    # Create DataFrame
    df = pd.DataFrame(all_data)

    # Optional: remove empty columns (all NaN)
    df = df.dropna(axis=1, how='all')

    st.subheader("Preview Extracted Data")
    st.dataframe(df)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
