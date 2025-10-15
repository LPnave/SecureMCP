# SecureMCP Python Backend

ML-based prompt sanitization service with zero-shot classification using BART and spaCy.

## Features

- 🤖 **Zero-shot classification** using facebook/bart-large-mnli
- 🔍 **Pattern matching** with spaCy for supplemental detection
- 🔐 **Multi-layer security** (credentials, injection, jailbreak, malicious code)
- ⚡ **Fast processing** (~100-500ms per prompt)
- 📊 **Detailed analytics** with confidence scores
- 🎯 **Three security levels** (low, medium, high)

## Requirements

- Python 3.9+
- 2GB+ RAM (for ML models)
- ~2GB disk space (for model cache)

## Installation

### 1. Install Python Dependencies

```bash
cd agent-ui/python-backend
pip install -r requirements.txt
```

### 2. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 3. Configure Environment (Optional)

Create a `.env` file in the `python-backend` directory:

```bash
# Copy example and edit
cp .env.example .env
```

Default configuration:
- Port: 8003
- Host: 0.0.0.0
- Security Level: medium
- CORS Origins: http://localhost:3000,http://localhost:3001

## Running the Server

### Development Mode (with auto-reload)

```bash
python app/main.py
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --port 8003
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8003 --workers 4
```

## API Endpoints

### POST /api/sanitize
Sanitize a single prompt

**Request:**
```json
{
  "prompt": "What's the weather today?",
  "security_level": "medium",
  "return_details": false
}
```

**Response:**
```json
{
  "is_safe": true,
  "sanitized_prompt": "What's the weather today?",
  "original_prompt": "What's the weather today?",
  "warnings": [],
  "blocked_patterns": [],
  "confidence": 0.95,
  "modifications_made": false,
  "processing_time_ms": 234.5
}
```

### POST /api/sanitize/batch
Sanitize multiple prompts

**Request:**
```json
{
  "prompts": ["prompt1", "prompt2"],
  "security_level": "medium",
  "return_details": false
}
```

### GET /api/health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime_seconds": 123.45,
  "version": "1.0.0"
}
```

### GET /api/stats
Get performance statistics

### GET /api/security/level
Get current security level

### PUT /api/security/level
Update security level

**Request:**
```json
{
  "level": "high"
}
```

## Security Levels

### Low
- Basic sensitive data masking
- Warnings only for most threats
- Best for: Development, testing

### Medium (Default)
- Blocks high-confidence threats
- Sanitizes credentials and sensitive data
- Best for: Production, general use

### High
- Strict validation
- Blocks jailbreak attempts
- Aggressive sanitization
- Best for: High-security environments

## Testing

### Quick Test

```bash
# In one terminal
python app/main.py

# In another terminal
curl -X POST http://localhost:8003/api/sanitize \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world!"}'
```

### Health Check

```bash
curl http://localhost:8003/api/health
```

## Performance

- **First request:** ~2-3s (model initialization)
- **Subsequent requests:** ~100-500ms
- **Memory usage:** ~1.5GB (models loaded)
- **Concurrent requests:** Supported (asyncio)

## Troubleshooting

### Models Not Loading

```bash
# Reinstall transformers
pip install --upgrade transformers torch

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Port Already in Use

Change the port in `.env`:
```
PORT=8004
```

### CORS Errors

Add your frontend origin to `CORS_ORIGINS` in `.env`:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://yourapp.com
```

## Architecture

```
┌─────────────────────────────────────┐
│         FastAPI Server              │
│  (app/main.py)                      │
└────────────┬────────────────────────┘
             │
             ├─ /api/sanitize
             ├─ /api/sanitize/batch
             ├─ /api/health
             ├─ /api/stats
             └─ /api/security/level
             │
             ▼
┌─────────────────────────────────────┐
│    ZeroShotSecurityValidator        │
│  (app/core/security.py)             │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ BART Zero-Shot Classifier     │ │
│  │ facebook/bart-large-mnli      │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ spaCy Pattern Matcher         │ │
│  │ en_core_web_sm                │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Entropy Detection             │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

## License

Part of the SecureMCP project.
