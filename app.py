#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
app.py
------
ממשק Streamlit לכלי הסרת התשובות מקבצי PDF.
כל לוגיקת העיבוד נמצאת בקובץ pdf_cleaner.py, והקובץ הזה רק בונה סביבה ממשק ווב.
"""

import io
import os
import tempfile
import zipfile

import streamlit as st

from pdf_cleaner import HAS_FITZ, process_pdf_bytes


st.set_page_config(page_title="Answers Remover", page_icon="📄", layout="centered")

st.title("📄 Answers Remover")
st.caption("הסרת הדגשות/תשובות מקבצי PDF ובניית עמוד סיכום עם התשובות שהוסרו")

if not HAS_FITZ:
    st.warning(
        "החבילה PyMuPDF (fitz) לא מותקנת - לא ניתן יהיה לייצר עמוד סיכום עם תמונות של התשובות שהוסרו. "
        "העיבוד עצמו (הסרת ההדגשות) עדיין יעבוד כרגיל."
    )

uploaded_files = st.file_uploader(
    "בחרו קובץ PDF אחד או יותר",
    type=["pdf"],
    accept_multiple_files=True,
)

extract_answers = st.checkbox(
    "לחלץ את התשובות שהודגשו לעמוד סיכום בסוף הקובץ",
    value=True,
    disabled=not HAS_FITZ,
)

process_clicked = st.button("עבד קבצים", type="primary", disabled=not uploaded_files)

if process_clicked and uploaded_files:
    results = []  # (output_filename, bytes)
    progress_bar = st.progress(0)
    status_placeholder = st.empty()

    def status_callback(message):
        status_placeholder.info(message)

    total = len(uploaded_files)

    for i, uploaded_file in enumerate(uploaded_files):
        status_callback(f"מעבד קובץ {i + 1} מתוך {total}: {uploaded_file.name}")

        # fitz צריך לקרוא מנתיב בדיסק, ולכן שומרים את הקובץ שהועלה זמנית
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            output_bytes = process_pdf_bytes(
                tmp_path,
                extract_answers=extract_answers,
                status_callback=status_callback,
            )
            output_name = "SCRAPED_" + uploaded_file.name
            results.append((output_name, output_bytes))
        except Exception as e:
            st.error(f"שגיאה בעיבוד הקובץ {uploaded_file.name}: {e}")
        finally:
            os.remove(tmp_path)

        progress_bar.progress((i + 1) / total)

    status_callback("התהליך הסתיים בהצלחה!")
    st.success(f"עובדו {len(results)} מתוך {total} קבצים בהצלחה.")

    if results:
        st.subheader("הורדת הקבצים")

        # הורדה בודדת לכל קובץ
        for output_name, output_bytes in results:
            st.download_button(
                label=f"⬇️ הורד {output_name}",
                data=output_bytes,
                file_name=output_name,
                mime="application/pdf",
                key=output_name,
            )

        # אם יש יותר מקובץ אחד - מציעים גם הורדת ZIP מרוכז
        if len(results) > 1:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for output_name, output_bytes in results:
                    zip_file.writestr(output_name, output_bytes)
            zip_buffer.seek(0)

            st.download_button(
                label="⬇️ הורד הכל כ-ZIP",
                data=zip_buffer,
                file_name="scraped_pdfs.zip",
                mime="application/zip",
            )

st.divider()

st.caption(
    """
שימו לב, האפליקציה מסירה אובייקטים מעוצבים שיובאו מוורד,
ולכן יש סיכוי שתסיר גם טבלאות ואלמנטים עיצוביים אחרים, אם קיימים.

בסוף כל קובץ תתווסף עמוד תיעוד עם רשימת התשובות שהודגשו, לפי סדר הופעתן,
כדי שיהיה ניתן לשייך כל תשובה לשאלה המתאימה.

וזיכרו: הפתרון הטוב ביותר יהיה לשלוח מייל חביב למתרגל האחראי לאחר המבחן
ולבקש ממנו להעלות גם גרסה ללא הפתרונות למען הסמסטרים הבאים.

בהצלחה!
"""
)
