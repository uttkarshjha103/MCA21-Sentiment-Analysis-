# MCA21 Sentiment Analysis System

AI-based Sentiment Analysis and Summarization System for MCA21 consultation comments.

## Features

- Automated sentiment analysis using RoBERTa model
- Text summarization with T5 model
- Keyword extraction and topic clustering
- Multilingual support
- Interactive dashboard with visualizations
- Report generation (Excel, PDF, CSV)
- Role-based authentication (Admin/Analyst)

## Technology Stack

- **Backend**: FastAPI with Python 3.9+
- **Database**: MongoDB with Motor async driver
- **AI/ML**: Hugging Face Transformers (RoBERTa, T5)
- **Authentication**: JWT tokens
- **Caching**: Redis
- **Task Queue**: Celery

## Project Structure

```
mca21-sentiment-analysis/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   ├── models/
│   ├── api/
│   ├── services/
│   └── utils/
├── tests/
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment variables
3. Run the application: `uvicorn app.main:app --reload`