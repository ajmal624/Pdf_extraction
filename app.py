import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import re  # ✅ Import for regular expressions
import tempfile
from PIL import Image

# Optional: Set this if Tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Document Data Extraction App")

st.write("Upload an image file of your form and extract the key fields as a CSV.")

# Upload file
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Read image using OpenCV
    image = cv2.imread(file_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to improve OCR
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # OCR with pytesseract
    text = pytesseract.image_to_string(processed)

    st.subheader("Extracted Text")
    st.text_area("OCR Output", text, height=300)

    # Parse fields using regex
    fields = {}

    # Date
    date_match = st.text_input("Enter date pattern if needed", r"Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})")
    match = re.search(date_match, text)
    if match:
        fields["Date"] = match.group(1)

    # Client Email
    match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    if match:
        fields["Client Email"] = match.group(0)

    # Telephone
    match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if match:
        fields["Client Telephone"] = match.group(0)

    # Name
    name_match = re.search(r'Name[:\s]*(.*)', text)
    if name_match:
        fields["Client Name"] = name_match.group(1).strip()

    # Address
    address_match = re.search(r'Address[:\s]*(.*)', text)
    if address_match:
        fields["Property Address"] = address_match.group(1).strip()

    # Commercial or Mixed
    comm_match = re.search(r'Commercial or Mixed[:\s]*(.*)', text)
    if comm_match:
        fields["Commercial or Mixed"] = comm_match.group(1).strip()

    # Reason for appraisal
    reason_match = re.search(r'Reason for appraisal\?[:\s]*(.*)', text, re.DOTALL)
    if reason_match:
        fields["Reason for appraisal"] = reason_match.group(1).strip()

    # Appraiser Fee
    fee_match = re.search(r'Appraiser Fee[:\s]*(.*)', text)
    if fee_match:
        fields["Appraiser Fee"] = fee_match.group(1).strip()

    # Scheduled Date
    sched_date_match = re.search(r'Scheduled date[:\s]*(.*)', text)
    if sched_date_match:
        fields["Scheduled date"] = sched_date_match.group(1).strip()

    # Scheduled Time
    sched_time_match = re.search(r'Scheduled time[:\s]*(.*)', text)
    if sched_time_match:
        fields["Scheduled time"] = sched_time_match.group(1).strip()

    # ETA Standard
    eta_match = re.search(r'ETA Standard is (.*)', text)
    if eta_match:
        fields["ETA Standard"] = eta_match.group(1).strip()

    # Access
    access_match = re.search(r'Access to (.*)', text)
    if access_match:
        fields["Access"] = "Access to " + access_match.group(1).strip()

    # Name on Report
    report_match = re.search(r'Name on report[:\s]*(.*)', text, re.DOTALL)
    if report_match:
        fields["Name on report"] = report_match.group(1).strip()

    # Create DataFrame
    df = pd.DataFrame(list(fields.items()), columns=["Field", "Value"])

    st.subheader("Extracted Fields")
    st.dataframe(df)

    # CSV download button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
