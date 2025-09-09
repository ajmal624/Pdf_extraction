import streamlit as st
import pdfplumber
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import base64

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App (Text + OCR)")

uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

def extract_text(file):
    """Extract text from PDF (text-based or OCR if image-based)."""
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except:
        pass

    if not text.strip():
        st.info("🔍 No text layer detected, running OCR...")
        try:
            images = convert_from_bytes(file.getvalue())
            for img in images:
                text += pytesseract.image_to_string(img) + "\n"
        except Exception as e:
            st.error(f"❌ OCR failed: {e}")

    return text

def parse_lines_to_dict(text):
    """Convert lines into dictionary: first word(s) as field, rest as value."""
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            field, value = parts
            data[field] = value.strip()
        else:
            data[parts[0]] = ""
    return data

def display_pdf(file):
    """Preview PDF in Streamlit using iframe."""
    base64_pdf = base64.b64encode(file.getvalue()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="900" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.subheader(f"📄 Preview: {uploaded_file.name}")
        display_pdf(uploaded_file)

    # Extraction options
    option = st.radio("Select extraction mode:", ["Extract PDF as-is", "Extract Table Data (all lines)"])

    if st.button("Run Extraction"):
        all_data = []
        for uploaded_file in uploaded_files:
            text = extract_text(uploaded_file)
            if not text.strip():
                st.warning(f"❌ No text found in {uploaded_file.name}")
                continue

            if option == "Extract PDF as-is":
                st.subheader(f"📄 Extracted Text from {uploaded_file.name}")
                st.text_area("PDF Text", text, height=300)

            elif option == "Extract Table Data (all lines)":
                pdf_data = parse_lines_to_dict(text)
                pdf_data["Filename"] = uploaded_file.name
                all_data.append(pdf_data)

        if option == "Extract Table Data (all lines)" and all_data:
            st.subheader("✅ Extracted Table Data")
            df = pd.DataFrame(all_data)
            df = df.dropna(axis=1, how="all")
            st.dataframe(df)

            csv = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Download Extracted CSV",
                data=csv,
                file_name="extracted_data.csv",
                mime="text/csv"
            )
