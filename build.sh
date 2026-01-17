#!/bin/bash
set -e

echo "---- Installing Python dependencies ----"
pip install --upgrade pip
pip install -r requirements.txt

echo "---- Downloading spaCy English model ----"
python -m spacy download en_core_web_sm

echo "---- Build completed ----"
