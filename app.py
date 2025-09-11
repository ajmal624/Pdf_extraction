import streamlit as st
from PIL import Image
import pytesseract
import csv

st.title("Document OCR Extraction App")

uploaded_file = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button("Extract Text"):
        with st.spinner("Processing..."):
            # --- Run OCR ---
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            words = []
            for i in range(len(ocr_data["text"])):
                text = ocr_data["text"][i].strip()
                if text:
                    words.append(text)

            extracted_text = " ".join(words)
            st.text_area("Extracted Text", extracted_text, height=300)

            # --- Save to CSV ---
            csv_filename = "extracted_fields.csv"
            with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Field", "Value"])
                writer.writerow(["Extracted Text", extracted_text])

            st.success(f"Text extraction complete! Saved as {csv_filename}")
            st.download_button("Download CSV", open(csv_filename, "rb"), file_name=csv_filename)
