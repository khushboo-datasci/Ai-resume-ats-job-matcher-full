import os
import gradio as gr
import pdfplumber
from docx import Document
from pdf2image import convert_from_path
import pytesseract
import spacy
from difflib import get_close_matches

# Safe spaCy model load
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Your full resume ATS + Gradio functions here
# extract_text_resume_all, extract_keywords_nlp, match_keywords_v2,
# match_generic_skills_v2, check_sections_v3, calculate_ats_score_v3,
# resume_improvement_tips, match_job, get_top_jobs, resume_ats_job_matcher

iface = gr.Interface(
    fn=resume_ats_job_matcher,
    inputs=[gr.File(label="Upload Resume (PDF/DOCX)"),
            gr.Textbox(label="Job Description"),
            gr.Textbox(label="Preferred Location (Optional)")],
    outputs="text",
    title="💼 AI Resume ATS & Job Matcher",
    description="Upload your resume and paste the job description to calculate ATS score, see missing keywords, improvement tips, and top matching jobs."
)

# Render compatible port
iface.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860))
)
