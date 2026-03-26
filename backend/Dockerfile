FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR, PDF processing
RUN apt-get update && apt-get install -y \
    gcc \
    libmagic1 \
    poppler-utils \
    curl \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Tesseract environment variable
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
