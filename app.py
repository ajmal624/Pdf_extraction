import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
from PIL import Image

st.title("Document Field Extraction")

# Upload image
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # OCR extraction with data
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Filter out empty text
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])
    data = data.sort_values(by=['top', 'left']).reset_index(drop=True)

    # Merge nearby words into lines
    lines = []
    current_line = []
    last_top = None
    for _, row in data.iterrows():
        if last_top is None or abs(row['top'] - last_top) < 10:
            current_line.append(row['text'])
        else:
            lines.append(" ".join(current_line))
            current_line = [row['text']]
        last_top = row['top']
    if current_line:
        lines.append(" ".join(current_line))

    # Heuristic grouping into fields and values
    fields = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Treat lines ending with ':' or '?' or very short lines as field names
        if line.endswith(":") or line.endswith("?") or len(line.split()) <= 3:
            field_name = line.rstrip(":?")
            # Find next non-empty line as value
            value_lines = []
            j = i + 1
            while j < len(lines) and lines[j].strip() != "":
                value_lines.append(lines[j].strip())
                j += 1
            value = " ".join(value_lines)
            fields.append((field_name, value))
            i = j
        else:
            # If not clearly a field name, check if next line is longer and treat it as value
            if i + 1 < len(lines) and len(lines[i + 1].strip().split()) > len(line.split()):
                field_name = line
                value = lines[i + 1].strip()
                fields.append((field_name, value))
                i += 2
            else:
                i += 1

    # Display and download CSV
    df = pd.DataFrame(fields, columns=["Field", "Value"])
    st.subheader("Extracted Fields and Values")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="extracted_fields.csv",
        mime="text/csv"
    )
