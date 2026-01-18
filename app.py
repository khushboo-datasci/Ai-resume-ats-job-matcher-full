import gradio as gr
import pdfplumber
from docx import Document
from pdf2image import convert_from_bytes
import pytesseract
import spacy
import io
import re
from difflib import get_close_matches

# -------------------- LOAD NLP MODEL --------------------
nlp = spacy.load("en_core_web_sm")

# -------------------- GENERIC SKILLS --------------------
GENERIC_SKILLS = [
    "communication","teamwork","leadership","problem solving","time management",
    "adaptability","customer service","chat support","email support","crm",
    "python","sql","excel","data analysis","sales","marketing"
]

# -------------------- SAMPLE JOB DATABASE --------------------
JOBS = [
    {"title": "Customer Support Executive", "location": "Jaipur", "skills": ["customer","chat","support","crm"]},
    {"title": "Data Analyst", "location": "Bangalore", "skills": ["data","sql","python","analysis"]},
    {"title": "HR Executive", "location": "Delhi", "skills": ["recruitment","communication","hr"]},
    {"title": "Marketing Executive", "location": "Mumbai", "skills": ["marketing","campaign","content"]},
    {"title": "Sales Executive", "location": "Noida", "skills": ["sales","client","crm"]}
]

# -------------------- RESUME TEXT EXTRACTION (FINAL FIX) --------------------
def extract_resume_text(file):
    text = ""

    try:
        if file.name.endswith(".pdf"):
            pdf_bytes = file.read()

            # Text based PDF
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + " "

            # OCR fallback
            if len(text.strip()) < 50:
                images = convert_from_bytes(pdf_bytes)
                for img in images:
                    text += pytesseract.image_to_string(img)

        elif file.name.endswith(".docx"):
            doc = Document(file)
            for p in doc.paragraphs:
                text += p.text + " "

    except Exception as e:
        print("Resume extraction error:", e)
        return ""

    return text.strip()

# -------------------- NLP KEYWORDS --------------------
def extract_keywords(text):
    doc = nlp(text.lower())
    return list(set([t.text for t in doc if t.pos_ in ["NOUN","PROPN"] and len(t.text) > 2]))

# -------------------- LOCATION EXTRACTION --------------------
def extract_location(text):
    cities = ["jaipur","delhi","bangalore","mumbai","noida","pune","hyderabad","chennai"]
    for city in cities:
        if city in text.lower():
            return city.title()
    return "Not mentioned"

# -------------------- ATS SCORE --------------------
def calculate_ats(resume_text, jd):
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd)

    matched = get_close_matches(" ".join(jd_keywords), resume_keywords, cutoff=0.4)

    keyword_score = min(len(set(resume_keywords) & set(jd_keywords)) * 3, 40)
    skill_score = min(sum(1 for s in GENERIC_SKILLS if s in resume_text.lower()) * 2, 30)
    length_score = 30 if len(resume_text.split()) > 150 else 15

    return keyword_score + skill_score + length_score

# -------------------- JOB MATCHING --------------------
def resume_ai_app(resume, job_description):
    resume_text = extract_resume_text(resume)

    if len(resume_text) < 30:
        return "❌ Could not extract text from resume."

    ats = calculate_ats(resume_text, job_description)
    location = extract_location(resume_text)
    jobs = recommend_jobs(resume_text)   
    tips = improvement_tips()

    return f"""
ATS Score: {ats}/100

Detected Location: {location}

IMPROVEMENT SUGGESTIONS:
- {tips[0]}
- {tips[1]}
- {tips[2]}

JOB RECOMMENDATIONS:
{jobs}
"""

# -------------------- IMPROVEMENT TIPS --------------------
def improvement_tips():
    return [
        "Add more job-specific keywords",
        "Quantify experience with numbers",
        "Improve skills section with tools & platforms"
    ]

# -------------------- GRADIO FUNCTION --------------------
def resume_ai_app(resume, job_description):
    resume_text = extract_resume_text(resume)

    if len(resume_text) < 30:
        return "❌ Could not extract text from resume."

    ats = calculate_ats(resume_text, job_description)
    location = extract_location(resume_text)
    jobs = recommend_jobs(resume_text)
    tips = improvement_tips()

    return f"""
ATS Score: {ats}/100

Detected Location: {location}

IMPROVEMENT SUGGESTIONS:
- {tips[0]}
- {tips[1]}
- {tips[2]}

JOB RECOMMENDATIONS:
{jobs}
"""

# -------------------- GRADIO UI --------------------
iface = gr.Interface(
    fn=resume_ai_app,
    inputs=[
        gr.File(label="Upload Resume (PDF/DOCX)"),
        gr.Textbox(label="Job Description")
    ],
    outputs="text",
    title="ResumeLens AI – ATS Resume Scanner & Job Matcher",
    description="Upload your resume to get ATS score, job matches, improvement tips & location detection."
)

iface.launch(server_name="0.0.0.0", server_port=7860)

jobs = recommend_jobs(resume_text)

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
