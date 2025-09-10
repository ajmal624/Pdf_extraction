import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import tempfile

st.title("Document Field Extractor")

# Upload image
uploaded_file = st.file_uploader("Upload document image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name

    # Load image
    image = cv2.imread(file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)

    # OCR with layout data
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DATAFRAME, config=custom_config)

    # Clean data
    data = data[data.conf != -1]
    data = data[data.text.notnull() & (data.text.str.strip() != '')]
    data = data[data.conf > 50]

    # Pairing fields: Group by line number and sort by 'left' position
    grouped = data.groupby('line_num')
    results = []

    for line_num, group in grouped:
        group_sorted = group.sort_values('left')
        texts = group_sorted.text.tolist()
        
        # Try pairing adjacent texts: left as field, right as value
        if len(texts) >= 2:
            field = texts[0]
            value = " ".join(texts[1:])
            results.append((field.strip(), value.strip()))
        else:
            # Single text could be field without value
            results.append((texts[0].strip(), ""))

    # Create DataFrame
    df = pd.DataFrame(results, columns=["Field", "Value"])

    # Show dataframe
    st.subheader("Extracted Fields and Values")
    st.dataframe(df)

    # Provide download option
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download as CSV", data=csv_data, file_name="fields.csv", mime="text/csv")
