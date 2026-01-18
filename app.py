import gradio as gr
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from docx import Document
import re
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nltk.download("punkt")

# -------------------------------
# Resume Text Extraction
# -------------------------------
def extract_text(file):
    text = ""

    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"

        # OCR fallback
        if len(text.strip()) < 50:
            images = convert_from_bytes(file.read())
            for img in images:
                text += pytesseract.image_to_string(img)

    elif file.name.endswith(".docx"):
        doc = Document(file)
        for p in doc.paragraphs:
            text += p.text + "\n"

    return text.strip()


# -------------------------------
# Location Extraction
# -------------------------------
def extract_location(text):
    locations = [
        "Delhi", "Mumbai", "Bangalore", "Hyderabad",
        "Chennai", "Pune", "Jaipur", "Noida", "Gurgaon",
        "Rajasthan", "Karnataka", "Maharashtra"
    ]
    for loc in locations:
        if loc.lower() in text.lower():
            return loc
    return "Not Mentioned"


# -------------------------------
# ATS & Job Matching
# -------------------------------
def ats_analyze(resume, job_desc):
    resume = resume.lower()
    job_desc = job_desc.lower()

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume, job_desc])

    score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    ats_score = round(score * 100, 2)

    job_words = set(job_desc.split())
    resume_words = set(resume.split())

    matched = job_words & resume_words
    missing = job_words - resume_words

    return ats_score, matched, missing


# -------------------------------
# Resume Improvement
# -------------------------------
def improve_resume(missing):
    tips = [
        "Add missing job-specific keywords naturally in your experience section.",
        "Quantify achievements (example: resolved 50+ tickets daily).",
        "Add technical tools, soft skills, and certifications.",
        "Use strong action verbs and bullet points."
    ]

    improved = "IMPROVEMENT SUGGESTIONS:\n"
    for t in tips:
        improved += "- " + t + "\n"

    return improved


# -------------------------------
# Job Recommendations
# -------------------------------
def recommend_jobs(resume_text):
    jobs = [
        ("Customer Support Executive", "Jaipur"),
        ("Data Analyst", "Bangalore"),
        ("HR Executive", "Delhi"),
        ("Marketing Executive", "Mumbai"),
        ("Sales Executive", "Noida")
    ]

    recommendations = []
    for job, loc in jobs:
        recommendations.append(f"{job} ({loc})")

    return "\n".join(recommendations)


# -------------------------------
# Main App Logic
# -------------------------------
def analyze(resume_file, job_desc):
    resume_text = extract_text(resume_file)

    if not resume_text:
        return "❌ Resume text could not be extracted."

    location = extract_location(resume_text)
    ats_score, matched, missing = ats_analyze(resume_text, job_desc)
    improvements = improve_resume(missing)
    jobs = recommend_jobs(resume_text)

    clean_resume = resume_text.replace("\n", " ")

    output = f"""
ATS SCORE: {ats_score}/100

Location Detected: {location}

Matched Keywords:
{', '.join(list(matched)) if matched else 'None'}

Missing Keywords:
{', '.join(list(missing)) if missing else 'None'}

{improvements}

TOP JOB MATCHES:
{jobs}

IMPROVED RESUME TEXT:
{clean_resume}
"""

    return output


# -------------------------------
# Gradio UI
# -------------------------------
app = gr.Interface(
    fn=analyze,
    inputs=[
        gr.File(label="Upload Resume (PDF/DOCX)"),
        gr.Textbox(label="Job Description", lines=5)
    ],
    outputs=gr.Textbox(label="ATS Analysis Report", lines=30),
    title="ResumeIQ – ATS & Job Match Analyzer",
    description="Upload resume & job description to get ATS score, missing skills, job matches, and improvement tips."
)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=8080)
