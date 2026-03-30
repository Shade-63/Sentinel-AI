# -- 1. Base image -- slim Python 3.11 on Linux
FROM python:3.11-slim

# -- 2. Set working directory inside the container
WORKDIR /app

# -- 3. Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# -- 4. Copy requirements first (Docker layer caching)
COPY requirements.txt .

# -- 5. Install PyTorch CPU-only FIRST (much smaller, ~200MB vs 2GB)
RUN pip install --no-cache-dir torch==2.2.2+cpu --index-url https://download.pytorch.org/whl/cpu

# -- 6. Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# -- 7. Copy the entire project into the container
COPY . .

# -- 8. HuggingFace Spaces requires port 7860
EXPOSE 7860

# -- 9. Start the app
CMD ["python", "app/app.py"]