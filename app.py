import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import re

# Optional: if Tesseract is not in your system's PATH, specify its location like below:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Extract Field Names from Uploaded Image")

st.write("Upload an image file and the app will extract the field names (bold texts or prominent lines).")

# Upload image file
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Load the image from the uploaded file
    img = Image.open(uploaded_file)

    st.image(img, caption="Uploaded Image", use_column_width=True)

    # Run OCR using pytesseract
    custom_config = r'--oem 3 --psm 6'
    ocr_data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)

    fields = []
    buffer_line = ""
    last_bottom = None

    # Loop through all detected text elements
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        conf = int(ocr_data['conf'][i])
        height = ocr_data['height'][i]
        top = ocr_data['top'][i]
        bottom = top + height

        # Skip empty or low-confidence entries
        if not text or conf < 50:
            continue

        # Skip entries that look like email or phone numbers
        if '@' in text or re.search(r'\d', text):
            continue

        # Group text lines based on vertical proximity
        if last_bottom is not None and abs(top - last_bottom) < 10:
            buffer_line += " " + text
        else:
            if buffer_line:
                fields.append(buffer_line.strip())
            buffer_line = text

        last_bottom = bottom

    # Add last buffered line
    if buffer_line:
        fields.append(buffer_line.strip())

    # Clean up text entries
    cleaned_fields = []
    for f in fields:
        # Remove unwanted characters
        f_clean = re.sub(r'[^A-Za-z0-9 ?]', '', f)
        if len(f_clean) > 2:
            cleaned_fields.append(f_clean.strip())

    # Remove duplicates while preserving order
    final_fields = list(dict.fromkeys(cleaned_fields))

    st.subheader("Extracted Field Names")
    df = pd.DataFrame(final_fields, columns=["Field Name"])
    st.dataframe(df)

    # Provide option to download as CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="field_names.csv",
        mime="text/csv"
    )
