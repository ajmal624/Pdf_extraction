import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import StringIO

def ocr_pdf(file_bytes):
    images = convert_from_bytes(file_bytes)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text

def clean_text(text):
    replacements = {
        "â€™": "'",
        "—": "-",
        "“": '"',
        "”": '"',
        "|": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def extract_key_value_pairs(text):
    text = clean_text(text)
    lines = text.splitlines()
    pairs = []

    # Regex to detect key-value pairs separated by colon, dash, or equal sign
    pattern = re.compile(r"^\s*([^:\-\=]{1,50}?)\s*[:\-=\s]{1,3}\s*(.+)$")

    for line in lines:
        match = pattern.match(line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            # Filter out lines where key or value is empty or too short
            if key and value:
                pairs.append((key, value))

    return pairs

def main():
    st.title("Dynamic OCR PDF Field Extractor")

    st.write("Upload any OCR-based PDF file. The app will perform OCR and dynamically extract key-value pairs.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        with st.spinner("Performing OCR on PDF pages..."):
            text = ocr_pdf(file_bytes)

        if not text.strip():
            st.error("No text found after OCR. Please check the PDF or try a different file.")
            return

        extracted_pairs = extract_key_value_pairs(text)

        if not extracted_pairs:
            st.warning("No key-value pairs found in the document.")
            return

        df = pd.DataFrame(extracted_pairs, columns=["Field", "Value"])

        st.subheader("Extracted Fields and Values")
        st.dataframe(df)

        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="Download extracted data as CSV",
            data=csv_data,
            file_name="extracted_fields.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
