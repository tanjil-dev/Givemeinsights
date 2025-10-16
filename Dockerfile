# Use a lightweight Python image
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Working directory
WORKDIR /app

# Install system dependencies + Chromium for Kaleido
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 libsm6 libxext6 libxrender-dev \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libdrm2 libgbm1 libnspr4 libnss3 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 xdg-utils chromium \
    && rm -rf /var/lib/apt/lists/*

# Tell Kaleido where to find Chromium
ENV KALIEDO_CHROME_PATH=/usr/bin/chromium

# Copy dependency list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port (Cloud Run expects this)
EXPOSE 8080

# Run Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
