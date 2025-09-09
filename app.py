import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
import pandas as pd
from io import BytesIO
import base64

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
            if data[current_field]:
                data[current_field] += "\n" + line
            else:
                data[current_field] = line
    return data

def display_pdf(file):
    """Preview PDF using iframe."""
    base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

if uploaded_file:
    st.subheader("📖 PDF Preview")
    display_pdf(uploaded_file)

    # Reset file pointer for reading again
    uploaded_file.seek(0)
    raw_text = extract_text(uploaded_file)

    if raw_text.strip():
        st.subheader("✅ Extracted Table")
        parsed_data = parse_dynamic_fields(raw_text)
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
