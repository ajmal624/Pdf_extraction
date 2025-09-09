import streamlit as st
import pdfplumber
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App (Text + OCR)")

uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

def extract_text(file):
    """Extract text from PDF (text-based or OCR if image-based)."""
    text = ""
    try:
        # Try text-based extraction first
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except:
        pass

    # If no text found, use OCR
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
    """
    Convert lines into dictionary.
    Each line is treated as a separate field with its value.
    Field = first word(s), Value = rest (heuristic, depends on PDF format).
    """
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Simple heuristic: first word as key, rest as value
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            field, value = parts
            data[field] = value.strip()
        else:
            # If only one word, use as field with empty value
            data[parts[0]] = ""
    return data

if uploaded_files:
    st.subheader("📄 Uploaded PDF Preview")
    for uploaded_file in uploaded_files:
        st.write(f"**File:** {uploaded_file.name}")
        # Preview PDF (not download)
        st.download_button(
            label="📥 Download Original PDF",
            data=uploaded_file.getvalue(),
            file_name=uploaded_file.name,
            mime="application/pdf"
        )

    # Buttons for two options
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
