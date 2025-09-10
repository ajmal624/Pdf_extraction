import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
from PIL import Image

# Optional: Set this if Tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Extract Field Names from Image")

st.write("Upload an image file and extract the field names, then download as a CSV.")

uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Read the image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # OCR configuration
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Clean data
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Group lines
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])
    lines = []
    for (block, par, line), group in grouped:
        line_text = ' '.join(group.text).strip()
        if line_text:
            lines.append(line_text)

    # Heuristics to identify field names
    field_names = set()
    for text in lines:
        # Ends with ":" or "-" or is short or uppercase/title case
        if text.endswith(":") or text.endswith("-"):
            field_names.add(text.rstrip(":-").strip())
        elif len(text.split()) <= 5:
            field_names.add(text.strip())
        elif text.isupper() or text.istitle():
            field_names.add(text.strip())

    sorted_fields = sorted(field_names)

    st.subheader("Extracted Field Names")

    if sorted_fields:
        df = pd.DataFrame(sorted_fields, columns=["Field Name"])
        st.dataframe(df)

        # CSV download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="field_names.csv",
            mime="text/csv"
        )
    else:
        st.write("No field names detected.")
