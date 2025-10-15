# SecureMCP Agent UI - Setup Guide

## Architecture Overview

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│   Next.js   │─────▶│  Python Backend  │─────▶│  GPT-OSS    │
│  Frontend   │      │  (FastAPI)       │      │  (Docker)   │
│             │◀─────│  - Sanitization  │◀─────│             │
└─────────────┘      │  - ML Models     │      └─────────────┘
                     └──────────────────┘
```

**Flow:**
1. User sends message in Next.js frontend
2. Frontend → Python Backend (`/api/chat`)
3. Python Backend:
   - Sanitizes prompt using zero-shot ML model
   - Forwards sanitized prompt to GPT-OSS
   - Returns AI response to frontend
4. Frontend displays response

## Prerequisites

1. **Python 3.9+** installed
2. **Node.js 18+** and npm installed
3. **GPT-OSS Docker** running locally

## Setup Instructions

### 1. Python Backend Setup

```bash
cd agent-ui/python-backend

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create .env file
cat > .env << EOF
PORT=8003
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=INFO
DEFAULT_SECURITY_LEVEL=medium
MODEL_CACHE_DIR=./models
USE_GPU=auto

# Update this to match your GPT-OSS Docker setup
GPT_OSS_URL=http://localhost:8080/v1/chat/completions
GPT_OSS_MODEL=gpt-3.5-turbo
EOF

# Start the backend
python -m app.main
```

**The backend will:**
- Load ML models (BART for zero-shot classification)
- Load spaCy for NLP pattern detection
- Start FastAPI server on port 8003
- Be ready to accept chat requests

### 2. Frontend Setup

```bash
cd agent-ui/secure_agent

# Remove old OpenAI dependency and install
npm install

# Create .env.local file (optional, defaults work)
cat > .env.local << EOF
NEXT_PUBLIC_SANITIZER_API_URL=http://localhost:8003
NEXT_PUBLIC_SANITIZER_ENABLED=true
NEXT_PUBLIC_SANITIZER_TIMEOUT_MS=5000
EOF

# Start frontend
npm run dev
```

### 3. GPT-OSS Docker Setup

Make sure your GPT-OSS Docker container is running and accessible:

```bash
# Example: Check if GPT-OSS is running
curl http://localhost:8080/v1/models

# Update GPT_OSS_URL in python-backend/.env if using different port
```

**Common GPT-OSS ports:**
- `8080` - Default port
- `11434` - Ollama default
- `5000` - Some custom setups

**Update the `.env` accordingly:**
```bash
# For Ollama
GPT_OSS_URL=http://localhost:11434/v1/chat/completions

# For custom Docker setup
GPT_OSS_URL=http://localhost:YOUR_PORT/v1/chat/completions
```

## Running Everything Together

### Option 1: Run Separately (Recommended for Development)

**Terminal 1 - Python Backend:**
```bash
cd agent-ui/python-backend
python -m app.main
```

**Terminal 2 - Next.js Frontend:**
```bash
cd agent-ui/secure_agent
npm run dev
```

**Terminal 3 - Check GPT-OSS:**
```bash
# Make sure GPT-OSS Docker is running
docker ps | grep gpt
```

### Option 2: Use npm script (Frontend + Backend)

```bash
cd agent-ui/secure_agent
npm run dev:full
```

This runs both frontend and backend using `concurrently`.

## Testing the Integration

### 1. Test Python Backend Health

```bash
curl http://localhost:8003/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime_seconds": 12.34,
  "version": "1.0.0"
}
```

### 2. Test Sanitization Endpoint

```bash
curl -X POST http://localhost:8003/api/sanitize \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, my password is secret123", "security_level": "medium"}'
```

Expected: Sanitized output with `[REDACTED]`

### 3. Test Chat Endpoint (Backend)

```bash
curl -X POST http://localhost:8003/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "security_level": "medium"
  }'
```

Expected: AI response from GPT-OSS

### 4. Test Full Flow (Frontend)

1. Open browser: `http://localhost:3000`
2. Type a message: "Hello, what can you help me with?"
3. Check browser console for logs:
   - `[Chat] Received X messages`
   - `[Chat] Sanitization was applied` (if sensitive data detected)

## Configuration

### Python Backend Configuration

