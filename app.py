import os
import re
import gradio as gr
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Clean text
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

# OCR fallback for scanned PDF
def ocr_pdf(pdf_bytes):
    text = ""
    try:
        images = convert_from_bytes(pdf_bytes)
        for img in images:
            text += pytesseract.image_to_string(img)
    except Exception:
        pass
    return text

# Extract text from resumes
def extract_resume_text(file):
    text = ""

    try:
        if file.name.endswith(".pdf"):
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + " "

            if len(text.strip()) < 50:
                pdf_bytes = file.read()
                text = ocr_pdf(pdf_bytes)

        elif file.name.endswith(".docx"):
            doc = Document(file)
            for p in doc.paragraphs:
                text += p.text + " "
    except:
        return ""

    return text.strip()

# Extract location
LOCATIONS = [
    "delhi","mumbai","bangalore","hyderabad","chennai",
    "pune","kolkata","jaipur","ahmedabad","noida","gurgaon"
]

def extract_location(text):
    for loc in LOCATIONS:
        if loc in text.lower():
            return loc.title()
    return "Not Mentioned"

# ATS scoring
def calculate_ats(resume, jd):
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume, jd])
    score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0] * 100

    resume_words = set(resume.split())
    jd_words = set(jd.split())

    matched = resume_words.intersection(jd_words)
    missing = jd_words - resume_words

    return round(score,2), matched, missing

# Suggested improvements
def improvement_suggestions(missing):
    tips = []
    if missing:
        tips.append("Add key job-specific terms from the description.")
    tips.append("Quantify experience using numbers (e.g., 50+ chats/day).")
    tips.append("Add strong skills and tools sections.")
    return tips

# Simple job recommendations
JOBS = [
    ("Customer Support Executive","Jaipur"),
    ("Data Analyst","Bangalore"),
    ("HR Executive","Delhi"),
    ("Marketing Executive","Mumbai"),
    ("Sales Executive","Noida")
]

def recommend_jobs(score, location):
    recs = []
    for job, loc in JOBS:
        loc_score = 10 if location.lower() in loc.lower() else 0
        rec = round(score*0.6 + loc_score,2)
        recs.append(f"{job} ({loc}) – Match: {rec}%")
    return "\n".join(recs)

# Main analyzer
def analyze_resume(file, job_desc):
    if not file or not job_desc.strip():
        return "❌ Upload resume AND job description.", "", ""

    text = extract_resume_text(file)
    if not text:
        return "❌ Could not extract text from resume.", "", ""

    clean_resume = clean_text(text)
    clean_jd = clean_text(job_desc)

    score, matched, missing = calculate_ats(clean_resume, clean_jd)
    location = extract_location(text)
    tips = improvement_suggestions(missing)

    result = (
        f"ATS Score: {score}/100\n"
        f"Location: {location}\n"
        f"Matched: {list(matched)[:15]}\n"
        f"Missing: {list(missing)[:15]}\n\n"
        "Suggestions:\n" + "\n".join(tips)
    )

    jobs = recommend_jobs(score, location)

    return result, jobs, "\n".join(tips)

# Gradio UI
ui = gr.Interface(
    fn=analyze_resume,
    inputs=[
        gr.File(label="Upload Resume (PDF / DOCX / Scanned PDF)"),
        gr.Textbox(label="Job Description", lines=4)
    ],
    outputs=[
        gr.Textbox(label="ATS Report"),
        gr.Textbox(label="Job Recommendations"),
        gr.Textbox(label="Tips")
    ],
    title="ResumeIQ – ATS Resume Analyzer",
    description="Upload any resume and job description to get ATS score, job recommendations and improvement tips."
)

ui.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860))
)
