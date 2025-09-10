import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import tempfile

# Streamlit app title
st.title("Dynamic Field Name Extractor")

# File uploader
uploaded_file = st.file_uploader("Upload document image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Save uploaded image to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Read and preprocess image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # OCR extraction using pytesseract
    custom_config = r'--oem 3 --psm 6'
    ocr_data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Filter out low confidence and empty text
    ocr_data = ocr_data[ocr_data.conf != -1]
    ocr_data = ocr_data[ocr_data.text.notnull() & (ocr_data.text.str.strip() != '')]
    ocr_data = ocr_data[ocr_data.conf > 50]

    # Group by line number to form text blocks
    fields = []
    grouped = ocr_data.groupby(['block_num', 'par_num', 'line_num'])

    for _, group in grouped:
        text_line = " ".join(group.text.tolist())
        text_line = text_line.strip()
        if text_line:
            fields.append(text_line)

    # Create DataFrame for field names
    df_fields = pd.DataFrame(fields, columns=["Field Name"])

    # Show extracted field names
    st.subheader("Detected Field Names")
    st.dataframe(df_fields)

    # Download as CSV
    csv_data = df_fields.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv_data, file_name="fields.csv", mime="text/csv")
