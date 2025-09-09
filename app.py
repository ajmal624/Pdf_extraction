import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PDF Extractor", layout="wide")
st.title("📄 PDF Extractor App")

uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

def preview_pdf_as_images(file):
    try:
        images = convert_from_bytes(file.getvalue())
        st.subheader(f"📄 Preview: {file.name}")
        for i, img in enumerate(images):
            st.image(img, caption=f"Page {i+1}", use_column_width=True)
        return images
    except Exception as e:
        st.error(f"❌ Error converting PDF to images: {e}")
        return []

def extract_text_from_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        st.warning("⚠️ PDF might be scanned or corrupted. Falling back to OCR...")
        return None

def extract_text_from_images(images):
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text

def extract_table_to_csv(text, filename):
    data = []
    for line in text.splitlines():
        line = line.strip()
        if line:  # ignore empty lines
            # treat each line as a field-value pair without ":" check
            data.append({"Line": line})
    if data:
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("📥 Download Extracted CSV", csv, file_name=filename.replace(".pdf",".csv"), mime="text/csv")
        st.dataframe(df)

if uploaded_file:
    # Preview PDF
    images = preview_pdf_as_images(uploaded_file)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📝 Extract PDF Directly"):
            text = extract_text_from_pdf(uploaded_file)
            if not text:  # If text is None, use OCR
                if images:
                    text = extract_text_from_images(images)
                else:
                    text = ""
            if text.strip():
                st.subheader("✅ Extracted Text")
                st.text_area("PDF Text", text, height=500)
            else:
                st.error("❌ No text could be extracted from this PDF.")

    with col2:
        if st.button("📊 Extract Table to CSV"):
            text = extract_text_from_pdf(uploaded_file)
            if not text:  # OCR fallback
                if images:
                    text = extract_text_from_images(images)
                else:
                    text = ""
            if text.strip():
                extract_table_to_csv(text, uploaded_file.name)
            else:
                st.error("❌ No text could be extracted for table conversion.")
