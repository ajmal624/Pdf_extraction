import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import StringIO

# OCR extraction from PDF bytes
def ocr_pdf(file_bytes):
    images = convert_from_bytes(file_bytes)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text

# Extract fields and values using regex, return list of tuples
def extract_fields(text):
    pattern = re.compile(r"(?P<field>[A-Za-z0-9 _\-\&\.\']+)\s*[:\-]\s*(?P<value>.+)")
    extracted = []
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            field = match.group("field").strip()
            value = match.group("value").strip()
            extracted.append((field, value))
    return extracted

def main():
    st.title("OCR PDF Field Extractor and CSV Exporter")

    st.write("Upload an OCR-based PDF file. The app will perform OCR to extract text, then extract fields and values, and allow CSV download.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        with st.spinner("Performing OCR on PDF pages..."):
            text = ocr_pdf(file_bytes)

        if not text.strip():
            st.error("No text found after OCR. Please check the PDF or try a different file.")
            return

        extracted = extract_fields(text)

        if not extracted:
            st.warning("No fields and values found with the current extraction pattern.")
            st.info("You may need to adjust the regex pattern in the code to match your PDF format.")
            return

        # Convert list of tuples to DataFrame with two columns: Field and Value
        df = pd.DataFrame(extracted, columns=["Field", "Value"])

        st.subheader("Extracted Fields and Values")
        st.dataframe(df)

        # Convert dataframe to CSV
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
