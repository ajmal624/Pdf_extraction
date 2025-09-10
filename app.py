import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
from PIL import Image

# Optional: Set this if Tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Document Data Extraction with Coordinates")

st.write("Upload an image and extract fields using OCR with position filtering.")

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
        line_text = ' '.join(group.text)
        x = group.left.min()
        y = group.top.min()
        lines.append({'text': line_text, 'x': x, 'y': y})

    # Sort lines by their y-coordinate (top to bottom)
    lines = sorted(lines, key=lambda x: x['y'])

    st.subheader("Detected Lines")
    for line in lines:
        st.write(f"{line['y']}: {line['text']}")

    # Extract fields based on keywords and proximity
    fields = {}

    # Create a simple function to find line by keyword
    def find_line(keyword):
        for line in lines:
            if keyword.lower() in line['text'].lower():
                return line['text']
        return None

    # Date
    date_line = find_line("Date")
    if date_line:
        fields["Date"] = date_line.split("Date")[-1].strip(" :")

    # Client Email
    email_line = None
    for line in lines:
        if "@" in line['text']:
            email_line = line['text']
            break
    if email_line:
        fields["Client Email"] = email_line.strip()

    # Client Telephone
    phone_line = None
    import re
    phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    for line in lines:
        if phone_pattern.search(line['text']):
            phone_line = line['text']
            break
    if phone_line:
        fields["Client Telephone"] = phone_pattern.search(phone_line).group()

    # Client Name
    name_line = find_line("Name")
    if name_line:
        fields["Client Name"] = name_line.split("Name")[-1].strip(" :")

    # Property Address
    address_line = find_line("Address")
    if address_line:
        fields["Property Address"] = address_line.split("Address")[-1].strip(" :")

    # Commercial or Mixed
    comm_line = find_line("Commercial or Mixed")
    if comm_line:
        fields["Commercial or Mixed"] = comm_line.split("Commercial or Mixed")[-1].strip(" :")

    # Reason for appraisal
    reason_line = find_line("Reason for appraisal")
    if reason_line:
        fields["Reason for appraisal"] = reason_line.split("Reason for appraisal")[-1].strip(" :")

    # Appraiser Fee
    fee_line = find_line("Appraiser Fee")
    if fee_line:
        fields["Appraiser Fee"] = fee_line.split("Appraiser Fee")[-1].strip(" :")

    # Scheduled Date
    sched_date_line = find_line("Scheduled date")
    if sched_date_line:
        fields["Scheduled date"] = sched_date_line.split("Scheduled date")[-1].strip(" :")

    # Scheduled Time
    sched_time_line = find_line("Scheduled time")
    if sched_time_line:
        fields["Scheduled time"] = sched_time_line.split("Scheduled time")[-1].strip(" :")

    # ETA Standard
    eta_line = find_line("ETA Standard")
    if eta_line:
        fields["ETA Standard"] = eta_line.split("ETA Standard")[-1].strip(" :")

    # Access
    access_line = find_line("Access")
    if access_line:
        fields["Access"] = access_line.split("Access")[-1].strip(" :")

    # Name on Report
    report_line = find_line("Name on report")
    if report_line:
        fields["Name on report"] = report_line.split("Name on report")[-1].strip(" :")

    # Display fields
    st.subheader("Extracted Fields")
    df = pd.DataFrame(list(fields.items()), columns=["Field", "Value"])
    st.dataframe(df)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
