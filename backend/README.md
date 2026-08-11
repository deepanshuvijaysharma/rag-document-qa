# Backend Service - RAG Document Q&A

This directory contains the Python FastAPI backend service for the RAG Document Q&A application.

## Prerequisites

- Python 3.11+
- Virtual environment (`venv` or `conda`)

## Setup Instructions

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. Create local `.env` configuration file from template:
   ```bash
   cp .env.example .env
   ```

4. Run the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. Access interactive API documentation:
   - Swagger UI: `http://localhost:8000/api/v1/docs`
   - ReDoc: `http://localhost:8000/api/v1/redoc`
   - Health Check: `http://localhost:8000/health`
