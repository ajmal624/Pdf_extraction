import streamlit as st
import pdfplumber
import pandas as pd
import re

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
            if not line or ":" not in line:
                continue  # skip lines without ":"

            # Split only at the first ":"
            parts = line.split(":", 1)
            field = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            pdf_data[field] = value

        # Add filename
        pdf_data["Filename"] = uploaded_file.name
        all_data.append(pdf_data)

    # Create DataFrame dynamically with all unique fields
    df = pd.DataFrame(all_data)
    df = df.fillna("")  # optional, replace missing fields with empty string

    st.subheader("Preview Extracted Data")
    st.dataframe(df)

    # Download CSV
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
