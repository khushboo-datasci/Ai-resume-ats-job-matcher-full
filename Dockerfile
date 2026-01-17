# Base Python image
FROM python:3.11-slim

# System dependencies for OCR and PDF
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --use-deprecated=legacy-resolver -r requirements.txt

# Copy all project files
COPY . .

# Expose Gradio default port
EXPOSE 7860

# Start command
CMD ["python", "app.py"]
