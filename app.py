import streamlit as st
import pandas as pd
from PIL import Image
import pytesseract

# Tesseract path setup if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("Dynamic Form Data Extractor")

# Upload file
uploaded_file = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg"])
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    # OCR processing
    ocr_text = pytesseract.image_to_string(image)
    st.text_area("OCR Output", ocr_text, height=300)

    # Split lines and process
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    
    # Simple heuristic: line with colon or common patterns treated as field name
    fields = []
    for line in lines:
        if ':' in line or (' ' in line and len(line.split()) <= 5):
            # Attempt to split field and value
            if ':' in line:
                parts = line.split(':', 1)
                field = parts[0].strip()
                value = parts[1].strip()
            else:
                # If no colon, attempt to split by first space
                parts = line.split(' ', 1)
                field = parts[0].strip()
                value = parts[1].strip() if len(parts) > 1 else ""
            fields.append({"Field": field, "Value": value})
    
    # Display and save CSV
    if fields:
        df = pd.DataFrame(fields)
        st.dataframe(df)
        
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "form_data.csv", "text/csv")
    else:
        st.write("No fields detected.")
