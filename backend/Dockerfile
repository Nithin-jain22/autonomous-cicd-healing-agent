FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of backend code
COPY . .

# Expose port (Railway provides PORT automatically)
EXPOSE 8000

# Start FastAPI server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]