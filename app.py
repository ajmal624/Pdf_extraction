import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile

# Optional: Set path to tesseract if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("OCR Field Name Extractor")

st.write("Upload an image and extract all text blocks as field names. The result will be available as a CSV file.")

# File uploader
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load image with OpenCV
    image = cv2.imread(file_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to improve OCR accuracy
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # OCR: Get detailed data including coordinates
    data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DATAFRAME)

    # Filter out empty text
    data = data[data['text'].notnull() & (data['text'].str.strip() != '')]

    # Treat each text block as a "field name"
    fields_df = pd.DataFrame({
        "Field Name": data["text"].values
    })

    st.subheader("Extracted Field Names")
    st.dataframe(fields_df)

    # Allow user to download the CSV file
    csv = fields_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Field Names as CSV",
        data=csv,
        file_name="field_names.csv",
        mime="text/csv"
    )
