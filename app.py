import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import re

st.title("Field Name Extractor from Image")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Load and preprocess image
    image = Image.open(uploaded_file)
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

    # OCR extraction
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)
    data = data.dropna(subset=['text'])
    data = data[data.conf != -1]

    # Group by lines
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])
    lines = []
    for (_, _, _), group in grouped:
        line_text = ' '.join(group.text).strip()
        if line_text:
            lines.append(line_text)

    # Known keywords that likely represent field names
    keywords = ["Date", "Client", "Information", "Property", "Commercial", "Address",
                "Reason", "Appraisal", "Fee", "Scheduled", "Time", "Access", "Name"]

    field_names = []
    for line in lines:
        original_line = line
        line = line.strip()

        # Remove lines that are mostly punctuation or too noisy
        num_chars = len(line)
        if num_chars == 0:
            continue

        # Count numbers and punctuation
        num_numbers = sum(c.isdigit() for c in line)
        num_punctuations = sum(1 for c in line if not c.isalnum() and not c.isspace())

        # Heuristic rules to remove noise
        if num_numbers / max(1, num_chars) > 0.5:
            continue  # too many numbers
        if num_punctuations / max(1, num_chars) > 0.3:
            continue  # too much punctuation
        if len(line) < 2:
            continue  # too short

        # Normalize line by removing extra spaces and splitting at colon
        if ':' in line:
            line = line.split(':')[0].strip()

        # Check for keywords
        has_keyword = any(kw.lower() in line.lower() for kw in keywords)

        # Accept lines if they have keywords or are short and clean
        if has_keyword or (len(line.split()) <= 5 and num_punctuations < 3):
            field_names.append(line)

    # Remove duplicates while preserving order
    seen = set()
    final_fields = []
    for name in field_names:
        name = name.strip()
        if name and name not in seen:
            seen.add(name)
            final_fields.append(name)

    # Display the final field names
    st.subheader("Extracted Field Names")
    for name in final_fields:
        st.write(name)

    # Save to CSV
    df = pd.DataFrame(final_fields, columns=["Field Name"])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="field_names.csv",
        mime="text/csv"
    )
