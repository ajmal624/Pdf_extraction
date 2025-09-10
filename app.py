import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
import re
from PIL import Image

# Optional: Set this if Tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Dynamic Document Data Extraction")

uploaded_file = st.file_uploader("Upload a document image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Read image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # OCR with detailed data
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Group lines by block and paragraph
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])

    lines = []
    for _, group in grouped:
        text = ' '.join(group.text)
        x = group.left.min()
        y = group.top.min()
        lines.append({'text': text.strip(), 'x': x, 'y': y})

    lines = sorted(lines, key=lambda x: x['y'])

    # Display raw OCR lines
    st.subheader("Detected Text Lines")
    for line in lines:
        st.write(f"{line['y']}: {line['text']}")

    # Patterns to identify fields
    email_pattern = re.compile(r'\S+@\S+')
    phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    date_pattern = re.compile(r'\d{1,2}/\d{1,2}/\d{2,4}')
    currency_pattern = re.compile(r'\$\d+[,\d]*')

    # Extract fields based on patterns and proximity
    fields = {}

    for idx, line in enumerate(lines):
        text = line['text']

        # Date
        if date_pattern.search(text):
            fields["Date"] = date_pattern.search(text).group()

        # Email
        if email_pattern.search(text):
            fields["Client Email"] = email_pattern.search(text).group()

        # Phone
        if phone_pattern.search(text):
            fields["Client Telephone"] = phone_pattern.search(text).group()

        # Appraiser Fee
        if currency_pattern.search(text):
            fields["Appraiser Fee"] = currency_pattern.search(text).group()

    # Heuristically assign other fields based on proximity or keywords
    for idx, line in enumerate(lines):
        text = line['text'].lower()

        if "name" in text and "report" not in text:
            # Use next line if available
            if idx + 1 < len(lines):
                fields["Client Name"] = lines[idx + 1]['text']

        if "address" in text:
            if idx + 1 < len(lines):
                fields["Property Address"] = lines[idx + 1]['text']

        if "access" in text:
            fields["Access"] = lines[idx]['text']

        if "eta" in text or "standard" in text:
            fields["ETA Standard"] = lines[idx]['text']

        if "scheduled" in text and "time" in text:
            if idx + 1 < len(lines):
                fields["Scheduled date"] = lines[idx + 1]['text']

        if "report" in text:
            if idx + 1 < len(lines):
                fields["Name on report"] = lines[idx + 1]['text']

    # Display extracted fields
    st.subheader("Extracted Fields")
    df = pd.DataFrame(list(fields.items()), columns=["Field", "Value"])
    st.dataframe(df)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="extracted_fields.csv",
        mime="text/csv"
    )
