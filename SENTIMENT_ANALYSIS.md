# Sentiment Analysis Feature

## Overview

The sentiment analysis feature uses the RoBERTa-base model from Hugging Face to classify comments as positive, negative, or neutral with confidence scores. The system supports both single text analysis and batch processing for efficiency.

## Model Information

- **Model**: cardiffnlp/twitter-roberta-base-sentiment-latest
- **Architecture**: RoBERTa (Robustly Optimized BERT Pretraining Approach)
- **Labels**: positive, negative, neutral
- **Device**: Automatically detects CUDA GPU if available, otherwise uses CPU

## API Endpoints

### 1. Analyze Single Text

**Endpoint**: `POST /api/v1/sentiment/analyze`

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "text": "This is an excellent policy!"
}
```

**Response**:
```json
{
  "label": "positive",
  "confidence": 0.9234,
  "scores": {
    "negative": 0.0123,
    "neutral": 0.0643,
    "positive": 0.9234
  },
  "processed_at": "2024-01-15T10:30:00Z"
}
```

### 2. Batch Analysis

**Endpoint**: `POST /api/v1/sentiment/analyze/batch`

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "texts": [
    "This is great!",
    "This is terrible.",
    "This is okay."
  ],
  "batch_size": 32
}
```

**Response**:
```json
{
  "results": [
    {
      "label": "positive",
      "confidence": 0.9234,
      "scores": {...},
      "processed_at": "2024-01-15T10:30:00Z"
    },
    ...
  ],
  "total_processed": 3,
  "model_info": {
    "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
    "device": "cpu",
    "labels": ["negative", "neutral", "positive"]
  }
}
```

### 3. Get Model Information

**Endpoint**: `GET /api/v1/sentiment/model-info`

**Authentication**: Required (Bearer token)

**Response**:
```json
{
  "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
  "device": "cpu",
  "labels": ["negative", "neutral", "positive"]
}
```

## Usage in Code

### Using the Service Directly

```python
from app.services.sentiment import get_sentiment_analyzer

# Get the analyzer instance
analyzer = get_sentiment_analyzer()

# Analyze single text
result = analyzer.analyze_sentiment("This is an excellent policy!")
print(f"Sentiment: {result.label}, Confidence: {result.confidence}")

# Batch analysis
texts = ["Text 1", "Text 2", "Text 3"]
results = analyzer.batch_analyze(texts, batch_size=32)
for result in results:
    print(f"Sentiment: {result.label}")
```

### Using the API

```python
import httpx

# Login to get token
response = httpx.post("http://localhost:8000/api/v1/auth/login", json={
    "email": "user@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Analyze sentiment
headers = {"Authorization": f"Bearer {token}"}
response = httpx.post(
    "http://localhost:8000/api/v1/sentiment/analyze",
    json={"text": "This is great!"},
    headers=headers
)
result = response.json()
print(f"Sentiment: {result['label']}")
```

## Performance Considerations

### Batch Processing

- Use batch processing for analyzing multiple texts efficiently
- Default batch size is 32, which balances memory usage and performance
- Batch processing is significantly faster than individual requests

### Model Loading

- The model is loaded lazily on first use
- The model instance is cached globally for reuse across requests
- First request will be slower due to model loading (~5-10 seconds)
- Subsequent requests are fast (~100-500ms per text)

### Memory Usage

- Model size: ~500MB
- GPU memory (if available): ~1GB
- CPU memory: ~2GB for model + processing

## Testing

### Unit Tests

Run unit tests for the sentiment service:

```bash
pytest tests/test_sentiment.py -v
```

### Integration Tests

Run integration tests for the API endpoints:

```bash
pytest tests/test_sentiment_endpoints.py -v
```

## Requirements

The following dependencies are required:

- transformers==4.36.0 (or later)
- torch==2.9.0 (or later)
- sentencepiece (optional, for some tokenizers)

Install with:

```bash
pip install transformers torch
```

## Troubleshooting

### Model Download Issues

If the model fails to download:
1. Check internet connection
2. Set HF_TOKEN environment variable for authenticated access
3. Manually download the model and place in cache directory

### Memory Issues

If you encounter out-of-memory errors:
1. Reduce batch_size parameter
2. Use CPU instead of GPU (set CUDA_VISIBLE_DEVICES="")
3. Process texts in smaller chunks

### Slow Performance

If analysis is slow:
1. Use batch processing instead of individual requests
2. Enable GPU if available
3. Increase batch_size (if memory allows)
4. Consider using a smaller model variant

## Future Enhancements

- Support for additional languages
- Custom model fine-tuning on domain-specific data
- Caching of frequently analyzed texts
- Real-time streaming analysis
- Integration with comment upload pipeline
