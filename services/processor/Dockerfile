FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for scikit-learn
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon')"

# Copy application code
COPY . .

# Run the processor service
CMD ["python", "main.py"]
