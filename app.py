import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image

st.title("Field Name Extraction from Image")

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

    # Group lines
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])
    lines = []
    for (_, _, _), group in grouped:
        line_text = ' '.join(group.text).strip()
        if line_text:
            lines.append(line_text)

    # Heuristic filtering
    keywords = ["Information", "Address", "Commercial", "Appraisal", "Fee", "Schedule", "Access", "Name", "Date", "Telephone", "Email"]
    field_names = []
    for line in lines:
        words = line.split()
        num_words = len(words)
        has_numbers = any(char.isdigit() for char in line)
        punctuation_count = sum(1 for char in line if char in [":", "|", "-", "—", ".", ","])
        
        # Include if line is short OR has known keywords
        if (num_words <= 8 and not has_numbers and punctuation_count <= 2) or any(kw.lower() in line.lower() for kw in keywords):
            field_names.append(line)

    # Remove duplicates and empty lines
    seen = set()
    filtered_fields = []
    for name in field_names:
        name = name.strip()
        if name and name not in seen:
            seen.add(name)
            filtered_fields.append(name)

    # Display extracted field names
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
