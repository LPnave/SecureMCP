# SecureMCP Agent UI

A Next.js-based AI assistant interface with integrated ML-powered prompt sanitization.

## Architecture

This project consists of two services:

1. **Next.js Frontend** (`secure_agent/`) - Chat UI built with assistant-ui
2. **Python Backend** (`python-backend/`) - ML-based sanitization service

```
┌──────────────────────────────────────────┐
│      Next.js Frontend (Port 3000)       │
│   - Chat UI (assistant-ui)              │
│   - Message handling                    │
│   - OpenAI integration                  │
└────────────┬─────────────────────────────┘
             │ HTTP REST API
             ▼
┌──────────────────────────────────────────┐
│   Python Backend (Port 8003)             │
│   - Zero-shot classification (BART)     │
│   - Pattern matching (spaCy)            │
│   - Credential masking                  │
│   - Threat detection                    │
└────────────┬─────────────────────────────┘
             │ Sanitized Prompts
             ▼
┌──────────────────────────────────────────┐
│          OpenAI API                      │
└──────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- 2GB+ RAM
- OpenAI API key

### 1. Install Dependencies

#### Frontend (Next.js)
```bash
cd secure_agent
npm install
```

#### Backend (Python)
```bash
cd python-backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Environment

#### Frontend
Create `secure_agent/.env.local`:
```env
OPENAI_API_KEY=sk-your-api-key-here
NEXT_PUBLIC_SANITIZER_API_URL=http://localhost:8003
NEXT_PUBLIC_SANITIZER_ENABLED=true
```

#### Backend (Optional)
Create `python-backend/.env`:
```env
PORT=8003
DEFAULT_SECURITY_LEVEL=medium
CORS_ORIGINS=http://localhost:3000
```

### 3. Start Both Services

#### Option A: Run Manually (Two Terminals)

**Terminal 1 - Python Backend:**
```bash
cd python-backend
python app/main.py
```

**Terminal 2 - Next.js Frontend:**
```bash
cd secure_agent
npm run dev
```

#### Option B: Use Package Script (requires concurrently)

```bash
cd secure_agent
npm install concurrently --save-dev
npm run dev:full
```

### 4. Open the App

Visit [http://localhost:3000](http://localhost:3000)

## Features

### 🔒 Security Features

- **ML-based threat detection** using zero-shot classification
- **Credential masking** (passwords, API keys, tokens)
- **Injection prevention** (prompt injection, jailbreak attempts)
- **Malicious code detection**
- **Three security levels** (low, medium, high)

### 🎨 UI Features

- **Multi-thread conversations** with sidebar
- **Real-time streaming** responses
- **Markdown rendering** with code highlighting
- **File attachments** support
- **Dark mode** support
- **Responsive design**

### 📊 Sanitization Details

The system automatically:
1. Detects sensitive data in prompts
2. Masks credentials and personal info
3. Blocks or neutralizes threats
4. Logs warnings and modifications
5. Sends sanitized prompts to OpenAI

## Project Structure

```
agent-ui/
├── secure_agent/              # Next.js Frontend
│   ├── app/
│   │   ├── api/chat/
│   │   │   └── route.ts      # Chat endpoint with sanitization
│   │   ├── assistant.tsx      # Main chat interface
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── components/
│   │   ├── assistant-ui/     # Chat UI components
│   │   └── ui/               # Reusable UI components
│   ├── lib/
│   │   ├── sanitizer-client.ts  # Backend API client
│   │   └── utils.ts
│   └── package.json
│
└── python-backend/            # Python Sanitization Service
    ├── app/
    │   ├── main.py           # FastAPI app
    │   ├── api/
    │   │   ├── routes.py     # API endpoints
    │   │   └── models.py     # Pydantic models
    │   ├── core/
    │   │   ├── config.py     # Configuration
    │   │   └── security.py   # Security validator
    │   └── utils/
    │       └── logger.py
    ├── requirements.txt
    └── README.md
```

## API Documentation

### Python Backend API

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

### Main Endpoints

- `POST /api/sanitize` - Sanitize a prompt
- `POST /api/sanitize/batch` - Batch sanitization
- `GET /api/health` - Health check
- `GET /api/stats` - Performance statistics
- `GET /api/security/level` - Get security level
- `PUT /api/security/level` - Update security level

## Configuration

### Security Levels

| Level  | Description | Use Case |
|--------|-------------|----------|
| `low` | Basic masking, warnings only | Development |
| `medium` | Blocks high-confidence threats | Production (default) |
| `high` | Strict validation, aggressive blocking | High-security |

### Environment Variables

#### Frontend (`secure_agent/.env.local`)
```env
OPENAI_API_KEY=                        # Required
NEXT_PUBLIC_SANITIZER_API_URL=         # Default: http://localhost:8003
NEXT_PUBLIC_SANITIZER_TIMEOUT_MS=      # Default: 5000
NEXT_PUBLIC_SANITIZER_ENABLED=         # Default: true
```

#### Backend (`python-backend/.env`)
```env
PORT=                                  # Default: 8003
HOST=                                  # Default: 0.0.0.0
CORS_ORIGINS=                          # Default: http://localhost:3000
LOG_LEVEL=                             # Default: INFO
DEFAULT_SECURITY_LEVEL=                # Default: medium
```

## Development

### Running Tests

```bash
# Backend tests
cd python-backend
pytest

# Frontend tests
cd secure_agent
npm test
```

### Adding Security Categories

Edit `python-backend/app/core/security.py`:

```python
self.security_categories = [
    "contains password or secret credentials",
    "your custom category here",
    # ...
]
```

### Customizing Sanitization

Modify methods in `ZeroShotSecurityValidator` class:
- `_sanitize_high_entropy_credentials()`
- `_sanitize_credentials_generic()`
- `_sanitize_malicious_content()`
- etc.

## Troubleshooting

### Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Frontend Can't Connect to Backend

1. Check backend is running: `curl http://localhost:8003/api/health`
2. Check CORS settings in `python-backend/.env`
3. Verify `NEXT_PUBLIC_SANITIZER_API_URL` in frontend `.env.local`

### Sanitization Taking Too Long

- First request is slow (model loading): ~2-3s
- Increase timeout: `NEXT_PUBLIC_SANITIZER_TIMEOUT_MS=10000`
- Consider using GPU for faster inference

### Memory Issues

The ML models require ~1.5GB RAM. If you have limited memory:
- Use the fallback model (automatically tries distilbert)
- Reduce batch sizes
- Restart the backend periodically

## Performance

| Metric | Value |
|--------|-------|
| First request | ~2-3s (model load) |
| Subsequent requests | ~100-500ms |
| Memory usage | ~1.5GB |
| Model size | ~1.6GB (BART) + ~15MB (spaCy) |
| Concurrent requests | Supported |

## Production Deployment

### Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment

1. **Backend**: Use gunicorn with uvicorn workers
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Frontend**: Build and deploy
   ```bash
   npm run build
   npm start
   ```

## License

Part of the SecureMCP project.

## Contributing

See the main SecureMCP repository for contributing guidelines.
