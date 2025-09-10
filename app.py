import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
from PIL import Image

st.title("Extract Field Names from Document")

st.write("Upload an image and extract possible field names using OCR.")

uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save the uploaded image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load the image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # OCR with detailed data
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Filter out empty text and low-confidence results
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Group by line number
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])

    lines = []
    for (block, par, line), group in grouped:
        line_text = ' '.join(group.text)
        x = group.left.min()
        y = group.top.min()
        lines.append({'text': line_text, 'x': x, 'y': y})

    # Sort lines by their y-coordinate
    lines = sorted(lines, key=lambda x: x['y'])

    st.subheader("Detected Lines")
    for line in lines:
        st.write(f"{line['y']}: {line['text']}")

    # Heuristic: Identify lines that are likely field names
    # Criteria:
    # 1. Lines ending with ':' or '?'
    # 2. Lines with short length (e.g., <= 5 words)
    # 3. Lines containing keywords like 'Name', 'Date', 'Address', etc.
    #    (Optional – can be skipped if you want purely based on format)

    possible_field_names = []
    for line in lines:
        text = line['text'].strip()
        if text.endswith(":") or text.endswith("?") or len(text.split()) <= 5:
            possible_field_names.append(text)

    # Remove duplicates and clean entries
    possible_field_names = list(dict.fromkeys(possible_field_names))

    st.subheader("Extracted Field Names")
    df = pd.DataFrame(possible_field_names, columns=["Field Name"])
    st.dataframe(df)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Field Names as CSV",
        data=csv,
        file_name="field_names.csv",
        mime="text/csv"
    )
