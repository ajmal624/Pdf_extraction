import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
import re
from PIL import Image

st.title("Custom OCR Field Extractor")

st.write("""
Upload an image, then specify field names and regex patterns to extract information from the document.
""")

# Upload image
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

# User enters field names and patterns
st.subheader("Define Fields and Patterns")

fields = {}
field_names = st.text_area("Enter field names (one per line)", help="E.g. Date, Client Email, Phone Number")
patterns = st.text_area("Enter corresponding regex patterns (one per line)", help="Use Python regex. One pattern per line.")

if uploaded_file and field_names and patterns:
    field_list = [f.strip() for f in field_names.splitlines() if f.strip()]
    pattern_list = [p.strip() for p in patterns.splitlines() if p.strip()]

    if len(field_list) != len(pattern_list):
        st.error("Number of fields and patterns must match!")
    else:
        # Create dictionary of fields and patterns
        fields = dict(zip(field_list, pattern_list))

        # Save the uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(uploaded_file.read())
            file_path = tmp_file.name

        # Load and preprocess image
        image = cv2.imread(file_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # OCR with detailed data
        custom_config = r'--oem 3 --psm 6'
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

        # Clean data
        data = data[data.conf != -1]
        data = data.dropna(subset=['text'])

        # Combine lines by block, paragraph, and line numbers
        grouped = data.groupby(['block_num', 'par_num', 'line_num'])
        lines = []
        for (_, _, _), group in grouped:
            text = ' '.join(group.text)
            x = group.left.min()
            y = group.top.min()
            lines.append({'text': text, 'x': x, 'y': y})

        # Sort lines by y-coordinate
        lines = sorted(lines, key=lambda l: l['y'])

        # Show all detected lines
        st.subheader("Detected Text Lines")
        for line in lines:
            st.write(f"{line['y']}: {line['text']}")

        # Extract fields based on user-defined patterns
        extracted = {}
        for field, pattern in fields.items():
            found = None
            regex = re.compile(pattern, re.IGNORECASE)
            for line in lines:
                match = regex.search(line['text'])
                if match:
                    found = match.group().strip()
                    break
            extracted[field] = found if found else "Not Found"

        # Display extracted fields
        st.subheader("Extracted Data")
        df = pd.DataFrame(list(extracted.items()), columns=["Field", "Value"])
        st.dataframe(df)

        # Download CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="extracted_data.csv",
            mime="text/csv"
        )
else:
    st.info("Please upload an image and define fields with regex patterns.")
