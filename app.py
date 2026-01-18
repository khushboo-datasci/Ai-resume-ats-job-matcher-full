import gradio as gr
import pdfplumber
import pytesseract
from PIL import Image
import docx
import re
from sklearn.feature_extraction.text import TfidfVectorizer

# ---------- TEXT EXTRACTION ----------
def extract_text(file):
    text = ""

    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

                # OCR fallback
                img = page.to_image(resolution=300).original
                text += pytesseract.image_to_string(img)

    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + " "

    return text.strip()


# ---------- ATS LOGIC ----------
def ats_score(resume_text, jd_text):
    resume_text = resume_text.lower()
    jd_text = jd_text.lower()

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform([resume_text, jd_text])

    score = (tfidf * tfidf.T).A[0][1] * 100
    score = round(score, 2)

    keywords = set(vectorizer.get_feature_names_out())
    resume_words = set(resume_text.split())
    matched = keywords & resume_words
    missing = keywords - resume_words

    return score, list(matched)[:20], list(missing)[:20]


# ---------- MAIN FUNCTION ----------
def process(resume, jd, location):
    resume_text = extract_text(resume)

    if not resume_text:
        return "❌ Resume text extract nahi ho raha", "", "", ""

    score, matched, missing = ats_score(resume_text, jd)

    tips = """
• Job description ke keywords add karo  
• Skills section strong banao  
• Action verbs use karo  
• Location mention karo  
"""

    return (
        f"{score}/100",
        ", ".join(matched),
        ", ".join(missing),
        f"Suggested Location Match: {location}\n\nTips:\n{tips}"
    )


# ---------- GRADIO UI ----------
ui = gr.Interface(
    fn=process,
    inputs=[
        gr.File(label="Upload Resume (PDF/DOCX)"),
        gr.Textbox(label="Job Description", lines=5),
        gr.Textbox(label="Preferred Job Location")
    ],
    outputs=[
        gr.Textbox(label="ATS Score"),
        gr.Textbox(label="Matched Keywords"),
        gr.Textbox(label="Missing Keywords"),
        gr.Textbox(label="Improvement & Location")
    ],
    title="OCR + ATS Resume Scanner",
    description="Scans ALL resumes (PDF/DOCX), calculates ATS score, keywords, OCR support & location match"
)

ui.launch(server_name="0.0.0.0", server_port=7860)
