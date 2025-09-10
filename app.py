import streamlit as st
import pytesseract
import cv2
import pandas as pd
import tempfile

# Optional: Set tesseract path if necessary
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Appraisal OCR - Raw Text Extraction")

st.write("Upload an image, and this app will extract all text elements with their coordinates without predefined field names.")

# File uploader
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Read image using OpenCV
    image = cv2.imread(file_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding to improve OCR accuracy
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Perform OCR and get detailed data including coordinates
    data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DATAFRAME)

    # Drop empty text rows
    data = data[data.text.notna()]
    data = data[data.text.str.strip() != ""]

    # Show extracted data
    st.subheader("Extracted Text Elements")
    st.dataframe(data[['level', 'left', 'top', 'width', 'height', 'conf', 'text']])

    # Allow user to download the data as CSV
    csv = data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="ocr_output.csv",
        mime="text/csv"
    )
