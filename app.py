import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
from PIL import Image

st.title("Dynamic Document Data Extraction")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save uploaded image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Read and preprocess the image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # OCR using pytesseract
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)
    data = data[data.conf != -1].dropna(subset=['text'])

    # Extract lines with coordinates
    lines = []
    for _, row in data.iterrows():
        text = row['text'].strip()
        if text:
            lines.append({
                'text': text,
                'x': row['left'],
                'y': row['top'],
                'w': row['width'],
                'h': row['height'],
                'center_x': row['left'] + row['width'] // 2,
                'center_y': row['top'] + row['height'] // 2
            })

    # Sort lines by top-left position (reading order)
    lines = sorted(lines, key=lambda l: (l['y'], l['x']))

    # Heuristic: associate labels with values based on proximity
    extracted = []
    used_indices = set()

    for i, line in enumerate(lines):
        if i in used_indices:
            continue
        label = line['text']
        value = ""

        # Try to find a nearby value (same line, right side or next line below)
        for j, candidate in enumerate(lines):
            if j == i or j in used_indices:
                continue

            # Horizontal proximity: on same line and to the right
            same_line = abs(candidate['y'] - line['y']) < 10
            to_right = candidate['x'] > line['x'] + line['w']

            # Vertical proximity: candidate below label
            below = candidate['y'] > line['y'] + line['h'] and abs(candidate['x'] - line['x']) < 50

            if same_line and to_right:
                value = candidate['text']
                used_indices.add(j)
                break
            elif below:
                value = candidate['text']
                used_indices.add(j)
                break

        extracted.append({'Field': label, 'Value': value})
        used_indices.add(i)

    # Display extracted fields
    st.subheader("Extracted Fields and Values")
    df = pd.DataFrame(extracted)
    st.dataframe(df)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="extracted_data.csv", mime="text/csv")
