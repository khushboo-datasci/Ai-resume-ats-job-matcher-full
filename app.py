import os, re
import gradio as gr
import pdfplumber, pytesseract
from pdf2image import convert_from_path
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -------------------------
# Utils
# -------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# -------------------------
# OCR
# -------------------------
def ocr_pdf(path):
    text = ""
    images = convert_from_path(path)
    for img in images:
        text += pytesseract.image_to_string(img)
    return text


# -------------------------
# Extract Resume Text
# -------------------------
def extract_text(file):
    text = ""

    if file.name.endswith(".pdf"):
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    if page.extract_text():
                        text += page.extract_text() + " "
        except:
            pass

        if len(text) < 50:
            text = ocr_pdf(file.name)

    elif file.name.endswith(".docx"):
        doc = Document(file)
        for p in doc.paragraphs:
            text += p.text + " "

    return text


# -------------------------
# Location Extraction
# -------------------------
LOCATIONS = [
    "delhi","mumbai","bangalore","hyderabad","chennai",
    "pune","kolkata","jaipur","ahmedabad","noida","gurgaon"
]

def extract_location(text):
    for loc in LOCATIONS:
        if loc in text:
            return loc.title()
    return "Not Found"


# -------------------------
# ATS Score
# -------------------------
def ats_score(resume, jd):
    vectorizer = TfidfVectorizer(stop_words="english")
    vec = vectorizer.fit_transform([resume, jd])
    score = cosine_similarity(vec[0:1], vec[1:2])[0][0] * 100

    resume_words = set(resume.split())
    jd_words = set(jd.split())

    matched = resume_words & jd_words
    missing = jd_words - resume_words

    return round(score,2), matched, missing


# -------------------------
# Job Recommendation
# -------------------------
JOBS = [
    ("Customer Support Executive","Jaipur"),
    ("Data Analyst","Bangalore"),
    ("HR Executive","Delhi"),
    ("Marketing Executive","Mumbai"),
    ("Sales Executive","Noida")
]

def recommend_jobs(score, location):
    rec = []
    for job, loc in JOBS:
        match = 10 if location.lower() in loc.lower() else 0
        rec.append(f"{job} ({loc}) - Match Score: {round(score*0.6+match,2)}")
    return "\n".join(rec)


# -------------------------
# MAIN FUNCTION
# -------------------------
def analyze(resume_file, jd):
    if not resume_file or jd.strip()=="":
        return "❌ Upload resume & JD both", "", ""

    resume = extract_text(resume_file)
    if len(resume) < 50:
        return "❌ Resume read nahi ho raha", "", ""

    resume_c = clean_text(resume)
    jd_c = clean_text(jd)

    score, matched, missing = ats_score(resume_c, jd_c)
    location = extract_location(resume_c)

    tips = []
    if score < 40: tips.append("Job keywords add karo")
    if score < 60: tips.append("Experience quantify karo")
    if score < 80: tips.append("Skills improve karo")
    if score >= 80: tips.append("Resume ATS friendly hai ✅")

    improved_resume = resume + "\n\nIMPROVEMENT SUGGESTIONS:\n- " + "\n- ".join(tips)

    return (
        f"""
### ✅ ATS Score: {score}/100
**Location Found:** {location}

**Matched Keywords:** {list(matched)[:15]}  
**Missing Keywords:** {list(missing)[:15]}

### ✍ Tips:
- {' | '.join(tips)}
""",
        recommend_jobs(score, location),
        improved_resume
    )


# -------------------------
# UI
# -------------------------
ui = gr.Interface(
    fn=analyze,
    inputs=[
        gr.File(label="Upload Resume (PDF / DOCX / Scanned PDF)"),
        gr.Textbox(label="Job Description", lines=6)
    ],
    outputs=[
        gr.Markdown(label="ATS Result"),
        gr.Textbox(label="Job Recommendations"),
        gr.Textbox(label="Improved Resume Text (Download / Copy)")
    ],
    title="AI OCR + ATS Resume Scanner",
    description="All resume types | Location | ATS | Jobs | Improvements"
)

# -------------------------
# RAILWAY FIX
# -------------------------
ui.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT",7860))
)
