import streamlit as st
import pdfplumber
import pandas as pd
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App (Text + OCR Support)")

uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

def extract_text_from_pdf(file_bytes):
    """Try extracting text with pdfplumber, then fallback to OCR."""
    pdf_text = ""

    # ---------- Try text-based extraction ----------
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"
    except Exception as e:
        st.warning(f"⚠️ pdfplumber failed: {e}")

    # ---------- If no text, fallback to OCR ----------
    if not pdf_text.strip():
        st.info("🔍 No text layer detected, running OCR...")
        try:
            images = convert_from_bytes(file_bytes, dpi=300)
            for img in images:
                text = pytesseract.image_to_string(img, lang="eng")
                pdf_text += text + "\n"
        except Exception as e:
            st.error(f"❌ OCR failed: {e}")

    return pdf_text

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        st.write(f"📂 Processing: {uploaded_file.name}")

        file_bytes = uploaded_file.read()
        pdf_text = extract_text_from_pdf(file_bytes)

        if not pdf_text.strip():
            st.error(f"❌ No text extracted from {uploaded_file.name}")
            continue

        pdf_data = {}

        # ---------- Extract fields ----------
        for line in pdf_text.splitlines():
            line = line.strip()
            if ":" not in line:
                continue  # skip lines without ":"

            # Handle "File ID + Due Date" special case
            if "Due Date:" in line and "File ID" in line:
                parts = line.split("Due Date:")
                pdf_data["File ID"] = parts[0].replace("File ID", "").strip()
                pdf_data["Due Date"] = parts[1].strip()
                continue

            # Split on first colon only
            field, value = line.split(":", 1)
            field = field.strip()
            value = value.strip()

            if field and value:
                pdf_data[field] = value

        pdf_data["Filename"] = uploaded_file.name
        all_data.append(pdf_data)

    if all_data:
        df = pd.DataFrame(all_data)

        # Drop empty columns
        df = df.dropna(axis=1, how="all")

        st.subheader("✅ Extracted Data")
        st.dataframe(df)

        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="extracted_data.csv",
            mime="text/csv"
        )
