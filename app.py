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
            if ":" not in line:
                continue  # skip lines without ":"

            # Check for special case: "File ID ... Due Date:..."
            if re.search(r"Due Date\s*:", line, re.IGNORECASE) and "File ID" in line:
                # Extract File ID and Due Date separately
                file_match = re.match(r"(.*)Due Date\s*:\s*(.*)", line, re.IGNORECASE)
                if file_match:
                    file_part = file_match.group(1).strip()
                    due_part = file_match.group(2).strip()
                    pdf_data["File ID"] = file_part.replace("File ID", "").strip()
                    pdf_data["Due Date"] = due_part
                    continue

            # Normal field:value split
            field, value = line.split(":", 1)
            pdf_data[field.strip()] = value.strip()

        pdf_data["Filename"] = uploaded_file.name
        all_data.append(pdf_data)

    df = pd.DataFrame(all_data)
    df = df.loc[:, df.any()]  # Remove empty columns automatically

    st.subheader("Preview Extracted Data")
    st.dataframe(df)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
