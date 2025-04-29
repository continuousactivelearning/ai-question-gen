# Use an official Python base image
FROM python:3.9-slim

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    python3-dev \
    curl \
    git \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app


# Install Python dependencies using uv
COPY requirements.txt .
RUN pip install uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Expose the port your Flask app runs on (default 5000)
EXPOSE 5000

# Set environment variable for Flask
ENV FLASK_APP=backend.rest_api.py
ENV FLASK_RUN_HOST=0.0.0.0

# Start the Flask app
CMD ["flask", "run"]
