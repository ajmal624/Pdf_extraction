import streamlit as st 

from PyPDF2 import PdfReader 

import requests 

import os 

 


HF_API_KEY = st.secrets["HF_API_KEY"]
   # Store in Streamlit Secrets


 

API_URL = "https://api-inference.huggingface.co/models/microsoft/phi-3-mini-4k-instruct" 

 

headers = {"Authorization": f"Bearer {HF_API_KEY}"} 

 

def query(payload): 

    response = requests.post(API_URL, headers=headers, json=payload) 

    return response.json() 

 

st.title("📑 PDF Data Extractor (Open Source Model)") 

 

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"]) 

 

if uploaded_file: 

    # Extract text from PDF 

    pdf_reader = PdfReader(uploaded_file) 

    raw_text = "" 

    for page in pdf_reader.pages: 

        raw_text += page.extract_text() or "" 

 

    st.subheader("Raw Extracted Text") 

    st.text_area("PDF Content", raw_text, height=250) 

 

    task = st.text_input("What do you want to extract? (e.g. 'Summarize this PDF', 'List all dates', 'Extract invoice numbers')") 

 

    if st.button("Process with Open Source Model") and task: 

        with st.spinner("Thinking..."): 

            output = query({ 

                "inputs": f"Task: {task}\n\nPDF Content:\n{raw_text[:3000]}",  # Keep within model context limit 

                "parameters": {"max_new_tokens": 500} 

            }) 

             

            if isinstance(output, dict) and "error" in output: 

                st.error(output["error"]) 

            else: 

                st.subheader("🔎 Extracted Result") 

                st.write(output[0]["generated_text"]) 

 

 

 

 
