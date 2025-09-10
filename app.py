import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import tempfile
from PIL import Image

st.title("Extract Bold Field Names from Image")

st.write("Upload an image file and extract only the bold field names into a CSV.")

uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load the image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply adaptive threshold to highlight bold areas
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 10)

    # Dilate to connect text and make bold regions more visible
    kernel = np.ones((2,2), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=1)

    # Find contours which may correspond to bold text
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    mask = np.zeros_like(gray)

    # Filter by contour area and draw them on mask
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 100:  # Tune this threshold as needed
            cv2.drawContours(mask, [cnt], -1, 255, -1)

    # OCR only on bold-like areas
    result = cv2.bitwise_and(gray, gray, mask=mask)

    # OCR
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(result, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Clean data
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])

    # Group lines
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])
    field_names = set()
    for (block, par, line), group in grouped:
        line_text = ' '.join(group.text).strip()
        if line_text:
            field_names.add(line_text)

    # Sort for display
    sorted_fields = sorted(field_names)

    st.subheader("Extracted Bold Field Names")

    if sorted_fields:
        df = pd.DataFrame(sorted_fields, columns=["Field Name"])
        st.dataframe(df)

        # CSV download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="bold_field_names.csv",
            mime="text/csv"
        )
    else:
        st.write("No bold fields detected.")
