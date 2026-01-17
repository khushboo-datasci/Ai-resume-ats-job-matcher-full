#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt

# Pro plan / Metal build ke liye system packages
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
