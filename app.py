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
    # Save image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load and process image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # OCR extraction
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Filter out empty entries
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Sort by top coordinate then left coordinate
    data = data.sort_values(by=['top', 'left']).reset_index(drop=True)

    # Extract fields by proximity
    lines = []
    for _, row in data.iterrows():
        lines.append({
            'text': row['text'],
            'left': row['left'],
            'top': row['top'],
            'width': row['width'],
            'height': row['height']
        })

    # Heuristic pairing: find nearby text blocks on the same line or close vertically
    pairs = []
    used_indices = set()
    for i, line in enumerate(lines):
        if i in used_indices:
            continue
        key = line['text']
        key_right = line['left'] + line['width']
        key_bottom = line['top'] + line['height']

        # Find nearest text to the right or below
        value = ""
        min_dist = float('inf')
        value_idx = -1

        for j, candidate in enumerate(lines):
            if j == i or j in used_indices:
                continue
            # Check if candidate is to the right on the same line
            same_line = abs(candidate['top'] - line['top']) < 10 and candidate['left'] > key_right
            below_line = abs(candidate['left'] - line['left']) < 20 and candidate['top'] > key_bottom

            if same_line or below_line:
                dist = np.hypot(candidate['left'] - key_right, candidate['top'] - key_bottom)
                if dist < min_dist:
                    min_dist = dist
                    value = candidate['text']
                    value_idx = j

        if value_idx != -1:
            used_indices.add(value_idx)
        used_indices.add(i)
        pairs.append((key, value))

    # Display extracted fields
    df = pd.DataFrame(pairs, columns=["Field", "Value"])
    st.subheader("Extracted Fields")
    st.dataframe(df)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="extracted_fields.csv",
        mime="text/csv"
    )
