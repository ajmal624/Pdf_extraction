import streamlit as st
import cv2
import pytesseract
from PIL import Image
import numpy as np
import pandas as pd
import io

# Set path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux/Mac
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows

def preprocess_image(image):
    image = np.array(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    denoised = cv2.medianBlur(thresh, 3)
    processed = cv2.bitwise_not(denoised)
    return processed

def extract_text(image):
    processed = preprocess_image(image)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(processed, config=custom_config)
    return text, processed

def parse_text_to_fields(text):
    # Basic parsing by looking for common field names
    lines = text.split('\n')
    fields = {}
    current_key = None
    current_value = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(keyword in line.lower() for keyword in ["name", "email", "telephone", "address", "date", "fee", "scheduled time", "reason", "commercial", "mixed", "notes"]):
            if current_key:
                fields[current_key] = current_value.strip()
            if ':' in line:
                parts = line.split(":", 1)
                current_key = parts[0].strip()
                current_value = parts[1].strip()
            else:
                current_key = line.strip()
                current_value = ""
        else:
            current_value += " " + line
    if current_key:
        fields[current_key] = current_value.strip()
    return fields

def convert_dict_to_csv(fields):
    df = pd.DataFrame([fields])
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

def main():
    st.title("📄 Appraisal Document OCR Extractor")

    uploaded_file = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        with st.spinner("Processing..."):
            text, processed_image = extract_text(image)

        st.subheader("✅ Extracted Text")
        st.text_area("OCR Output", text, height=300)

        st.subheader("🖼 Preprocessed Image")
        st.image(processed_image, caption="Preprocessed Image", use_column_width=True)

        # Parse text into fields
        fields = parse_text_to_fields(text)
        st.subheader("📋 Extracted Fields")
        st.json(fields)

        # Convert to CSV and provide download button
        csv_data = convert_dict_to_csv(fields)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name="extracted_data.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
