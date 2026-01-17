#!/bin/bash
set -e

apt-get update
apt-get install -y tesseract-ocr poppler-utils

pip install --upgrade pip
pip install -r requirements.txt
