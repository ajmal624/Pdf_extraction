import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
import re
from PIL import Image

st.title("Document Data Extraction with Heuristics")

uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load image and preprocess
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # OCR extraction
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)
    data = data[data.conf != -1].dropna(subset=['text'])

    # Group lines by proximity
    lines = []
    for _, row in data.iterrows():
        lines.append({
            'text': row['text'],
            'x': row['left'],
            'y': row['top'],
            'w': row['width'],
            'h': row['height']
        })

    # Sort by vertical position
    lines = sorted(lines, key=lambda l: l['y'])

    # Merge lines that are close to each other vertically
    merged_lines = []
    threshold = 10  # pixels
    for line in lines:
        if not merged_lines:
            merged_lines.append(line)
            continue
        prev = merged_lines[-1]
        if abs(line['y'] - (prev['y'] + prev['h'])) < threshold:
            # Merge text
            prev['text'] += " " + line['text']
            prev['h'] = max(prev['h'], line['h'])
        else:
            merged_lines.append(line)

    st.subheader("Merged Lines")
    for line in merged_lines:
        st.write(f"{line['y']}: {line['text']}")

    # Define patterns
    patterns = {
        'Date': r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        'Client Email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        'Client Telephone': r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    }

    # Heuristic extraction function
    def extract_field(pattern, lines):
        for line in lines:
            match = re.search(pattern, line['text'])
            if match:
                return match.group()
        return "Not Found"

    # Extract fields
    fields = {}
    fields['Date'] = extract_field(patterns['Date'], merged_lines)
    fields['Client Email'] = extract_field(patterns['Client Email'], merged_lines)
    fields['Client Telephone'] = extract_field(patterns['Client Telephone'], merged_lines)

    # Heuristic for other fields without patterns
    def extract_by_context(keywords, lines):
        for line in lines:
            for kw in keywords:
                if kw.lower() in line['text'].lower():
                    # Extract part after keyword or full line if needed
                    parts = line['text'].split(kw)
                    if len(parts) > 1 and parts[1].strip():
                        return parts[1].strip()
                    else:
                        return line['text'].strip()
        return "Not Found"

    fields['Client Name'] = extract_by_context(["Name", "Client", "Contact"], merged_lines)
    fields['Property Address'] = extract_by_context(["Address", "Location", "Site"], merged_lines)
    fields['Reason for appraisal'] = extract_by_context(["Reason", "Purpose"], merged_lines)
    fields['Appraiser Fee'] = extract_by_context(["Fee", "Cost", "Charge"], merged_lines)
    fields['ETA Standard'] = extract_by_context(["ETA", "Turnaround", "Expected"], merged_lines)
    fields['Access'] = extract_by_context(["Access", "Entry", "Availability"], merged_lines)
    fields['Name on report'] = extract_by_context(["Name on report", "Report Title"], merged_lines)

    # Display results
    st.subheader("Extracted Fields with Heuristics")
    df = pd.DataFrame(list(fields.items()), columns=["Field", "Value"])
    st.dataframe(df)

    # CSV Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="extracted_data.csv", mime="text/csv")
