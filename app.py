import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 Dynamic PDF Field Extractor App")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

def extract_text(file):
    """Extract text from PDF. If none, use OCR."""
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if not text.strip():  # OCR fallback
            images = convert_from_bytes(file.getvalue())
            for img in images:
                text += pytesseract.image_to_string(img)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text

def parse_dynamic_fields(text):
    """
    Parse text dynamically into field-value pairs.
    Treat lines ending with ':' as new fields. 
    Multi-line values are appended to last detected field.
    """
    data = {}
    current_field = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            field, value = line.split(":", 1)
            field = field.strip()
            value = value.strip()
            current_field = field
            data[current_field] = value
        elif current_field:
            # Append line to last detected field
            if data[current_field]:
                data[current_field] += "\n" + line
            else:
                data[current_field] = line
    return data

if uploaded_file:
    # Preview PDF
    st.subheader("📖 PDF Preview")
    pdf_bytes = uploaded_file.read()
    st.pdf(BytesIO(pdf_bytes))

    # Extract text and parse dynamically
    raw_text = extract_text(BytesIO(pdf_bytes))
    
    if raw_text.strip():
        parsed_data = parse_dynamic_fields(raw_text)
        st.subheader("✅ Extracted Table")
        df = pd.DataFrame([parsed_data])
        st.dataframe(df)

        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 Download CSV",
            csv,
            file_name=uploaded_file.name.replace(".pdf", ".csv"),
            mime="text/csv"
        )
    else:
        st.warning("⚠️ No text found in this PDF. It might be scanned or image-based.")
