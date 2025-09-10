import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
from PIL import Image

st.title("Document Field Name Extraction")

st.write("Upload an image and extract only the field names using OCR.")

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

    # Remove empty text entries and low confidence results
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Group by line number
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])

    lines = []
    for (block, par, line), group in grouped:
        line_text = ' '.join(group.text).strip()
        lines.append({'text': line_text})

    # Heuristic to find field names:
    # - Lines that end with ":" or "-"
    # - Lines that are short (<= 5 words)
    # - Lines that are all uppercase or title case

    possible_fields = set()

    for i, line in enumerate(lines):
        text = line['text']

        # Rule 1: Ends with ":" or "-"
        if text.endswith(":") or text.endswith("-"):
            possible_fields.add(text.rstrip(":-").strip())
            continue

        # Rule 2: Short lines, likely field names
        if len(text.split()) <= 5:
            possible_fields.add(text.strip())
            continue

        # Rule 3: Lines in uppercase or title case
        if text.isupper() or text.istitle():
            possible_fields.add(text.strip())
            continue

    # Convert to sorted list
    sorted_fields = sorted(possible_fields)

    # Display the extracted field names
    st.subheader("Extracted Field Names")
    if sorted_fields:
        df = pd.DataFrame(sorted_fields, columns=["Field Name"])
        st.dataframe(df)

        # CSV download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Field Names as CSV",
            data=csv,
            file_name="field_names.csv",
            mime="text/csv"
        )
    else:
        st.write("No field names detected.")
