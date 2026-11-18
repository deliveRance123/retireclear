# Production Dockerfile for RetireClear
FROM python:3.12-slim

# Install system dependencies including Tesseract OCR and system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application source
COPY . .

# Create uploads directory structure
RUN mkdir -p uploads/passports uploads/documents uploads/certificates

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=5000
ENV FLASK_CONFIG=production

# Expose port
EXPOSE 5000

# Start production server with Gunicorn
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
