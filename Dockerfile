# ── 1. Base image — slim Python 3.11 on Linux
FROM python:3.11-slim

# ── 2. Set working directory inside the container
WORKDIR /app

# ── 3. Install system dependencies
#    gcc        → needed to compile some Python packages
#    tesseract-ocr     → the OCR binary (what pytesseract wraps)
#    tesseract-ocr-eng → English language data pack for Tesseract
#    libglib2.0-0      → required by Pillow for image processing
RUN apt-get update && apt-get install -y \
    gcc \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── 4. Copy requirements first (Docker caching trick —
#    if requirements.txt hasn't changed, this layer is cached
#    and pip install doesn't re-run on every build)
COPY requirements.txt .

# ── 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ── 6. Copy the entire project into the container
COPY . .

# ── 7. HuggingFace Spaces requires port 7860
EXPOSE 7860

# ── 8. Tell the container how to start your app
#    The 0.0.0.0 host is critical — without it the app
#    only listens inside the container and HF can't reach it
CMD ["python", "app/app.py"]