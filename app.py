import os, re, tempfile
import gradio as gr
import pdfplumber, pytesseract
from pdf2image import convert_from_path
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# -----------------------------
# Utilities
# -----------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# -----------------------------
# OCR
# -----------------------------
def ocr_pdf(path):
    text = ""
    images = convert_from_path(path)
    for img in images:
        text += pytesseract.image_to_string(img)
    return text


# -----------------------------
# Resume Text Extraction
# -----------------------------
def extract_resume_text(file):
    text = ""

    if file.name.endswith(".pdf"):
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    if page.extract_text():
                        text += page.extract_text() + " "
        except:
            pass

        if len(text.strip()) < 50:
            text = ocr_pdf(file.name)

    elif file.name.endswith(".docx"):
        doc = Document(file)
        for p in doc.paragraphs:
            text += p.text + " "

    return text.strip()


# -----------------------------
# Location Extraction
# -----------------------------
LOCATIONS = [
    "delhi","mumbai","bangalore","hyderabad","chennai",
    "pune","kolkata","jaipur","ahmedabad","noida","gurgaon"
]

def extract_location(text):
    for loc in LOCATIONS:
        if loc in text:
            return loc.title()
    return "Not Mentioned"


# -----------------------------
# ATS Score
# -----------------------------
def calculate_ats(resume, jd):
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume, jd])
    score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0] * 100

    resume_words = set(resume.split())
    jd_words = set(jd.split())

    return round(score, 2), resume_words & jd_words, jd_words - resume_words


# -----------------------------
# AI Resume Rewrite (Offline)
# -----------------------------
def ai_rewrite_resume(text):
    lines = text.split("\n")
    improved = []
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue
        line = line.replace("Responsible for", "Successfully handled")
        line = line.replace("Worked on", "Contributed to")
        line = line.replace("Helped", "Assisted and improved")
        improved.append("• " + line if len(line.split()) > 5 else line)
    return "\n".join(improved)


# -----------------------------
# Job Recommendations
# -----------------------------
JOBS = [
    ("Customer Support Executive", "Jaipur"),
    ("Data Analyst", "Bangalore"),
    ("HR Executive", "Delhi"),
    ("Marketing Executive", "Mumbai"),
    ("Sales Executive", "Noida")
]

def recommend_jobs(score, location):
    results = []
    for job, loc in JOBS:
        loc_score = 15 if location.lower() in loc.lower() else 0
        results.append(f"{job} ({loc}) — Match Score: {round(score*0.7+loc_score,2)}")
    return "\n".join(results)


# -----------------------------
# PDF Generator
# -----------------------------
def generate_pdf(text):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp.name, pagesize=A4)
    width, height = A4
    y = height - 40

    for line in text.split("\n"):
        if y < 40:
            c.showPage()
            y = height - 40
        c.drawString(40, y, line[:100])
        y -= 14

    c.save()
    return temp.name


# -----------------------------
# Main Function
# -----------------------------
def analyze_resume(resume_file, jd):
    if not resume_file or not jd.strip():
        return "❌ Upload resume & job description", "", "", None

    resume = extract_resume_text(resume_file)
    if len(resume) < 50:
        return "❌ Resume text could not be extracted", "", "", None

    resume_c = clean_text(resume)
    jd_c = clean_text(jd)

    score, matched, missing = calculate_ats(resume_c, jd_c)
    location = extract_location(resume_c)

    tips = []
    if score < 40:
        tips.append("Add more job-specific keywords from the job description.")
    if score < 60:
        tips.append("Quantify your experience with measurable results.")
    if score < 80:
        tips.append("Strengthen your skills section with relevant keywords.")
    if score >= 80:
        tips.append("Your resume is ATS-friendly and optimized.")

    rewritten = ai_rewrite_resume(resume)
    final_resume = rewritten + "\n\nIMPROVEMENT SUGGESTIONS:\n- " + "\n- ".join(tips)

    pdf_path = generate_pdf(final_resume)

    result = f"""
### ✅ ATS Score: {score}/100
**📍 Location Detected:** {location}

**✔ Matched Keywords:** {list(matched)[:15]}  
**❌ Missing Keywords:** {list(missing)[:15]}

### ✍ Suggestions:
- {"\n- ".join(tips)}
"""

    return result, recommend_jobs(score, location), final_resume, pdf_path


# -----------------------------
# UI
# -----------------------------
ui = gr.Interface(
    fn=analyze_resume,
    inputs=[
        gr.File(label="Upload Resume (PDF / DOCX / Scanned PDF)"),
        gr.Textbox(label="Job Description", lines=6)
    ],
    outputs=[
        gr.Markdown(label="ATS Analysis"),
        gr.Textbox(label="Job Recommendations", lines=6),
        gr.Textbox(label="AI Rewritten Resume", lines=25),
        gr.File(label="Download Improved Resume (PDF)")
    ],
    title="ResumeIQ – AI ATS Resume Scanner & Improver",
    description="Scan any resume • ATS score • AI rewrite • Job match • PDF download"
)

# -----------------------------
# Railway Compatible Launch
# -----------------------------
ui.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860))
)
