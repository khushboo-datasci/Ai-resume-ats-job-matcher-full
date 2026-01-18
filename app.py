import os
import gradio as gr
import pdfplumber
from docx import Document
from pdf2image import convert_from_bytes
import pytesseract
import io
import re
import spacy

# -------------------- TESSERACT PATH --------------------
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# -------------------- LOAD SPACY MODEL --------------------
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

# -------------------- RESUME TEXT EXTRACTION --------------------
def extract_resume_text(file):
    text = ""
    try:
        file_bytes = file.read()

        if file.name.endswith(".pdf"):
            # Try text extraction first
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + " "
            except:
                pass

            # Always run OCR for reliability (scanned + typed)
            images = convert_from_bytes(file_bytes, dpi=300, fmt="ppm")  # ppm fixes Docker PIL issues
            ocr_text = ""
            for img in images:
                ocr_text += pytesseract.image_to_string(img, config="--psm 6")
            if len(ocr_text.strip()) > 0:
                text = ocr_text

        elif file.name.endswith(".docx"):
            doc = Document(io.BytesIO(file_bytes))
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
    keyword_score = min(len(set(resume_keywords) & set(jd_keywords)) * 3, 40)
    skill_score = min(sum(1 for s in GENERIC_SKILLS if s in resume_text.lower()) * 2, 30)
    length_score = 30 if len(resume_text.split()) > 150 else 15
    return keyword_score + skill_score + length_score

# -------------------- JOB RECOMMENDATION --------------------
def recommend_jobs(resume_text):
    resume_text_lower = resume_text.lower()
    recommended = []
    for job in JOBS:
        match_count = sum(1 for skill in job["skills"] if skill in resume_text_lower)
        if match_count > 0:
            recommended.append(f"{job['title']} ({job['location']})")
    if not recommended:
        return "No matching jobs found"
    return "\n".join(recommended)

# -------------------- IMPROVEMENT TIPS --------------------
def improvement_tips():
    return [
        "Add more job-specific keywords",
        "Quantify your experience with numbers",
        "Enhance skills section with tools & platforms you know"
    ]

# -------------------- HIGHLIGHT SKILLS --------------------
def highlight_skills(text):
    highlighted_text = text
    for skill in GENERIC_SKILLS:
        highlighted_text = re.sub(
            rf"\b({skill})\b",
            r"**\1**",
            highlighted_text,
            flags=re.IGNORECASE
        )
    return highlighted_text

# -------------------- EXTRACT DETECTED SKILLS --------------------
def extract_detected_skills(text):
    detected = []
    text_lower = text.lower()
    for skill in GENERIC_SKILLS:
        if skill in text_lower:
            detected.append(skill.title())
    if not detected:
        return "No generic skills detected"
    return ", ".join(detected)

# -------------------- MAIN APP FUNCTION --------------------
def resume_ai_app(resume, job_description):
    resume_text = extract_resume_text(resume)
    if len(resume_text) < 30:
        return "❌ Could not extract text from resume.", "", ""
    
    ats = calculate_ats(resume_text, job_description)
    location = extract_location(resume_text)
    jobs = recommend_jobs(resume_text)
    tips = improvement_tips()
    skills_detected = extract_detected_skills(resume_text)
    
    output_text = f"""
ATS Score: {ats}/100

Detected Location: {location}

IMPROVEMENT SUGGESTIONS:
- {tips[0]}
- {tips[1]}
- {tips[2]}

JOB RECOMMENDATIONS:
{jobs}
"""
    output_text = highlight_skills(output_text)
    return output_text, skills_detected, "\n".join(tips)

# -------------------- GRADIO UI --------------------
iface = gr.Interface(
    fn=resume_ai_app,
    inputs=[
        gr.File(label="Upload Resume (PDF/DOCX)"),
        gr.Textbox(label="Job Description", lines=6)
    ],
    outputs=[
        gr.Textbox(label="ATS Report & Job Recommendations", lines=25),
        gr.Textbox(label="Detected Skills"),
        gr.Textbox(label="Improvement Tips")
    ],
    title="ResumeLens AI – ATS Resume Scanner & Job Matcher",
    description="Upload your resume to get ATS score, job matches, improvement tips, and location detection. Detected skills are highlighted in bold.",
)

# -------------------- LAUNCH --------------------
port = int(os.environ.get("PORT", 7860))
iface.launch(server_name="0.0.0.0", server_port=port, share=False, debug=True)
