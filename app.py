import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
import re
from PIL import Image

st.title("Document OCR Field Extraction")

uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save uploaded image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load and preprocess the image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # OCR with detailed data
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Clean data: remove empty or low confidence entries
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Group lines by block, paragraph, and line number
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])
    lines = []
    for (_, _, _), group in grouped:
        text = ' '.join(group.text)
        x = group.left.min()
        y = group.top.min()
        lines.append({'text': text, 'x': x, 'y': y})

    # Sort lines by y coordinate (top to bottom)
    lines = sorted(lines, key=lambda l: l['y'])

    st.subheader("Detected Lines")
    for line in lines:
        st.write(f"{line['y']}: {line['text']}")

    # Define patterns to extract fields (hardcoded but scanning lines)
    patterns = {
        "Date": r'Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})',
        "Client Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        "Client Telephone": r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        "Client Name": r'Name[:\s]*(.+)',
        "Property Address": r'Address[:\s]*(.+)',
        "Commercial or Mixed": r'(Commercial|Mixed)',
        "Reason for appraisal": r'Reason[:\s]*(.+)',
        "Appraiser Fee": r'Fee[:\s]*\$?([\d,]+)',
        "Scheduled date": r'Scheduled date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})',
        "Scheduled time": r'Scheduled time[:\s]*(\d{1,2}[:.\s]?\d{2}\s*(AM|PM)?)',
        "ETA Standard": r'ETA[:\s]*(.+)',
        "Access": r'Access[:\s]*(.+)',
        "Name on report": r'Name on report[:\s]*(.+)'
    }

    # Extract fields by scanning all lines
    extracted = {}
    for field, pattern in patterns.items():
        found = None
        regex = re.compile(pattern, re.IGNORECASE)
        for line in lines:
            match = regex.search(line['text'])
            if match:
                if match.groups():
                    found = match.group(1).strip()
                else:
                    found = match.group().strip()
                break
        extracted[field] = found if found else "Not Found"

    # Display extracted fields
    st.subheader("Extracted Fields")
    df = pd.DataFrame(list(extracted.items()), columns=["Field", "Value"])
    st.dataframe(df)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
