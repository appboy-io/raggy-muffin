FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ .

# Fix for asyncio "no running event loop" error - set environment variable
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Run Streamlit with explicit asyncio policy
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
