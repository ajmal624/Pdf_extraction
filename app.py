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

def parse_line_to_pairs(line):
    # Split by tabs or 2+ spaces
    tokens = re.split(r'\t+|\s{2,}', line.strip())
    pairs = []
    i = 0
    while i < len(tokens):
        token = tokens[i].strip()
        # If token contains colon, split into field:value
        if ':' in token:
            field, value = token.split(':', 1)
            pairs.append((field.strip(), value.strip()))
            i += 1
        else:
            # Try to pair current token as field with next token as value
            if i + 1 < len(tokens):
                pairs.append((token, tokens[i+1].strip()))
                i += 2
            else:
                # No value, just field with empty string
                pairs.append((token, ""))
                i += 1
    return pairs

def extract_fields(text):
    text = clean_text(text)
    lines = text.splitlines()
    data = {}

    for line in lines:
        pairs = parse_line_to_pairs(line)
        for field, value in pairs:
            # If field already exists, append value separated by space
            if field in data and value:
                data[field] += " " + value
            else:
                data[field] = value

    return data

def main():
    st.title("Improved OCR PDF Field Extractor")

    uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        with st.spinner("Performing OCR..."):
            text = ocr_pdf(file_bytes)

        if not text.strip():
            st.error("No text found after OCR.")
            return

        extracted_data = extract_fields(text)

        if not extracted_data:
            st.warning("No fields extracted.")
            return

        df = pd.DataFrame(list(extracted_data.items()), columns=["Field", "Value"])

        st.subheader("Extracted Fields and Values")
        st.dataframe(df)

        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="extracted_fields.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
