import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import re

st.title("Dynamic OCR Table Extraction")

uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    # Extract text
    text = pytesseract.image_to_string(image)
    st.text_area("Raw OCR Output", text, height=300)

    # Split text into lines
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Attempt to dynamically extract key-value pairs
    data = {}
    for line in lines:
        # Match patterns like "Field: value" or "Field - value"
        match = re.match(r"(.+?)[:\-]\s*(.+)", line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            data[key] = value

    # Convert to DataFrame
    if data:
        df = pd.DataFrame([data])
        st.subheader("Extracted Data Table")
        st.dataframe(df)

        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="extracted_data.csv",
            mime="text/csv"
        )
    else:
        st.warning("No key-value pairs detected. OCR might need better preprocessing.")
