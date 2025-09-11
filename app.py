import streamlit as st
import cv2
import pytesseract
from PIL import Image
import numpy as np

# Configure tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux/Mac
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows

def preprocess_image(image):
    # Convert PIL Image to numpy array
    image = np.array(image)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Denoise image
    denoised = cv2.medianBlur(thresh, 3)

    # Invert image back
    processed = cv2.bitwise_not(denoised)

    return processed

def extract_text(image):
    processed = preprocess_image(image)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(processed, config=custom_config)
    return text, processed

def main():
    st.title("📄 Commercial Appraisal OCR Extractor")
    st.write("Upload an image of the appraisal document and extract text.")

    uploaded_file = st.file_uploader("Choose an image file", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)

        st.image(image, caption="Uploaded Image", use_column_width=True)

        with st.spinner("Processing..."):
            text, processed_image = extract_text(image)

        st.subheader("✅ Extracted Text")
        st.text_area("OCR Output", text, height=300)

        st.subheader("🖼 Preprocessed Image")
        st.image(processed_image, caption="Preprocessed Image", use_column_width=True)

if __name__ == "__main__":
    main()
