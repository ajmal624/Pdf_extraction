import streamlit as st
from PIL import Image
import pytesseract
import torch
from transformers import LayoutLMProcessor, LayoutLMForTokenClassification
import pandas as pd
import io

# Load the processor and model
@st.cache_resource
def load_model():
    processor = LayoutLMProcessor.from_pretrained("microsoft/layoutlm-base-uncased")
    model = LayoutLMForTokenClassification.from_pretrained("microsoft/layoutlm-base-uncased")
    return processor, model

processor, model = load_model()

st.title("Document Form Field Extractor")

uploaded_file = st.file_uploader("Upload a document image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Document", use_column_width=True)

    # OCR extraction
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    words = []
    boxes = []
    for i in range(len(ocr_data["text"])):
        text = ocr_data["text"][i].strip()
        if text:
            words.append(text)
            x, y, w, h = ocr_data["left"][i], ocr_data["top"][i], ocr_data["width"][i], ocr_data["height"][i]
            width, height = image.size
            box = [
                int(1000 * x / width),
                int(1000 * y / height),
                int(1000 * (x + w) / width),
                int(1000 * (y + h) / height)
            ]
            boxes.append(box)

    # Encoding
    encoding = processor(images=image, words=words, boxes=boxes, return_tensors="pt", truncation=True, padding="max_length")

    # Prediction
    outputs = model(**encoding)
    logits = outputs.logits
    predictions = torch.argmax(logits, dim=2)
    labels = predictions[0].tolist()
    id2label = model.config.id2label

    # Extract fields dynamically
    fields = []
    current_field = ""
    current_value = ""
    current_label = None

    for word, label_id in zip(words, labels):
        label = id2label[label_id]

        if label.startswith("B-") or label.startswith("I-"):
            label_type = label.split("-")[1]

            if label_type != current_label:
                if current_field or current_value:
                    fields.append((current_field.strip(), current_value.strip()))
                current_field = word if label_type == "QUESTION" else ""
                current_value = word if label_type == "ANSWER" else ""
                current_label = label_type
            else:
                if label_type == "QUESTION":
                    current_field += " " + word
                else:
                    current_value += " " + word
        else:
            if current_field or current_value:
                fields.append((current_field.strip(), current_value.strip()))
            current_field = ""
            current_value = ""
            current_label = None

    if current_field or current_value:
        fields.append((current_field.strip(), current_value.strip()))

    # Display results
    df = pd.DataFrame(fields, columns=["Field", "Value"])
    st.subheader("Extracted Fields and Values")
    st.dataframe(df)

    # Download CSV
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, "fields.csv", "text/csv")
