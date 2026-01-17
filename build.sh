#!/bin/bash
set -e

echo "---- Updating system packages ----"
sudo apt-get update -y

echo "---- Installing Tesseract OCR ----"
sudo apt-get install -y tesseract-ocr

echo "---- Installing Poppler Utils (PDF to image) ----"
sudo apt-get install -y poppler-utils

echo "---- Installing Python dependencies ----"
pip install --upgrade pip
pip install -r requirements.txt

echo "---- Downloading spaCy English model ----"
python -m spacy download en_core_web_sm

echo "---- Build completed ----"
