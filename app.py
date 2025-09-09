import streamlit as st
import pdfplumber
import pandas as pd

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App")

uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        pdf_text = ""
        # Read PDF
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"

        # Parse field:value pairs using only ':'
        pdf_data = {}
        for line in pdf_text.splitlines():
            line = line.strip()
            if not line or ':' not in line:
                continue  # skip lines without ':'

            parts = line.split(':', 1)
            field = parts[0].strip()
            value = parts[1].strip()
            pdf_data[field] = value if value else ""

        # Add filename to the data
        pdf_data["Filename"] = uploaded_file.name
        all_data.append(pdf_data)

    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    st.subheader("Preview Extracted Data")
    st.dataframe(df.fillna(""))

    # Download button
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 Download Extracted CSV",
        data=csv,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
