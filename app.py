import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image

st.title("Field Name Extraction from Image (Heuristic Filter)")

uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Load image
    image = Image.open(uploaded_file)
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

    # OCR with detailed data
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Filter out empty texts and low confidence
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Group by lines
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])
    lines = []
    for (_, _, _), group in grouped:
        line_text = ' '.join(group.text).strip()
        if line_text:
            lines.append(line_text)

    # Heuristic: Consider lines with fewer than 6 words and not full sentences
    field_names = []
    for line in lines:
        words = line.split()
        if len(words) <= 6 and not any(char in line for char in [":", "|", "-", "—"]) and not any(char.isdigit() for char in line):
            field_names.append(line)

    # Further remove duplicates while preserving order
    seen = set()
    filtered_fields = []
    for name in field_names:
        if name not in seen:
            seen.add(name)
            filtered_fields.append(name)

    # Display results
    st.subheader("Extracted Field Names")
    for name in filtered_fields:
        st.write(name)

    # Prepare CSV for download
    df = pd.DataFrame(filtered_fields, columns=["Field Name"])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="field_names.csv",
        mime="text/csv"
    )
