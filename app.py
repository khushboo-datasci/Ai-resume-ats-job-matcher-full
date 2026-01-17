import gradio as gr
import pdfplumber
from docx import Document
from pdf2image import convert_from_path
import pytesseract
import spacy
from difflib import get_close_matches

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Generic Skills
GENERIC_SKILLS = [
    "communication","teamwork","leadership","problem-solving","critical thinking",
    "time management","adaptability","creativity","data analysis","customer service",
    "sales","marketing","project management","programming","python","java","sql",
    "machine learning","excel","powerpoint","research"
]

# Sample Jobs
JOBS = [
    {"title": "Customer Support Executive", "description": "Live chat support, customer service, troubleshooting, CRM, communication, multitasking", "location": "Jaipur, Rajasthan"},
    {"title": "Marketing Executive", "description": "Campaign planning, market research, content creation, client communication, reporting", "location": "Mumbai, Maharashtra"},
    {"title": "Data Analyst", "description": "Data analysis, SQL, Python, Excel, reporting, visualization", "location": "Bangalore, Karnataka"},
    {"title": "Sales Executive", "description": "Lead generation, client communication, CRM, sales reporting, multitasking", "location": "Jaipur, Rajasthan"}
]

# --- OCR + Text Extraction ---
def extract_text_resume_all(file):
    text = ""
    filename = file.name if hasattr(file, "name") else file
    if filename.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
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
    return text

# --- Keyword Extraction ---
def extract_keywords_nlp(text):
    doc = nlp(text.lower())
    keywords = set()
    for token in doc:
        if token.pos_ in ["NOUN","PROPN"] and len(token.text) > 2:
            keywords.add(token.text)
    return list(keywords)

def match_keywords_v2(resume_keywords, job_keywords):
    matched = set()
    for jk in job_keywords:
        close = get_close_matches(jk.lower(), [r.lower() for r in resume_keywords], cutoff=0.5)
        if close:
            matched.add(close[0])
    return list(matched)

def match_generic_skills_v2(resume_text, generic_skills):
    resume_text_lower = resume_text.lower()
    matched = []
    for skill in generic_skills:
        if skill.lower() in resume_text_lower:
            matched.append(skill)
        else:
            words = skill.lower().split()
            if any(w in resume_text_lower for w in words):
                matched.append(skill)
    return matched

# --- Sections & ATS Score ---
SECTION_KEYWORDS = {
    "education": ["education","academic","qualifications","degree","school","college","university"],
    "experience": ["experience","work experience","employment","professional experience","career","background"],
    "skills": ["skills","technical skills","expertise","proficiencies","capabilities","abilities"],
    "projects": ["projects","project work","academic projects","assignments"],
    "certifications": ["certifications","licenses","achievements","awards"]
}

def check_sections_v3(resume_text):
    resume_text_lower = resume_text.lower()
    present_sections = []
    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in resume_text_lower:
                present_sections.append(section)
                break
    return present_sections

def calculate_ats_score_v3(resume_text, job_keywords, generic_skills):
    present_sections = check_sections_v3(resume_text)
    section_score = len(present_sections)/5*40
    resume_keywords = extract_keywords_nlp(resume_text)
    matched_keywords = match_keywords_v2(resume_keywords, job_keywords)
    keyword_score = len(matched_keywords)/max(len(job_keywords),1)*40
    matched_generic_skills = match_generic_skills_v2(resume_text, generic_skills)
    generic_score = len(matched_generic_skills)/max(len(generic_skills),1)*20
    ats_score = section_score + keyword_score + generic_score
    return round(ats_score,2), present_sections, matched_keywords, matched_generic_skills

# --- Missing Keywords + Tips ---
def find_missing_keywords(resume_text, job_description):
    resume_keywords = set(extract_keywords_nlp(resume_text))
    job_keywords = set(extract_keywords_nlp(job_description))
    return list(job_keywords - resume_keywords)

def resume_improvement_tips(matched_generic_skills, missing_keywords):
    tips = []
    if len(matched_generic_skills) < 5:
        tips.append("Add more soft skills like communication, teamwork, leadership.")
    if len(missing_keywords) > 0:
        tips.append("Include missing job-specific keywords naturally in experience or skills section.")
    tips.append("Use bullet points with action verbs (Handled, Managed, Improved, Resolved).")
    tips.append("Quantify achievements (e.g., 95% customer satisfaction, 50+ chats/day).")
    return tips

# --- Job Matching ---
def match_job(resume_text, job, generic_skills, location_filter=None):
    job_keywords = extract_keywords_nlp(job['description'])
    resume_keywords = extract_keywords_nlp(resume_text)
    matched_keywords = match_keywords_v2(resume_keywords, job_keywords)
    keyword_score = len(matched_keywords)/max(len(job_keywords),1)*50
    matched_generic_skills = match_generic_skills_v2(resume_text, generic_skills)
    generic_score = len(matched_generic_skills)/max(len(generic_skills),1)*30
    present_sections = check_sections_v3(resume_text)
    section_score = len(present_sections)/5*20
    total_score = round(keyword_score+generic_score+section_score,2)
    if location_filter and location_filter.lower() not in job['location'].lower():
        total_score *= 0.7
    return total_score, matched_keywords, matched_generic_skills

def get_top_jobs(resume_text, jobs_list, generic_skills, top_n=5, location=None):
    results = []
    for job in jobs_list:
        score, matched_keywords, matched_generic_skills = match_job(resume_text, job, generic_skills, location)
        results.append({
            "title": job['title'],
            "location": job['location'],
            "score": score,
            "matched_keywords": matched_keywords,
            "matched_generic_skills": matched_generic_skills
        })
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    return results[:top_n]

# --- Gradio App ---
def resume_ats_job_matcher(resume_file, job_description, location_filter=""):
    resume_text = extract_text_resume_all(resume_file)
    if "Unsupported" in resume_text:
        return "Unsupported file format!"

    job_keywords = extract_keywords_nlp(job_description)
    ats_score, present_sections, matched_keywords, matched_generic_skills = calculate_ats_score_v3(
        resume_text, job_keywords, GENERIC_SKILLS
    )
    missing_keywords = find_missing_keywords(resume_text, job_description)
    improvement_tips = resume_improvement_tips(matched_generic_skills, missing_keywords)
    top_jobs = get_top_jobs(resume_text, JOBS, GENERIC_SKILLS, top_n=5, location=location_filter)

    result = f"""
ATS Score: {ats_score}/100
Sections Found: {present_sections}
Matched Job Keywords: {matched_keywords}
Matched Generic Skills: {matched_generic_skills}
Missing Keywords: {missing_keywords[:20]}

Resume Improvement Tips:
- {chr(10).join(improvement_tips)}

Top Jobs Match:
"""
    for idx, job in enumerate(top_jobs,1):
        result += f"\n{idx}. {job['title']} ({job['location']}) - Score: {job['score']}\n"
        result += f"Matched Keywords: {job['matched_keywords']}\n"
        result += f"Matched Generic Skills: {job['matched_generic_skills']}\n"

    return result

def main():
    iface = gr.Interface(
        fn=resume_ats_job_matcher,
        inputs=[gr.File(label="Upload Resume (PDF/DOCX)"),
                gr.Textbox(label="Job Description"),
                gr.Textbox(label="Preferred Location (Optional)")],
        outputs="text",
        title="💼 AI Resume ATS & Job Matcher",
        description="Upload your resume and paste the job description to calculate ATS score, see missing keywords, improvement tips, and top matching jobs."
    )
    iface.launch(server_name="0.0.0.0", server_port=8080)

if __name__ == "__main__":
    main()
