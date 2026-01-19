# 💼 AI Resume ATS & Job Matcher

An end-to-end AI-powered Resume ATS Scanner & Job Recommendation System built using **Python, spaCy, OCR, and Gradio**.  
The system analyzes resumes (PDF/DOCX), calculates ATS score, extracts skills, finds missing keywords, and recommends suitable jobs with location matching.

---

## 🌐 Live Deployment

🚀 **Try the live app here:**  
👉 (https://rare-gratitude-production-95d7.up.railway.app/)

---

## 🚀 Features

- 📄 Supports **PDF & DOCX resumes**
- 🔍 **OCR-based extraction** for scanned resumes
- 📊 **ATS Score calculation**
- 🧠 NLP-based **keyword extraction (spaCy)**
- 🛠️ Generic & job-specific **skill matching**
- 📍 **Location-based job recommendations**
- 💡 Resume improvement suggestions
- 🌐 Web UI using **Gradio**
- 🐳 Fully **Dockerized & deployment-ready**

---

## 🧠 How It Works (Project Flow)

1. User uploads a resume (PDF/DOCX)
2. Text extraction:
   - `pdfplumber` → normal PDFs
   - `pytesseract + pdf2image` → scanned PDFs
   - `python-docx` → DOCX files
3. NLP processing using **spaCy**
4. Extract:
   - Keywords
   - Skills
   - Resume sections (Education, Skills, Experience, etc.)
5. ATS score calculation based on:
   - Section presence
   - Keyword match
   - Generic skill coverage
6. Job matching using a sample jobs database
7. Display:
   - ATS Score
   - Missing keywords
   - Improvement tips
   - Best job recommendations

---

## 🛠️ Tech Stack

- **Python 3.11**
- **spaCy (en_core_web_sm)**
- **Gradio**
- **pdfplumber**
- **pytesseract**
- **pdf2image**
- **python-docx**
- **Docker**
- **Tesseract OCR**

---

## 📂 Project Structure

```text
├── app.py
├── Dockerfile
├── requirements.txt
├── README.md

------

Author

Khushboo kumari
Aspiring Data Scientist | AI & NLP Enthusiast

🔗 GitHub:(https://github.com/khushboo-datasci)
