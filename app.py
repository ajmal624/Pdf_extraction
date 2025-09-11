import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import io

# Streamlit app
st.title("Dynamic OCR Text Extractor")

# File uploader
uploaded_file = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Open image
    image = Image.open(uploaded_file)

    # Display image
    st.image(image, caption="Uploaded Image", use_column_width=True)

    # OCR extraction
    extracted_text = pytesseract.image_to_string(image)

    # Show extracted raw text
    st.subheader("Extracted Text")
    st.text_area("OCR Output", extracted_text, height=300)

    # Process text into lines
    lines = extracted_text.split('\n')

    # Remove empty lines and strip spaces
    cleaned_lines = [line.strip() for line in lines if line.strip()]

    # Pair lines: alternate lines as Field and Value
    fields = []
    values = []
    i = 0
    while i < len(cleaned_lines):
        field = cleaned_lines[i]
        value = cleaned_lines[i+1] if i+1 < len(cleaned_lines) else ""
        fields.append(field)
        values.append(value)
        i += 2

    # Create DataFrame
    df = pd.DataFrame({
        "Field": fields,
        "Value": values
    })

    # Show DataFrame
    st.subheader("Extracted Fields and Values")
    st.dataframe(df)

    # Download button to save as CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="extracted_text.csv",
        mime="text/csv"
    )
