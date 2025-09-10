import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
from PIL import Image

# Optional: Set tesseract path if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Field Name Extractor from Document")

# Upload file
uploaded_file = st.file_uploader("Upload an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # OCR extraction
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Filter out empty text
    data = data[data.text.notnull() & (data.text.str.strip() != '')]

    # Heuristic: Take texts with confidence > 50 and group by line number
    fields = []
    grouped = data.groupby('line_num')

    for _, group in grouped:
        text_line = " ".join(group['text'].tolist())
        fields.append(text_line.strip())

    # Store field names
    df = pd.DataFrame(fields, columns=["Field Name"])

    st.subheader("Detected Field Names")
    st.dataframe(df)

    # Download CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="fields.csv", mime="text/csv")
