FROM python:3.11-slim

WORKDIR /app

# Install dependencies - copy requirements first for layer caching
COPY requirements.txt .

# Force reinstall to avoid stale cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ ./app/

# Create required directories
RUN mkdir -p logs uploads/reports

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
