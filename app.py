import gradio as gr
import pdfplumber
from docx import Document
from pdf2image import convert_from_path
import pytesseract
import spacy
import re

# Load spaCy
nlp = spacy.load("en_core_web_sm")

# ------------------ CONFIG ------------------
GENERIC_SKILLS = [
    "communication","teamwork","leadership","problem solving",
    "customer service","sql","python","excel",
    "data analysis","sales","marketing","machine learning"
]

JOBS = [
    {"title":"Customer Support Executive","location":"Jaipur",
     "keywords":["chat","support","customer","crm","communication"]},

    {"title":"Data Analyst","location":"Bangalore",
     "keywords":["sql","python","excel","data","analysis"]},

    {"title":"Marketing Executive","location":"Mumbai",
     "keywords":["marketing","campaign","content","sales"]}
]

# ------------------ TEXT EXTRACTION ------------------
def extract_text(file):
    text = ""

    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text()

        # OCR fallback
        if len(text.strip()) < 50:
            images = convert_from_path(file.name)
            for img in images:
                text += pytesseract.image_to_string(img)

    elif file.name.endswith(".docx"):
        doc = Document(file)
        for p in doc.paragraphs:
            text += p.text + "\n"

    return text.strip()

# ------------------ KEYWORDS ------------------
def get_keywords(text):
    doc = nlp(text.lower())
    return set(
        token.text for token in doc
        if token.pos_ in ["NOUN","PROPN"] and len(token.text) > 2
    )

# ------------------ ATS SCORE ------------------
def ats_score(resume, job_keywords):
    resume_words = get_keywords(resume)
    matched = resume_words.intersection(job_keywords)

    score = (len(matched) / max(len(job_keywords),1)) * 100
    return round(score,2), list(matched), list(job_keywords - resume_words)

# ------------------ IMPROVEMENT TIPS ------------------
def improve_tips(missing):
    tips = []
    if missing:
        tips.append("Add these missing keywords naturally: " + ", ".join(missing[:8]))
    tips.append("Use action verbs: Managed, Handled, Improved")
    tips.append("Quantify results (50+ chats/day, 95% CSAT)")
    tips.append("Add Skills & Experience sections clearly")
    return tips

# ------------------ JOB MATCHING ------------------
def job_match(resume):
    results = []
    resume_words = get_keywords(resume)

    for job in JOBS:
        matched = resume_words.intersection(set(job["keywords"]))
        score = round(len(matched)/len(job["keywords"])*100,2)

        results.append({
            "title":job["title"],
            "location":job["location"],
            "score":score,
            "matched":list(matched)
        })

    return sorted(results, key=lambda x:x["score"], reverse=True)

# ------------------ MAIN FUNCTION ------------------
def analyze_resume(file, job_desc):
    resume_text = extract_text(file)

    if len(resume_text) < 50:
        return "❌ Resume text extract nahi ho raha. Image-based PDF ho sakta hai."

    job_keywords = get_keywords(job_desc)
    score, matched, missing = ats_score(resume_text, job_keywords)

    tips = improve_tips(missing)
    jobs = job_match(resume_text)

    output = f"""
ATS SCORE: {score}/100

Matched Keywords:
{matched}

Missing Keywords:
{missing}

IMPROVEMENT TIPS:
- """ + "\n- ".join(tips) + "\n\nTOP JOB MATCHES:\n"

    for j in jobs:
        output += f"\n{j['title']} ({j['location']}) → {j['score']}%\nMatched: {j['matched']}\n"

    return output

# ------------------ GRADIO UI ------------------
app = gr.Interface(
    fn=analyze_resume,
    inputs=[
        gr.File(label="Upload Resume (PDF / DOCX)"),
        gr.Textbox(label="Job Description", lines=5)
    ],
    outputs="text",
    title="OCR + ATS Resume Matcher",
    description="Scans ALL resumes (PDF/DOCX), calculates ATS score, missing keywords, job match & improvement tips"
)

app.launch(server_name="0.0.0.0", server_port=7860)
