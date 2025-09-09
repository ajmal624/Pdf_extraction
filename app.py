import streamlit as st
import pdfplumber
import pandas as pd
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
import re

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App (Text + OCR)")

uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

def extract_text(uploaded_file):
    """Extract text from PDF using pdfplumber, fallback to OCR if no text."""
    text_data = []
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                text_data.append(text)
            else:
                # OCR fallback
                images = convert_from_bytes(file_bytes, first_page=page_num, last_page=page_num)
                ocr_text = pytesseract.image_to_string(images[0])

                # 🛠️ Preprocess OCR text
                ocr_text = ocr_text.replace(";", ":")  # common OCR mistake
                ocr_text = re.sub(r"\s{2,}", " ", ocr_text)  # normalize spaces
                lines = []
                for line in ocr_text.splitlines():
                    line = line.strip()
                    if ":" in line:  # keep only key:value style lines
                        lines.append(line)
                text_data.append("\n".join(lines))

    return "\n".join(text_data)

def parse_pdf_text(pdf_text, filename):
    """Parse text into key:value fields only if ':' exists."""
    pdf_data = {}

    for line in pdf_text.splitlines():
        line = line.strip()
        if ":" not in line:
            continue

        # Special case: File ID + Due Date in one line
        if "Due Date:" in line and "File ID" in line:
            parts = line.split("Due Date:")
            pdf_data["File ID"] = parts[0].replace("File ID", "").strip()
            pdf_data["Due Date"] = parts[1].strip()
            continue

        field, value = line.split(":", 1)
        field = field.strip()
        value = value.strip()

        if field and value:
            pdf_data[field] = value

    pdf_data["Filename"] = filename
    return pdf_data


if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        st.write(f"📂 Processing: {uploaded_file.name}")
        pdf_text = extract_text(uploaded_file)

        if not pdf_text.strip():
            st.warning(f"No text extracted from {uploaded_file.name}")
            continue

        pdf_data = parse_pdf_text(pdf_text, uploaded_file.name)
        all_data.append(pdf_data)

    if all_data:
        df = pd.DataFrame(all_data)
        df = df.dropna(axis=1, how="all")  # drop empty columns

        st.subheader("✅ Extracted Data")
        st.dataframe(df)

        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="extracted_data.csv",
            mime="text/csv"
        )
