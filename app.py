import gradio as gr
import pdfplumber
from docx import Document
from pdf2image import convert_from_path
import pytesseract
import spacy
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile

nlp = spacy.load("en_core_web_sm")

# ---------------- CONFIG ----------------
GENERIC_SKILLS = [
    "communication","teamwork","leadership","customer service",
    "problem solving","sql","python","excel","data analysis",
    "sales","marketing"
]

JOBS = [
    {"title":"Customer Support Executive","location":"Jaipur",
     "keywords":["chat","support","customer","crm","communication"]},

    {"title":"Data Analyst","location":"Bangalore",
     "keywords":["sql","python","excel","data","analysis"]},

    {"title":"Marketing Executive","location":"Mumbai",
     "keywords":["marketing","campaign","content","sales"]}
]

# ---------------- TEXT EXTRACTION ----------------
def extract_text(file):
    text = ""

    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text()

        # OCR fallback for scanned PDFs
        if len(text.strip()) < 50:
            images = convert_from_path(file.name)
            for img in images:
                text += pytesseract.image_to_string(img)

    elif file.name.endswith(".docx"):
        doc = Document(file)
        for p in doc.paragraphs:
            text += p.text + "\n"

    return text.strip()

# ---------------- NLP ----------------
def keywords(text):
    doc = nlp(text.lower())
    return set(t.text for t in doc if t.pos_ in ["NOUN","PROPN"] and len(t.text) > 2)

# ---------------- ATS ----------------
def ats_score(resume, job_desc):
    job_keys = keywords(job_desc)
    resume_keys = keywords(resume)

    matched = resume_keys & job_keys
    missing = job_keys - resume_keys

    score = round((len(matched)/max(len(job_keys),1))*100,2)
    return score, list(matched), list(missing)

# ---------------- AI RESUME REWRITE ----------------
def rewrite_resume(resume):
    lines = resume.split("\n")
    improved = []

    for l in lines:
        if len(l.strip()) > 30:
            improved.append(f"• Achieved impact by {l.strip()}")
    return "\n".join(improved[:8])

# ---------------- JOB MATCH ----------------
def job_match(resume):
    resume_keys = keywords(resume)
    results = []

    for job in JOBS:
        m = resume_keys & set(job["keywords"])
        score = round((len(m)/len(job["keywords"]))*100,2)

        results.append(f"{job['title']} ({job['location']}) → {score}%\nMatched: {list(m)}")

    return "\n\n".join(results)

# ---------------- PDF REPORT ----------------
def generate_pdf(report_text):
    path = tempfile.mktemp(".pdf")
    c = canvas.Canvas(path, pagesize=A4)
    text = c.beginText(40, 800)

    for line in report_text.split("\n"):
        text.textLine(line)

    c.drawText(text)
    c.save()
    return path

# ---------------- MAIN ----------------
def analyze(file, job_desc):
    resume = extract_text(file)

    if len(resume) < 50:
        return "❌ Resume extract nahi ho raha", None, None

    score, matched, missing = ats_score(resume, job_desc)
    rewritten = rewrite_resume(resume)
    jobs = job_match(resume)

    report = f"""
ATS SCORE: {score}/100

MATCHED KEYWORDS:
{matched}

MISSING KEYWORDS:
{missing}

AI IMPROVED RESUME POINTS:
{rewritten}

TOP JOB MATCHES:
{jobs}
"""

    pdf = generate_pdf(report)
    return report, rewritten, pdf

# ---------------- UI ----------------
app = gr.Interface(
    fn=analyze,
    inputs=[
        gr.File(label="Upload Resume (PDF/DOCX)"),
        gr.Textbox(label="Job Description", lines=5)
    ],
    outputs=[
        gr.Textbox(label="ATS + Job Match Report"),
        gr.Textbox(label="AI Resume Rewrite"),
        gr.File(label="Download ATS PDF")
    ],
    title="AI Resume ATS Scanner + Improvement Tool",
    description="Scans ALL resumes, calculates ATS score, rewrites resume, shows job matches & downloadable PDF"
)

app.launch(server_name="0.0.0.0", server_port=7860)
