import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import tempfile

# Title of the app
st.title("Image Text Extraction with OCR")

# File uploader widget
uploaded_file = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Open and display the uploaded image
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_column_width=True)

    # OCR extraction button
    if st.button("Extract Text"):
        with st.spinner("Extracting text..."):
            # Use pytesseract to extract text
            extracted_text = pytesseract.image_to_string(image)

            # Process text into lines and create a DataFrame
            lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
            df = pd.DataFrame(lines, columns=["Extracted Text"])

            # Show the extracted text
            st.dataframe(df)

            # Save DataFrame to CSV and provide download link
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".csv") as tmp_file:
                df.to_csv(tmp_file.name, index=False)
                tmp_file_path = tmp_file.name

            st.success("Text extraction complete!")
            st.download_button("Download CSV", data=open(tmp_file_path, "rb"), file_name="extracted_text.csv")
