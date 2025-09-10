# -------------------- OCR Table Extraction --------------------
with col2:
    if st.button("Table Extraction to Word/CSV (Tables)"):
        uploaded_file.seek(0)
        extracted_records = []
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                all_tables = []
                for page_num, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    for tidx, table in enumerate(tables, start=1):
                        all_tables.append((page_num, tidx, table))

            if not all_tables:
                st.warning("⚠️ No tables found in this PDF.")
            else:
                st.success(f"✅ Found {len(all_tables)} tables!")

                for page_num, tidx, table in all_tables:
                    st.write(f"### Table {tidx} (Page {page_num})")
                    df_preview = pd.DataFrame(table)
                    st.dataframe(df_preview)

                    # Let user choose rows for fields/values
                    field_row = st.number_input(
                        f"Select field row for Table {tidx} (Page {page_num})",
                        min_value=0, max_value=len(table)-1, value=1, step=1
                    )
                    value_row = st.number_input(
                        f"Select value row for Table {tidx} (Page {page_num})",
                        min_value=0, max_value=len(table)-1, value=2, step=1
                    )

                    if st.button(f"Extract Table {tidx} (Page {page_num})"):
                        fields = table[field_row]
                        values = table[value_row]
                        record = {}
                        for f, v in zip(fields, values):
                            if f and v:
                                record[str(f).strip()] = str(v).strip()
                        if record:
                            extracted_records.append(record)
                            st.success(f"✅ Extracted {len(record)} fields from Table {tidx} (Page {page_num})")
                            st.json(record)

            # Once done, let user download
            if extracted_records:
                df = pd.DataFrame(extracted_records)
                st.write("### Final Extracted Data")
                st.dataframe(df)

                # Save to Word
                doc = Document()
                doc.add_heading("Extracted Table Data", level=1)
                for idx, record in enumerate(extracted_records, start=1):
                    doc.add_heading(f"Record {idx}", level=2)
                    table = doc.add_table(rows=1, cols=2)
                    hdr_cells = table.rows[0].cells
                    hdr_cells[0].text = "Field"
                    hdr_cells[1].text = "Value"
                    for field, value in record.items():
                        row_cells = table.add_row().cells
                        row_cells[0].text = str(field)
                        row_cells[1].text = str(value)
                    doc.add_paragraph()

                word_bytes = BytesIO()
                doc.save(word_bytes)
                word_bytes.seek(0)

                st.download_button(
                    "📥 Download Word Document",
                    data=word_bytes,
                    file_name="ocr_extraction.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

                csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")
                st.download_button(
                    "📥 Download CSV",
                    data=csv_bytes,
                    file_name="ocr_extraction.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Table extraction failed: {e}")
