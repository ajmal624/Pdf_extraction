import streamlit as st
import easyocr
from PIL import Image
import pandas as pd
import tempfile

# Title
st.title("Image OCR Text Extraction")

# File uploader
uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Display image
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button("Extract Text"):
        with st.spinner("Extracting text..."):
            # Initialize EasyOCR reader (only once)
            reader = easyocr.Reader(['en'], gpu=False)

            # Perform OCR
            result = reader.readtext(uploaded_file.getvalue())

            # Extract text lines
            extracted_data = []
            for res in result:
                text = res[1]
                extracted_data.append(text)

            # Create DataFrame
            df = pd.DataFrame(extracted_data, columns=["Extracted Text"])

            # Display extracted text
            st.dataframe(df)

            # Save to CSV and provide download
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".csv") as tmp_file:
                df.to_csv(tmp_file.name, index=False)
                tmp_file_path = tmp_file.name

            st.success("Extraction complete!")
            st.download_button("Download CSV", data=open(tmp_file_path, "rb"), file_name="extracted_text.csv")
