import streamlit as st
import pdfplumber
import pandas as pd
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from io import BytesIO
import docx
import fitz  # PyMuPDF for PDF → Word-like conversion


st.set_page_config(page_title="PDF Extractor Pro", layout="wide")
st.title("📄 PDF Extractor Pro App")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

def extract_text_with_ocr(file_bytes):
    """Try normal extraction, fallback to OCR"""
    pdf_text = ""

    # Try pdfplumber first
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pdf_text += text + "\n"

    # Fallback OCR if no text layer
    if not pdf_text.strip():
        st.write("🔍 No text layer detected, running OCR...")
        try:
            images = convert_from_bytes(file_bytes)
            for img in images:
                text = pytesseract.image_to_string(img)
                pdf_text += text + "\n"
            if pdf_text.strip():
                st.success("✅ OCR text extracted successfully!")
        except Exception as e:
            st.error(f"❌ OCR failed: {e}")

    return pdf_text


def extract_key_values(pdf_text):
    """Extract only lines with : as key-value"""
    pdf_data = {}
    for line in pdf_text.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        field, value = line.split(":", 1)
        pdf_data[field.strip()] = value.strip()
    return pdf_data


def convert_pdf_to_word(file_bytes, output_path="converted.docx"):
    """Convert PDF → Word using PyMuPDF (basic text flow)"""
    doc = docx.Document()
    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    for page in pdf:
        text = page.get_text("text")
        if text.strip():
            doc.add_paragraph(text)
    doc.save(output_path)
    return output_path


def extract_from_word(docx_path):
    """Extract field:value or tabular from Word"""
    pdf_data = {}
    doc = docx.Document(docx_path)
    for para in doc.paragraphs:
        line = para.text.strip()
        if not line:
            continue
        if ":" in line:
            field, value = line.split(":", 1)
            pdf_data[field.strip()] = value.strip()
    return pdf_data


if uploaded_file:
    file_bytes = uploaded_file.read()

    # Button 1 → Direct PDF Extraction
    if st.button("📑 Extract from PDF (Direct)"):
        pdf_text = extract_text_with_ocr(file_bytes)
        if not pdf_text.strip():
            st.error("❌ No text extracted from PDF.")
        else:
            data = extract_key_values(pdf_text)
            data["Filename"] = uploaded_file.name
            df = pd.DataFrame([data])
            st.subheader("✅ Extracted Data (Direct)")
            st.dataframe(df)

            csv = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 Download CSV", csv, file_name="extracted_direct.csv", mime="text/csv")

    # Button 2 → Convert to Word → Extract
    if st.button("📝 Convert to Word & Extract"):
        word_path = convert_pdf_to_word(file_bytes, "temp.docx")
        data = extract_from_word(word_path)
        data["Filename"] = uploaded_file.name
        df = pd.DataFrame([data])
        st.subheader("✅ Extracted Data (Word-based)")
        st.dataframe(df)

        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("📥 Download CSV", csv, file_name="extracted_word.csv", mime="text/csv")
