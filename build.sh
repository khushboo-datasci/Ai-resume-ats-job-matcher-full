#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt
# If using Pro plan / Metal build (system packages supported)
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