Edit `agent-ui/python-backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8003 | Backend server port |
| `HOST` | 0.0.0.0 | Host to bind to |
| `CORS_ORIGINS` | localhost:3000,3001 | Allowed CORS origins |
| `LOG_LEVEL` | INFO | Logging level |
| `DEFAULT_SECURITY_LEVEL` | medium | Security: low, medium, high |
| `GPT_OSS_URL` | localhost:8080/v1/... | Your GPT-OSS endpoint |
| `GPT_OSS_MODEL` | gpt-3.5-turbo | Model name for GPT-OSS |

### Frontend Configuration

Create `agent-ui/secure_agent/.env.local`:

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_SANITIZER_API_URL` | http://localhost:8003 | Python backend URL |
| `NEXT_PUBLIC_SANITIZER_ENABLED` | true | Enable sanitization |
| `NEXT_PUBLIC_SANITIZER_TIMEOUT_MS` | 5000 | Request timeout |

## Troubleshooting

### Backend Won't Start

**Issue:** `ModuleNotFoundError: No module named 'app'`

**Fix:** Run from python-backend directory:
```bash
cd agent-ui/python-backend
python -m app.main
```

### Frontend Can't Connect to Backend

**Issue:** 422 or 503 errors

**Fix 1:** Check if backend is running:
```bash
curl http://localhost:8003/api/health
```

**Fix 2:** Check CORS configuration in backend `.env`:
```
CORS_ORIGINS=http://localhost:3000
```

### GPT-OSS Connection Failed

**Issue:** `503 - Cannot connect to AI model`

**Fixes:**
1. Check if GPT-OSS Docker is running:
   ```bash
   docker ps
   ```

2. Verify GPT-OSS URL:
   ```bash
   curl http://localhost:8080/v1/models
   ```

3. Update `GPT_OSS_URL` in backend `.env`

### Sanitization Not Working

**Issue:** Sensitive data not being redacted

**Fix:** Check security level in backend:
```bash
curl http://localhost:8003/api/security/level
```

Update if needed:
```bash
curl -X PUT http://localhost:8003/api/security/level \
  -H "Content-Type: application/json" \
  -d '{"level": "high"}'
```

### Models Taking Too Long to Load

**Issue:** Backend startup is slow

**Expected:** First startup downloads models (~500MB)
- BART model: ~400MB
- spaCy model: ~50MB

**Solution:** Be patient on first run. Subsequent starts are fast (models cached).

## API Endpoints

### Python Backend (`http://localhost:8003`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/sanitize` | POST | Sanitize single prompt |
| `/api/sanitize/batch` | POST | Sanitize multiple prompts |
| `/api/chat` | POST | Chat with sanitization + GPT-OSS |
| `/api/security/level` | GET | Get security level |
| `/api/security/level` | PUT | Update security level |
| `/api/stats` | GET | Get statistics |

### Frontend (`http://localhost:3000`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Chat endpoint (forwards to backend) |

## Security Levels

### Low
- Basic pattern detection
- Minimal false positives
- Faster processing

### Medium (Recommended)
- Balanced detection
- Zero-shot classification
- Entropy-based detection
- Good for most use cases

### High
- Aggressive detection
- May have false positives
- Maximum security
- Best for sensitive environments

## Performance Notes

- **First Request:** ~2-3 seconds (model warmup)
- **Subsequent Requests:** ~500-1000ms
- **With GPU:** ~200-400ms
- **Memory Usage:** ~2GB (with models loaded)

## Development Tips

1. **Hot Reload:**
   - Frontend: Enabled by default (Next.js)
   - Backend: Use `--reload` flag with uvicorn

2. **Debugging:**
   - Backend logs: Check console output
   - Frontend logs: Browser console
   - Network: Browser DevTools → Network tab

3. **Testing Sanitization:**
   ```bash
   # Test with sensitive data
   curl -X POST http://localhost:8003/api/chat \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [
         {"role": "user", "content": "My password is admin123"}
       ]
     }'
   ```

## Next Steps

1. **Customize Security Rules:** Edit `app/core/security.py`
2. **Add More Models:** Update `zeroshot_config.py`
3. **Enhance UI:** Modify Next.js components
4. **Add Logging:** Configure logging in `.env`

## Support

For issues or questions:
1. Check logs in backend console
2. Check browser console for frontend errors
3. Verify all services are running
4. Check configuration files

---

**Happy Chatting! 🚀**

