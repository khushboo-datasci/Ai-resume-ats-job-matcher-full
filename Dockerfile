FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --use-deprecated=legacy-resolver -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .

EXPOSE 7860

CMD ["python", "app.py"]
