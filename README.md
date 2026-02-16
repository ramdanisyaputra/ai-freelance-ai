# AI Freelance Proposal Generator

FastAPI service using LangGraph for intelligent proposal generation.

## Features

- **LangGraph Workflow**: Multi-step proposal generation with brief analysis, scope extraction, estimation, and content creation
- **Multi-Model Support**: Primary Claude model with OpenAI fallback
- **Async Processing**: Background task processing with callback to Laravel backend
- **HTML Output**: Rich HTML proposals ready for editing

## Setup

1. **Create virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. **Run the service**:
```bash
python app/main.py
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST /api/generate-proposal
Receives proposal generation requests from Laravel backend.

**Request Body**:
```json
{
  "proposal_id": 1,
  "brief": "Client brief text...",
  "user_brief": "Freelancer context...",
  "freelancer_profile": {
    "stack": ["React", "Laravel"],
    "rate_type": "project",
    "min_price": 5000000,
    "currency": "IDR"
  },
  "callback_url": "http://localhost:8000/api/ai/callback/proposal/1"
}
```

**Response**:
```json
{
  "status": "accepted",
  "proposal_id": 1,
  "message": "Proposal generation started"
}
```

### GET /health
Health check endpoint.

## Environment Variables

See `.env.example` for required configuration:
- `ANTHROPIC_API_KEY`: Claude API key
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `LARAVEL_API_URL`: Laravel backend URL
- `LARAVEL_API_TOKEN`: Authentication token for callbacks

## Workflow Steps

1. **Analyze Brief**: Extract key requirements from client message
2. **Generate Scope**: Create list of deliverables
3. **Estimate Project**: Calculate duration and pricing
4. **Generate Proposal**: Create professional HTML proposal

## Development

Run with auto-reload:
```bash
uvicorn app.main:app --reload
```

View logs:
```bash
tail -f logs/app.log
```
