import gradio as gr
import pdfplumber
from docx import Document
from pdf2image import convert_from_path
import pytesseract

GENERIC_SKILLS = [
    "communication","teamwork","leadership","problem-solving","critical thinking",
    "time management","adaptability","creativity","data analysis","customer service",
    "sales","marketing","project management","programming","python","java","sql",
    "machine learning","excel","powerpoint","research"
]

# ---------------- Extract Text + OCR ----------------
def extract_text_resume(file):
    text = ""
    filename = file.name if hasattr(file,"name") else file
    try:
        if filename.endswith(".pdf"):
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            # OCR fallback
            if len(text.strip()) == 0:
                pages = convert_from_path(file)
                for page in pages:
                    text += pytesseract.image_to_string(page) + "\n"
        elif filename.endswith(".docx"):
            doc = Document(file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            text = "Unsupported file format!"
    except Exception as e:
        text = f"Error extracting text: {str(e)}"
    return text

# ---------------- Keyword Extraction ----------------
def extract_keywords(text):
    words = set([w.lower() for w in text.split() if len(w)>2])
    return list(words)

def match_keywords(resume_keywords, job_keywords):
    matched = set()
    for jk in job_keywords:
        close = [r for r in resume_keywords if jk.lower() in r]
        if close:
            matched.add(close[0])
    return list(matched)

def match_generic_skills(resume_text):
    resume_text_lower = resume_text.lower()
    matched = []
    for skill in GENERIC_SKILLS:
        if skill.lower() in resume_text_lower:
            matched.append(skill)
    return matched

# ---------------- ATS Scoring ----------------
def calculate_ats(resume_text, job_description):
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_description)
    matched_keywords = match_keywords(resume_keywords, job_keywords)
    matched_generic = match_generic_skills(resume_text)
    
    keyword_score = len(matched_keywords)/max(len(job_keywords),1)*50
    generic_score = len(matched_generic)/len(GENERIC_SKILLS)*30
    ats_score = round(keyword_score + generic_score,2)
    
    missing_keywords = list(set(job_keywords)-set(resume_keywords))
    
    tips = []
    if len(matched_generic) < 5:
        tips.append("Add more soft skills like communication, teamwork, leadership.")
    if missing_keywords:
        tips.append("Include missing job-specific keywords naturally in your experience or skills section.")
    tips.append("Use bullet points with action verbs and quantify achievements.")
    
    return ats_score, matched_keywords, matched_generic, missing_keywords, tips

# ---------------- Gradio Interface ----------------
def main(resume_file, job_description):
    resume_text = extract_text_resume(resume_file)
    if "Unsupported" in resume_text:
        return "Unsupported file format!"
    
    ats_score, matched_keywords, matched_generic, missing_keywords, tips = calculate_ats(resume_text, job_description)
    
    result = f"""
ATS Score: {ats_score}/100
Matched Keywords: {matched_keywords}
Matched Generic Skills: {matched_generic}
Missing Keywords: {missing_keywords[:20]}

Resume Improvement Tips:
- {chr(10).join(tips)}
"""
    return result

iface = gr.Interface(
    fn=main,
    inputs=[gr.File(label="Upload Resume (PDF/DOCX)"), gr.Textbox(label="Job Description")],
    outputs="text",
    title="💼 OCR + ATS Resume Matcher",
    description="Upload your resume (PDF/DOCX) and job description to calculate ATS score, missing keywords, and improvement tips."
)

if __name__=="__main__":
    iface.launch(server_name="0.0.0.0", server_port=8080)
