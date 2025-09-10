import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image

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
    keywords = ["Date", "Client", "Information", "Property", "Commercial", "Address", "Reason", "Appraisal", "Fee", "Scheduled", "Time", "Access", "Name"]

    field_names = []
    for line in lines:
        original_line = line
        line = line.strip()

        # Normalize line by splitting at colon
        if ':' in line:
            line = line.split(':')[0].strip()

        words = line.split()
        num_words = len(words)
        has_numbers = any(char.isdigit() for char in line)
        punctuation_count = sum(1 for char in line if char in [":", "|", "-", "—", ".", ","])

        # Conditions to keep the line
        is_short = num_words <= 6
        has_keyword = any(kw.lower() in line.lower() for kw in keywords)

        # Accept if it is short or has known keywords, but not if it's mostly noise
        if (is_short or has_keyword) and punctuation_count < 5:
            if not has_numbers or has_keyword:
                field_names.append(line)

    # Remove duplicates and keep order
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
