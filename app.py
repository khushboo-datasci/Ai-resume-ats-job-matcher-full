import gradio as gr
import pdfplumber
from docx import Document
import re

# ---------------- SKILLS ----------------
GENERIC_SKILLS = [
    "communication","teamwork","leadership","problem solving","critical thinking",
    "time management","adaptability","creativity","customer service",
    "sales","marketing","python","sql","excel","machine learning","data analysis"
]

JOBS = [
    {"title":"Customer Support Executive","description":"chat support customer service communication","location":"Jaipur"},
    {"title":"Marketing Executive","description":"marketing content communication reporting","location":"Mumbai"},
    {"title":"Data Analyst","description":"data analysis python sql excel","location":"Bangalore"},
    {"title":"Sales Executive","description":"sales communication crm","location":"Jaipur"}
]

# ---------------- TEXT EXTRACTION ----------------
def extract_text_resume(file):
    text = ""
    name = file.name.lower()

    try:
        if name.endswith(".pdf"):
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + " "
        elif name.endswith(".docx"):
            doc = Document(file)
            for p in doc.paragraphs:
                text += p.text + " "
    except:
        pass

    return text.lower().strip()

# ---------------- CLEAN + KEYWORDS ----------------
def clean(text):
    return re.sub(r'[^a-zA-Z0-9 ]', '', text.lower())

def keywords(text):
    return set(clean(text).split())

# ---------------- ATS LOGIC ----------------
def ats_score(resume_text, job_text):
    resume_kw = keywords(resume_text)
    job_kw = keywords(job_text)

    matched = resume_kw & job_kw

    skill_match = [s for s in GENERIC_SKILLS if s in resume_text]

    score = (
        (len(matched)/max(len(job_kw),1))*60 +
        (len(skill_match)/len(GENERIC_SKILLS))*40
    )

    return round(score,2), matched, skill_match, list(job_kw-resume_kw)

# ---------------- MAIN ----------------
def run(resume_file, job_desc, location):
    resume_text = extract_text_resume(resume_file)

    if len(resume_text) < 50:
        return "❌ Resume text extract nahi ho raha.\nPDF scanned ho sakta hai.\nTry text-based PDF/DOCX."

    score, matched, skills, missing = ats_score(resume_text, job_desc)

    result = f"""
ATS Score: {score}/100

Matched Keywords:
{matched}

Matched Skills:
{skills}

Missing Keywords:
{missing[:15]}

Top Job Matches:
"""

    for j in JOBS:
        s,_,_,_ = ats_score(resume_text, j["description"])
        if location and location.lower() not in j["location"].lower():
            s *= 0.7
        result += f"\n• {j['title']} ({j['location']}) → {round(s,2)}"

    return result

# ---------------- UI ----------------
gr.Interface(
    fn=run,
    inputs=[
        gr.File(label="Upload Resume (PDF/DOCX)"),
        gr.Textbox(label="Job Description"),
        gr.Textbox(label="Preferred Location (optional)")
    ],
    outputs="text",
    title="ATS Resume Scanner",
    description="Public ATS Resume Scanner (Cloud Safe Version)"
).launch(server_name="0.0.0.0", server_port=8080)
