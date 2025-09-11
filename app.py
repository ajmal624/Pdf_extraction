import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import StringIO

# Hypothetical import of gemma3
import gemma3

def ocr_pdf(file_bytes):
    images = convert_from_bytes(file_bytes)
    text = ""
    for img in images:
        # First enhance the image using gemma3 before OCR
        enhanced_img = gemma3.enhance_image(img)  # Hypothetical method
        text += pytesseract.image_to_string(enhanced_img) + "\n"
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
    # Hypothetical text enhancement using gemma3
    text = gemma3.refine_text(text)
    return text

def extract_field_value_pairs(text):
    pairs = []
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        pattern = r'([^:\-\t\n\r\f\v]+?)\s*[:\-\t]\s*([^\t\n\r\f\v]+)'
        matches = re.findall(pattern, line)
        if matches:
            for field, value in matches:
                field = field.strip()
                value = value.strip()
                if field and value:
                    pairs.append((field, value))
        else:
            tokens = re.split(r'\s{2,}', line)
            if len(tokens) >= 2:
                for i in range(0, len(tokens) - 1, 2):
                    field = tokens[i].strip()
                    value = tokens[i+1].strip()
                    if field and value:
                        pairs.append((field, value))
            else:
                pairs.append((line, ""))
    return pairs

def main():
    st.title("OCR PDF Field-Value Extractor with Gemma3 Integration")

    uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        with st.spinner("Performing OCR..."):
            text = ocr_pdf(file_bytes)

        if not text.strip():
            st.error("No text found after OCR.")
            return

        text = clean_text(text)

        extracted_pairs = extract_field_value_pairs(text)

        if not extracted_pairs:
            st.warning("No field-value pairs found.")
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
            file_name="extracted_fields_values.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
