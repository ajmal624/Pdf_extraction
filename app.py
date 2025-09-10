import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import tempfile

# Optional: Set this if Tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Field Name Extraction from Image")

st.write("Upload an image, and the app will extract grouped field names and let you download them as CSV.")

uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Load image from uploaded file
    image = Image.open(uploaded_file)
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

    # OCR with detailed data
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Filter out empty texts and low confidence
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Group by line structure
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])

    lines = []
    for (block, par, line), group in grouped:
        line_text = ' '.join(group.text).strip()
        if line_text:  # Only include non-empty lines
            lines.append(line_text)

    # Remove duplicates and keep order
    seen = set()
    field_names = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            field_names.append(line)

    # Show extracted field names
    st.subheader("Extracted Field Names")
    for fname in field_names:
        st.write(fname)

    # Prepare CSV for download
    df = pd.DataFrame(field_names, columns=["Field Name"])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="field_names.csv",
        mime="text/csv"
    )
