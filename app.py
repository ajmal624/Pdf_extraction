import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
import re
from PIL import Image

st.title("Enhanced Document Data Extraction")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load and preprocess
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Filter out invalid entries
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Combine lines grouped by paragraph
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])
    lines = []
    for _, group in grouped:
        text = ' '.join(group.text)
        x = group.left.min()
        y = group.top.min()
        lines.append({'text': text, 'x': x, 'y': y})
    lines = sorted(lines, key=lambda x: x['y'])

    # Extract fields
    fields = {}

    full_text = " ".join([line['text'] for line in lines])

    # Date
    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', full_text)
    if date_match:
        fields["Date"] = date_match.group(1)

    # Email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', full_text)
    if email_match:
        fields["Client Email"] = email_match.group(0)

    # Phone
    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', full_text)
    if phone_match:
        fields["Client Telephone"] = phone_match.group(0)

    # Name heuristic: line before email or phone
    email_line_idx = next((i for i, l in enumerate(lines) if email_match and email_match.group(0) in l['text']), None)
    if email_line_idx and email_line_idx > 0:
        name_line = lines[email_line_idx - 1]['text']
        fields["Client Name"] = name_line

    # Property Address heuristic: look for 'Main St', 'Liberty', etc.
    address_match = re.search(r'\d{1,5}\s[\w\s\.]+,\s[\w\s]+,\s?[A-Z]{2}\s?\d{5}', full_text)
    if address_match:
        fields["Property Address"] = address_match.group(0)

    # Appraiser Fee
    fee_match = re.search(r'\$\d{1,5}(?:[.,]\d{2})?', full_text)
    if fee_match:
        fields["Appraiser Fee"] = fee_match.group(0)

    # Scheduled date (fallback if date already not found)
    sched_match = re.search(r'(Scheduled date[:\s]*)?(\w{3,9}[-\s]?\d{1,2})', full_text)
    if sched_match:
        fields["Scheduled date"] = sched_match.group(2)

    # Scheduled time
    time_match = re.search(r'(\d{1,2}:\d{2}\s?(AM|PM|am|pm)?)', full_text)
    if time_match:
        fields["Scheduled time"] = time_match.group(1)

    # ETA Standard
    eta_match = re.search(r'Standard is (\d+\s\w+)', full_text)
    if eta_match:
        fields["ETA Standard"] = eta_match.group(1)

    # Access
    access_match = re.search(r'Access to the whole property', full_text, re.IGNORECASE)
    if access_match:
        fields["Access"] = access_match.group(0)

    # Name on report heuristic: search for lines with "The Village" etc.
    report_lines = [l['text'] for l in lines if 'Liberty' in l['text']]
    if report_lines:
        fields["Name on report"] = report_lines[0]

    # Other heuristics can be added similarly...

    # Show extracted fields
    st.subheader("Extracted Fields")
    df = pd.DataFrame(list(fields.items()), columns=["Field", "Value"])
    st.dataframe(df)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="extracted_data.csv", mime="text/csv")
