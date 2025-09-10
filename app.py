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
    # Fix common OCR artifacts
    replacements = {
        "â€™": "'",
        "—": "-",
        "“": '"',
        "”": '"',
        "|": " ",  # Replace pipe with space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def extract_fields_advanced(text):
    # List of known fields in order of appearance
    fields = [
        "How did you hear about us",
        "Date",
        "Client Name",
        "Client Information",
        "Name",
        "Telephone",
        "Email",
        "Property Information",
        "Commercial or Mixed",
        "Commercial isal?",
        "Address or Mixed",
        "Reason for appraisal",
        "Appraisal Information",
        "Appraiser Fee",
        "Scheduled date",
        "Scheduled time",
        "ETA",
        "Access",
        "Name on report"
    ]

    # Clean text first
    text = clean_text(text)

    # Build regex pattern to split text by fields (using lookahead)
    # Escape field names for regex
    escaped_fields = [re.escape(f) for f in fields]
    pattern = r"(?=(" + "|".join(escaped_fields) + r"))"

    # Split text by field names, keep the field names in the results
    parts = re.split(pattern, text)

    # parts will be like ['', 'Date', '7/23/25 Client Information Name Telephone Email Bruce Davidson ...', 'Name on report', 'The Village of Liberty...']

    # Combine field names with their content
    combined = []
    i = 1
    while i < len(parts):
        field_name = parts[i].strip()
        if i + 1 < len(parts):
            value = parts[i + 1].strip()
        else:
            value = ""
        combined.append((field_name, value))
        i += 2

    # Post-process combined to merge related fields if needed
    # For example, "Client Information" contains Name, Telephone, Email in one block
    # You can parse those subfields here if needed

    # For simplicity, return combined as is
    return combined

def main():
    st.title("OCR PDF Field Extractor with Advanced Parsing")

    st.write("Upload an OCR-based PDF file. The app will perform OCR, then extract fields and values using advanced parsing.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        with st.spinner("Performing OCR on PDF pages..."):
            text = ocr_pdf(file_bytes)

        if not text.strip():
            st.error("No text found after OCR. Please check the PDF or try a different file.")
            return

        extracted = extract_fields_advanced(text)

        if not extracted:
            st.warning("No fields and values found with the current extraction pattern.")
            return

        # Convert to DataFrame
        df = pd.DataFrame(extracted, columns=["Field", "Value"])

        st.subheader("Extracted Fields and Values")
        st.dataframe(df)

        # CSV download
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
