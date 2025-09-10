import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image

st.title("Field Name Extractor from Image")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

    # OCR with high confidence filtering
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)
    data = data.dropna(subset=['text'])
    data = data[data.conf != -1]  # drop invalid OCR results

    # Group lines together
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])
    lines = []
    for (_, _, _), group in grouped:
        line_text = ' '.join(group.text).strip()
        conf_score = group.conf.mean()
        if line_text and conf_score > 50:  # only keep lines with decent confidence
            lines.append(line_text)

    # Known keywords often found in field names
    keywords = ["Date", "Client", "Information", "Property", "Commercial", "Address",
                "Reason", "Appraisal", "Fee", "Scheduled", "Time", "Access", "Name"]

    field_names = []
    for line in lines:
        line_clean = line.strip()

        # Skip empty lines
        if not line_clean:
            continue

        # Skip lines with excessive numbers or punctuations
        num_chars = len(line_clean)
        num_numbers = sum(c.isdigit() for c in line_clean)
        num_punctuations = sum(1 for c in line_clean if not c.isalnum() and not c.isspace())

        if num_numbers / max(1, num_chars) > 0.5:
            continue
        if num_punctuations / max(1, num_chars) > 0.3:
            continue
        if len(line_clean) < 2 or len(line_clean) > 40:
            continue

        # Normalize: remove trailing colon text
        if ':' in line_clean:
            line_clean = line_clean.split(':')[0].strip()

        # Accept if it has a keyword or is a short clean line
        has_keyword = any(kw.lower() in line_clean.lower() for kw in keywords)
        if has_keyword or (len(line_clean.split()) <= 5 and num_punctuations < 3):
            field_names.append(line_clean)

    # Deduplicate while preserving order
    seen = set()
    final_fields = []
    for name in field_names:
        name = name.strip()
        if name and name not in seen:
            seen.add(name)
            final_fields.append(name)

    # Display the results
    st.subheader("Extracted Field Names")
    for name in final_fields:
        st.write(name)

    # Allow CSV download
    df = pd.DataFrame(final_fields, columns=["Field Name"])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="field_names.csv",
        mime="text/csv"
    )
