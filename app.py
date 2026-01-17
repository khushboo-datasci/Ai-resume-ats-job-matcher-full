import gradio as gr
import pdfplumber
from docx import Document
from pdf2image import convert_from_path
import pytesseract

# Generic skills list
GENERIC_SKILLS = [
    "communication","teamwork","leadership","problem-solving","critical thinking",
    "time management","adaptability","creativity","data analysis","customer service",
    "sales","marketing","project management","programming","python","java","sql",
    "machine learning","excel","powerpoint","research"
]

# Sample jobs database
JOBS = [
    {"title": "Customer Support Executive", "description": "Live chat support, customer service, troubleshooting, CRM, communication, multitasking", "location": "Jaipur, Rajasthan"},
    {"title": "Marketing Executive", "description": "Campaign planning, market research, content creation, client communication, reporting", "location": "Mumbai, Maharashtra"},
    {"title": "Data Analyst", "description": "Data analysis, SQL, Python, Excel, reporting, visualization", "location": "Bangalore, Karnataka"},
    {"title": "Sales Executive", "description": "Lead generation, client communication, CRM, sales reporting, multitasking", "location": "Jaipur, Rajasthan"}
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
            # OCR fallback for scanned PDFs
            if len(text.strip()) == 0:
                pages = convert_from_path(file, dpi=150)
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
    return text.lower()

# ---------------- Keyword Extraction ----------------
def extract_keywords(text):
    return set([w for w in text.split() if len(w)>1])  # small words included

def match_keywords(resume_keywords, job_keywords):
    return list(resume_keywords & job_keywords)

def match_generic_skills(resume_text):
    matched = []
    for skill in GENERIC_SKILLS:
        if skill.lower() in resume_text:
            matched.append(skill)
    return matched

# ---------------- ATS Scoring ----------------
def calculate_ats(resume_text, job_description):
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_description.lower())
    matched_keywords = match_keywords(resume_keywords, job_keywords)
    matched_generic = match_generic_skills(resume_text)
    
    keyword_score = len(matched_keywords)/max(len(job_keywords),1)*50
    generic_score = len(matched_generic)/len(GENERIC_SKILLS)*30
    ats_score = round(keyword_score + generic_score,2)
    
    missing_keywords = list(job_keywords - resume_keywords)
    
    tips = []
    if len(matched_generic) < 5:
        tips.append("Add more soft skills like communication, teamwork, leadership.")
    if missing_keywords:
        tips.append("Include missing job-specific keywords naturally in your experience or skills section.")
    tips.append("Use bullet points with action verbs and quantify achievements.")
    
    return ats_score, matched_keywords, matched_generic, missing_keywords, tips

# ---------------- Job Matching ----------------
def get_top_jobs(resume_text, location_filter=""):
    results = []
    for job in JOBS:
        score, matched_keywords, matched_generic, _, _ = calculate_ats(resume_text, job['description'])
        # Location filter
        if location_filter and location_filter.lower() not in job['location'].lower():
            score *= 0.7
        results.append({
            "title": job['title'],
            "location": job['location'],
            "score": round(score,2),
            "matched_keywords": matched_keywords,
            "matched_generic_skills": matched_generic
        })
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    return results[:5]

# ---------------- Gradio Interface ----------------
def main(resume_file, job_description, location_filter=""):
    resume_text = extract_text_resume(resume_file)
    if "Unsupported" in resume_text:
        return "Unsupported file format!"
    
    ats_score, matched_keywords, matched_generic, missing_keywords, tips = calculate_ats(resume_text, job_description)
    
    top_jobs = get_top_jobs(resume_text, location_filter)
    
    result = f"""
ATS Score: {ats_score}/100
Matched Job Keywords: {matched_keywords}
Matched Generic Skills: {matched_generic}
Missing Keywords: {missing_keywords[:20]}

Resume Improvement Tips:
- {chr(10).join(tips)}

Top Jobs Match:
"""
    for idx, job in enumerate(top_jobs,1):
        result += f"\n{idx}. {job['title']} ({job['location']}) - Score: {job['score']}\n"
        result += f"Matched Keywords: {job['matched_keywords']}\n"
        result += f"Matched Generic Skills: {job['matched_generic_skills']}\n"

    return result

iface = gr.Interface(
    fn=main,
    inputs=[
        gr.File(label="Upload Resume (PDF/DOCX)"),
        gr.Textbox(label="Job Description"),
        gr.Textbox(label="Preferred Location (Optional)")
    ],
    outputs="text",
    title="💼 Pro OCR + ATS Resume Matcher",
    description="Upload your resume (PDF/DOCX/scanned) and job description to get ATS score, missing keywords, improvement tips, and top matching jobs."
)

if __name__=="__main__":
    iface.launch(server_name="0.0.0.0", server_port=8080)
