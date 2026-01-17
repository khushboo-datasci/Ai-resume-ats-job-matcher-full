#!/bin/bash

# Upgrade pip
pip install --upgrade pip

# Install python dependencies
pip install -r requirements.txt

# No need for sudo in Pro/Metal plan
# tesseract + poppler-utils already available in Metal plan
echo "✅ Dependencies installed"
