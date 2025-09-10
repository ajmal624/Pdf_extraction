import streamlit as st
import pytesseract
import cv2
import pandas as pd
import tempfile
from PIL import Image
import re

st.title("Dynamic Field Extraction from Document")

st.write("Upload an image and extract possible field names dynamically using OCR.")

uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save the uploaded image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Perform OCR
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Filter out empty results and low confidence
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Group by line number
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])

    lines = []
    for (block, par, line), group in grouped:
        line_text = ' '.join(group.text).strip()
        lines.append(line_text)

    # Heuristic to detect possible field names:
    # - Lines that end with ":" or "-"
    # - Lines that are short and may look like a label
    # - Lines followed by another line that is more descriptive

    possible_fields = set()

    for i, line in enumerate(lines):
        # Check if line ends with ":" or "-"
        if line.endswith(":") or line.endswith("-"):
            possible_fields.add(line.rstrip(":-").strip())
        # Check if line is short and next line looks like a value
        elif len(line.split()) <= 5 and i + 1 < len(lines):
            next_line = lines[i + 1]
            if len(next_line.split()) > 2:
                possible_fields.add(line.strip())

    # Display results
    st.subheader("Detected Field Names")
    if possible_fields:
        df = pd.DataFrame(sorted(possible_fields), columns=["Field Name"])
        st.dataframe(df)

        # CSV download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Field Names as CSV",
            data=csv,
            file_name="detected_field_names.csv",
            mime="text/csv"
        )
    else:
        st.write("No fields detected.")
