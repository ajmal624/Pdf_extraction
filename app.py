import pytesseract
from PIL import Image
import pandas as pd
import re

# Configure path to tesseract executable if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load the image
image_path = "your_image_file.jpg"  # Replace with your actual image path
img = Image.open(image_path)

# Perform OCR with layout analysis
custom_config = r'--oem 3 --psm 6'
ocr_data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)

# Heuristics to filter field names
fields = []
buffer_line = ""
last_bottom = None

for i in range(len(ocr_data['text'])):
    text = ocr_data['text'][i].strip()
    conf = int(ocr_data['conf'][i])
    height = ocr_data['height'][i]
    top = ocr_data['top'][i]
    bottom = top + height

    # Skip empty text or low confidence
    if not text or conf < 50:
        continue

    # Skip lines that look like data (emails, numbers, etc.)
    if '@' in text or re.search(r'\d', text):
        continue

    # Merge lines close to each other
    if last_bottom is not None and abs(top - last_bottom) < 10:
        buffer_line += " " + text
    else:
        if buffer_line:
            fields.append(buffer_line.strip())
        buffer_line = text

    last_bottom = bottom

# Append the last buffered line
if buffer_line:
    fields.append(buffer_line.strip())

# Optional: Clean unwanted characters like '*', ':'
cleaned_fields = []
for f in fields:
    f_clean = re.sub(r'[^A-Za-z0-9 ?]', '', f)  # Keep letters, numbers, spaces, question mark
    if len(f_clean) > 2:  # Filter out short garbage
        cleaned_fields.append(f_clean.strip())

# Remove duplicates while preserving order
final_fields = list(dict.fromkeys(cleaned_fields))

# Save to CSV
df = pd.DataFrame(final_fields, columns=["Field Name"])
csv_output = "extracted_fields.csv"
df.to_csv(csv_output, index=False)

print(f"Extracted {len(final_fields)} fields and saved to {csv_output}")
