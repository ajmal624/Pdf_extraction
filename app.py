import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import re

# Optional: If Tesseract is not in your PATH, set the correct path
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Extract Field Names from Uploaded Image")

st.write("Upload an image and extract field names (complete lines, not individual words).")

# Upload image
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Load image from uploaded file
    img = Image.open(uploaded_file)

    st.image(img, caption="Uploaded Image", use_column_width=True)

    # OCR with pytesseract
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DATAFRAME)

    # Filter out empty and low-confidence entries
    data = data[data.conf != -1]
    data = data.dropna(subset=['text'])
    data = data[data.conf > 50]  # Adjust confidence threshold if needed

    # Group text by block, paragraph, and line numbers
    grouped = data.groupby(['block_num', 'par_num', 'line_num'])

    lines = []
    for _, group in grouped:
        line_text = ' '.join(group.text).strip()
        lines.append(line_text)

    # Remove duplicates and empty lines
    lines = list(dict.fromkeys(lines))
    lines = [line for line in lines if len(line) > 2]

    st.subheader("Extracted Field Names")
    df = pd.DataFrame(lines, columns=["Field Name"])
    st.dataframe(df)

    # Download CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="field_names.csv",
        mime="text/csv"
    )
