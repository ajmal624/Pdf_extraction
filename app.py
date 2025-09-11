import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np
import cv2
import tempfile

st.title("OCR Extraction App using EasyOCR")

uploaded_file = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button("Extract Text"):
        with st.spinner("Running OCR..."):
            # Convert image to numpy array
            image_np = np.array(image)

            # Convert RGB to BGR for OpenCV
            image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            # Initialize EasyOCR reader
            reader = easyocr.Reader(['en'], gpu=False)

            # Perform OCR
            results = reader.readtext(image_cv)

            # Prepare data for display and saving
            data = []
            for bbox, text, prob in results:
                data.append({"Text": text, "Confidence": round(prob, 2)})

            df = pd.DataFrame(data)

            st.dataframe(df)

            # Save as CSV
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".csv") as tmp_file:
                df.to_csv(tmp_file.name, index=False)
                tmp_file_path = tmp_file.name

            st.success("OCR extraction completed!")
            st.download_button("Download CSV", data=open(tmp_file_path, "rb"), file_name="ocr_output.csv")
