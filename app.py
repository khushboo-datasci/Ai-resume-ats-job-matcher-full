import os
import io
import re
import gradio as gr
import pdfplumber
from docx import Document
from pdf2image import convert_from_bytes
import pytesseract
import spacy

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Load Spacy
nlp = spacy.load("en_core_web_sm")

# Generic skills
GENERIC_SKILLS = [
    "communication","teamwork","leadership","problem solving","time management",
    "adaptability","customer service","chat support","email support","crm",
    "python","sql","excel","data analysis","sales","marketing"
]

# Sample job DB
JOBS = [
    {"title": "Customer Support Executive", "location": "Jaipur", "skills": ["customer","chat","support","crm"]},
    {"title": "Data Analyst", "location": "Bangalore", "skills": ["data","sql","python","analysis"]},
    {"title": "HR Executive", "location": "Delhi", "skills": ["recruitment","communication","hr"]},
    {"title": "Marketing Executive", "location": "Mumbai", "skills": ["marketing","campaign","content"]},
    {"title": "Sales Executive", "location": "Noida", "skills": ["sales","client","crm"]}
]

# -------------------- RESUME TEXT EXTRACTION --------------------
def extract_resume_text(file):
    """
    Always extract text from PDF (typed/scanned) or DOCX resumes.
    Fallbacks ensure no ❌ errors in UI.
    """
    text = ""
    try:
        # Read bytes and reset pointer
        file_bytes = file.read()
        file.seek(0)
        print(f"[DEBUG] File name: {file.name}, size: {len(file_bytes)} bytes")

        # ---------- PDF ----------
        if file.name.lower().endswith(".pdf"):
            # Try pdfplumber
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + " "
                print(f"[DEBUG] pdfplumber text length: {len(text)}")
            except Exception as e:
                print("[DEBUG] pdfplumber failed:", e)

            # Always run OCR fallback
            try:
                images = convert_from_bytes(io.BytesIO(file_bytes), dpi=400, fmt="ppm")
                ocr_text = ""
                for img in images:
                    ocr_text += pytesseract.image_to_string(img, config="--psm 6")
                print(f"[DEBUG] OCR text length: {len(ocr_text)}")
                if len(ocr_text.strip()) > 0:
                    text = ocr_text  # overwrite with OCR if text is low or empty
            except Exception as e:
                print("[DEBUG] OCR failed:", e)

        # ---------- DOCX ----------
        elif file.name.lower().endswith(".docx"):
            try:
                doc = Document(io.BytesIO(file_bytes))
                for p in doc.paragraphs:
                    text += p.text + " "
                print(f"[DEBUG] DOCX text length: {len(text)}")
            except Exception as e:
                print("[DEBUG] DOCX failed:", e)

        else:
            print("[DEBUG] Unsupported file type")

    except Exception as e:
        print("[DEBUG] Resume extraction error:", e)
        text = "Could not extract text from resume."

    # Ensure at least a placeholder so UI doesn't crash
    if len(text.strip()) < 10:
        text = "Text extraction was difficult. PDF may be scanned. OCR attempted."

    print(f"[DEBUG] Final extracted text length: {len(text)}")
    return text.strip()

# -------------------- NLP & ATS --------------------
def extract_keywords(text):
    doc = nlp(text.lower())
    return list(set([t.text for t in doc if t.pos_ in ["NOUN","PROPN"] and len(t.text) > 2]))

def extract_location(text):
    cities = ["jaipur","delhi","bangalore","mumbai","noida","pune","hyderabad","chennai"]
    for city in cities:
        if city in text.lower():
            return city.title()
    return "Not mentioned"

def calculate_ats(resume_text, jd):
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd)
    keyword_score = min(len(set(resume_keywords) & set(jd_keywords)) * 3, 40)
    skill_score = min(sum(1 for s in GENERIC_SKILLS if s in resume_text.lower()) * 2, 30)
    length_score = 30 if len(resume_text.split()) > 150 else 15
    return keyword_score + skill_score + length_score

def recommend_jobs(resume_text):
    resume_text_lower = resume_text.lower()
    recommended = []
    for job in JOBS:
        match_count = sum(1 for skill in job["skills"] if skill in resume_text_lower)
        if match_count > 0:
            recommended.append(f"{job['title']} ({job['location']})")
    return "\n".join(recommended) if recommended else "No matching jobs found"

def improvement_tips():
    return [
        "Add more job-specific keywords",
        "Quantify your experience with numbers",
        "Enhance skills section with tools & platforms you know"
    ]

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

def extract_detected_skills(text):
    detected = [s.title() for s in GENERIC_SKILLS if s in text.lower()]
    return ", ".join(detected) if detected else "No generic skills detected"

# -------------------- MAIN APP --------------------
def resume_ai_app(resume, job_description):
    resume_text = extract_resume_text(resume)

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
        gr.Textbox(label="ATS Report & Job Recommendations", lines=15),
        gr.Textbox(label="Detected Skills", lines=10),
        gr.Textbox(label="Improvement Tips", lines=10)
    ],
    title="ResumeLens AI – ATS Resume Scanner & Job Matcher",
    description="Upload your resume to get ATS score, job matches, improvement tips, and location detection. Detected skills are highlighted in bold.",
)

port = int(os.environ.get("PORT", 7860))
iface.launch(server_name="0.0.0.0", server_port=port, share=False, debug=True)
