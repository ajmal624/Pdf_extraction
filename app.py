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

def extract_fields_multiline(text):
    # Known field names (adjust as needed)
    known_fields = [
        "How did you hear about us", "Date", "Client Name", "Client Telephone", "Client Email",
        "Property Address", "Commercial or Mixed", "Reason for appraisal", "Appraiser Fee",
        "Scheduled date", "Scheduled time", "ETA Standard", "Access", "Name on report"
    ]

    lines = text.splitlines()
    fields = []
    current_field = None
    current_value_lines = []

    # Precompile regex to detect field line: field name followed by colon or hyphen
    field_pattern = re.compile(r"^([A-Za-z0-9 _\-\&\.\']+)\s*[:\-]\s*(.*)$")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts with a known field name followed by colon/hyphen
        match = field_pattern.match(line)
        if match and match.group(1).strip() in known_fields:
            # Save previous field if exists
            if current_field:
                value = " ".join(current_value_lines).strip()
                fields.append((current_field, value))
            # Start new field
            current_field = match.group(1).strip()
            current_value_lines = [match.group(2).strip()]
        else:
            # If line does not start with a field, append to current value (multi-line value)
            if current_field:
                current_value_lines.append(line)
            else:
                # Line before any field detected, ignore or handle as needed
                pass

    # Save last field
    if current_field:
        value = " ".join(current_value_lines).strip()
        fields.append((current_field, value))

    return fields

def main():
    st.title("OCR PDF Field Extractor and CSV Exporter (Improved)")

    st.write("Upload an OCR-based PDF file. The app will perform OCR to extract text, then extract fields and values, and allow CSV download.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        with st.spinner("Performing OCR on PDF pages..."):
            text = ocr_pdf(file_bytes)

        if not text.strip():
            st.error("No text found after OCR. Please check the PDF or try a different file.")
            return

        extracted = extract_fields_multiline(text)

        if not extracted:
            st.warning("No fields and values found with the current extraction pattern.")
            st.info("You may need to adjust the known fields list or regex pattern in the code to match your PDF format.")
            return

        df = pd.DataFrame(extracted, columns=["Field", "Value"])

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
