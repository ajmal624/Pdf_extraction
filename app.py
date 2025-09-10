import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
import re

st.title("Appraisal OCR Extractor – No Fixed Keywords")

uploaded_file = st.file_uploader("Upload an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # OCR with coordinates
    data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DATAFRAME)
    data = data.dropna().reset_index(drop=True)

    extracted = []

    for index, row in data.iterrows():
        text = row['text'].strip()
        if not text:
            continue

        info_type = None
        # Detect emails
        if re.search(r'[\w\.-]+@[\w\.-]+', text):
            info_type = "Email"
        # Detect phone numbers
        elif re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text):
            info_type = "Phone Number"
        # Detect dates
        elif re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text):
            info_type = "Date"
        # Detect amounts
        elif re.search(r'\$\s*\d+(?:[.,]\d{2})?', text):
            info_type = "Amount"
        # Detect time formats
        elif re.search(r'\b\d{1,2}:\d{2}\s*(AM|PM|am|pm)?\b', text):
            info_type = "Time"

        # Add detected info or just raw text
        extracted.append({
            "Detected Type": info_type if info_type else "Text",
            "Content": text,
            "Left": row['left'],
            "Top": row['top']
        })

    df = pd.DataFrame(extracted)

    st.subheader("Detected Information")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="appraisal_data.csv", mime="text/csv")
