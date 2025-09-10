import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
from PIL import Image

# Optional: set this if Tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Dynamic Document Data Extraction")

st.write("Upload an image. The app will dynamically extract text lines and associate nearby lines as field-value pairs.")

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

    # Filter out empty and low-confidence results
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Group by lines
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])
    lines = []
    for (block, par, line), group in grouped:
        line_text = ' '.join(group.text)
        x = group.left.min()
        y = group.top.min()
        w = group.width.max()
        h = group.height.max()
        lines.append({
            'text': line_text.strip(),
            'x': x,
            'y': y,
            'w': w,
            'h': h,
            'right': x + w,
            'bottom': y + h,
            'center_x': x + w // 2,
            'center_y': y + h // 2
        })

    # Sort lines by y-coordinate (top to bottom)
    lines = sorted(lines, key=lambda l: (l['y'], l['x']))

    st.subheader("Detected Lines")
    for line in lines:
        st.write(f"{line['y']}: {line['text']}")

    # Associate lines as field-value pairs based on spatial proximity
    extracted = []
    used_indices = set()

    for i, line in enumerate(lines):
        if i in used_indices:
            continue

        label = line['text']
        value = ""

        # Look for candidate value in nearby lines
        for j, candidate in enumerate(lines):
            if j == i or j in used_indices:
                continue

            # Heuristic: same line and to the right
            same_line = abs(candidate['y'] - line['y']) < 10
            to_right = candidate['x'] > line['x'] + line['w']

            # Heuristic: next line below with similar alignment
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

    # Display extracted field-value pairs
    st.subheader("Extracted Fields")
    df = pd.DataFrame(extracted)
    st.dataframe(df)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
