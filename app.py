import gradio as gr
import pdfplumber
from docx import Document
from pdf2image import convert_from_path
import pytesseract
import spacy
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Generic skills
GENERIC_SKILLS = [
    "communication","teamwork","leadership","customer service",
    "problem solving","sql","python","excel","data analysis",
    "sales","marketing"
]

# Sample job database
JOBS = [
    {"title":"Customer Support Executive","location":"Jaipur",
     "keywords":["chat","support","customer","crm","communication"]},

    {"title":"Data Analyst","location":"Bangalore",
     "keywords":["sql","python","excel","data","analysis"]},

    {"title":"Marketing Executive","location":"Mumbai",
     "keywords":["marketing","campaign","content","sales"]}
]

# ------------------ Text Extraction ------------------
def extract_text(file):
    text = ""
    fname = file.name if hasattr(file, "name") else file

    if fname.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text()

        # OCR fallback for scanned PDFs
        if len(text.strip()) < 50:
            images = convert_from_path(fname)
            for img in images:
                text += pytesseract.image_to_string(img)

    elif fname.endswith(".docx"):
        doc = Document(file)
        for p in doc.paragraphs:
            text += p.text + "\n"

    return text.strip()

# ------------------ NLP Keywords ------------------
def extract_keywords(text):
    doc = nlp(text.lower())
    return set(token.text for token in doc if token.pos_ in ["NOUN","PROPN"] and len(token.text) > 2)

# ------------------ ATS Score ------------------
def calculate_ats(resume, job_desc):
    job_keys = extract_keywords(job_desc)
    resume_keys = extract_keywords(resume)

    matched = resume_keys & job_keys
    missing = job_keys - resume_keys
    score = round((len(matched)/max(len(job_keys),1))*100,2)
    return score, list(matched), list(missing)

# ------------------ AI Resume Improvement ------------------
def improve_resume(resume):
    lines = resume.split("\n")
    improved = []
    for l in lines:
        if len(l.strip()) > 30:
            improved.append(f"• Achieved impact by {l.strip()}")
    return "\n".join(improved[:8])

# ------------------ Job Matching ------------------
def match_jobs(resume):
    resume_keys = extract_keywords(resume)
    results = []
    for job in JOBS:
        matched = resume_keys & set(job["keywords"])
        score = round((len(matched)/len(job["keywords"]))*100,2)
        results.append(f"{job['title']} ({job['location']}) → {score}%\nMatched: {list(matched)}")
    return "\n\n".join(results)

# ------------------ PDF Report ------------------
def generate_pdf(text):
    path = tempfile.mktemp(".pdf")
    c = canvas.Canvas(path, pagesize=A4)
    txt = c.beginText(40, 800)
    for line in text.split("\n"):
        txt.textLine(line)
    c.drawText(txt)
    c.save()
    return path

# ------------------ Main Analysis ------------------
def analyze_resume(file, job_desc):
    resume_text = extract_text(file)
    if len(resume_text) < 50:
        return "❌ Resume extract nahi ho raha.", None, None

    score, matched, missing = calculate_ats(resume_text, job_desc)
    improved = improve_resume(resume_text)
    jobs = match_jobs(resume_text)

    report = f"""
ATS SCORE: {score}/100

MATCHED KEYWORDS:
{matched}

MISSING KEYWORDS:
{missing}

AI IMPROVED RESUME POINTS:
{improved}

TOP JOB MATCHES:
{jobs}
"""

    pdf_path = generate_pdf(report)
    return report, improved, pdf_path

# ------------------ Gradio Interface ------------------
iface = gr.Interface(
    fn=analyze_resume,
    inputs=[
        gr.File(label="Upload Resume (PDF/DOCX)"),
        gr.Textbox(label="Job Description", lines=5)
    ],
    outputs=[
        gr.Textbox(label="ATS + Job Match Report"),
        gr.Textbox(label="AI Resume Improvement"),
        gr.File(label="Download ATS PDF Report")
    ],
    title="AI Resume ATS + OCR + Improvement Tool",
    description="Upload any resume (PDF/DOCX) → calculate ATS score, improvement tips, job match & download PDF report"
)

iface.launch(server_name="0.0.0.0", server_port=7860)
