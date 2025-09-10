import streamlit as st
import pdfplumber
import re
import pandas as pd
from io import StringIO, BytesIO

# Function to extract text from uploaded PDF file
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Function to extract fields and values using regex
def extract_fields(text):
    # Adjust this regex pattern based on your PDF's field-value format
    pattern = re.compile(r"(?P<field>[A-Za-z0-9 _-]+)\s*[:\-]\s*(?P<value>.+)")
    fields = {}
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            field = match.group("field").strip()
            value = match.group("value").strip()
            fields[field] = value
    return fields

# Streamlit app
def main():
    st.title("PDF Field Extractor and CSV Exporter")

    st.write("Upload a PDF file containing fields and values. The app will extract the fields and their corresponding values and allow you to download them as a CSV file.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        # Extract text from PDF
        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(uploaded_file)

        if not text.strip():
            st.error("No text found in the PDF.")
            return

        # Extract fields and values
        fields = extract_fields(text)

        if not fields:
            st.warning("No fields and values found with the current extraction pattern.")
            st.info("You may need to adjust the regex pattern in the code to match your PDF format.")
            return

        # Show extracted data
        st.subheader("Extracted Fields and Values")
        df = pd.DataFrame([fields])
        st.dataframe(df)

        # Convert dataframe to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        # Provide download button
        st.download_button(
            label="Download extracted data as CSV",
            data=csv_data,
            file_name="extracted_fields.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
