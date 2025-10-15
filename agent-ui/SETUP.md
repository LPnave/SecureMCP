# 📦 Complete Setup Instructions

## System Requirements

| Component | Requirement |
|-----------|-------------|
| **Node.js** | 18.0.0 or higher |
| **Python** | 3.9.0 or higher |
| **RAM** | 2GB minimum, 4GB recommended |
| **Disk Space** | ~3GB (includes models) |
| **OS** | Windows, macOS, or Linux |

## Installation Steps

### Part 1: Frontend Setup (Next.js)

1. **Navigate to frontend directory:**
   ```bash
   cd agent-ui/secure_agent
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```
   
   Or if you prefer pnpm:
   ```bash
   pnpm install
   ```

3. **Create environment file:**
   
   Copy the example file:
   ```bash
   cp .env.local.example .env.local
   ```
   
   Or create manually:
   ```bash
   # On Windows
   notepad .env.local
   
   # On Mac/Linux
   nano .env.local
   ```
   
   Add the following content:
   ```env
   # Required: Your OpenAI API key
   OPENAI_API_KEY=sk-your-actual-api-key-here
   
   # Optional: Backend configuration
   NEXT_PUBLIC_SANITIZER_API_URL=http://localhost:8003
   NEXT_PUBLIC_SANITIZER_TIMEOUT_MS=5000
   NEXT_PUBLIC_SANITIZER_ENABLED=true
   ```

4. **Get your OpenAI API key:**
   - Go to https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy and paste into `.env.local`

5. **Verify installation:**
   ```bash
   npm run dev
   ```
   
   You should see:
   ```
   ▲ Next.js 15.5.4
   - Local:        http://localhost:3000
   ```

---

### Part 2: Backend Setup (Python)

1. **Navigate to backend directory:**
   ```bash
   cd ../python-backend
   ```

2. **Create virtual environment (recommended):**
   
   **Linux/Mac:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   
   **Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   This will install:
   - FastAPI & Uvicorn (web server)
   - Transformers & Torch (ML models)
   - spaCy (NLP)
   - Other utilities

4. **Download spaCy language model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```
   
   Expected output:
   ```
   ✔ Download and installation successful
   ```

5. **Create environment file (optional):**
   
   The backend works with defaults, but you can customize:
   ```bash
   # Create .env file
   cat > .env << EOF
   PORT=8003
   HOST=0.0.0.0
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   LOG_LEVEL=INFO
   DEFAULT_SECURITY_LEVEL=medium
   MODEL_CACHE_DIR=./models
   USE_GPU=auto
   EOF
   ```

6. **Verify installation:**
   ```bash
   python app/main.py
   ```
   
   You should see:
   ```
   ============================================================
   Starting SecureMCP Python Backend
   ============================================================
   Loading ML models...
   ✓ Models loaded successfully in X.XX seconds
   ✓ Security level: medium
   ✓ Server ready to accept requests!
   ```

---

### Part 3: Running Both Services

You have three options:

#### ⭐ Option 1: Single Command (Easiest)

```bash
cd secure_agent
npm run dev:full
```

This starts both backend and frontend together!

#### Option 2: Separate Terminals

**Terminal 1 - Backend:**
```bash
cd python-backend
python app/main.py
```

**Terminal 2 - Frontend:**
```bash
cd secure_agent
npm run dev
```

#### Option 3: Startup Scripts

**Linux/Mac:**
```bash
# Terminal 1
cd python-backend
chmod +x start.sh
./start.sh

# Terminal 2
cd secure_agent
npm run dev
```

**Windows:**
```bash
# Terminal 1
cd python-backend
start.bat

# Terminal 2
cd secure_agent
npm run dev
```

---

## Verification

### 1. Check Backend Health

Open a new terminal:
```bash
curl http://localhost:8003/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime_seconds": 15.23,
  "version": "1.0.0"
}
```

### 2. Check Frontend

Visit: http://localhost:3000

You should see:
- Chat interface with sidebar
- "Hello there! How can I help you today?" welcome message
- Message input at the bottom

### 3. Test Sanitization

In the chat, type:
```
My password is Secret123
```

Check the backend terminal logs - you should see:
```
Sanitizing prompt...
Sanitization complete - Safe: True, Modified: True
```

The password should be masked before being sent to OpenAI!

---

## API Documentation

Once running, access the interactive API docs:

- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

Try the endpoints directly in the browser!

---

## Configuration Guide

### Security Levels

Edit `python-backend/.env`:

```env
DEFAULT_SECURITY_LEVEL=low     # Warnings only
DEFAULT_SECURITY_LEVEL=medium  # Balanced (default)
DEFAULT_SECURITY_LEVEL=high    # Strict blocking
```

### CORS Configuration

If running frontend on a different port:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://yourdomain.com
```

### Timeout Settings

Frontend `.env.local`:
```env
NEXT_PUBLIC_SANITIZER_TIMEOUT_MS=10000  # 10 seconds
```

### Disable Sanitization

For testing without sanitization:

```env
NEXT_PUBLIC_SANITIZER_ENABLED=false
```

---

## Common Setup Issues

### Issue: `npm install` fails

**Solution:**
```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Issue: `pip install` fails

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -v -r requirements.txt
```

### Issue: spaCy model download fails

**Solution:**
```bash
# Try direct download
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Verify
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('✓ Model loaded')"
```

### Issue: Port already in use

**Backend:**
```env
# Change PORT in python-backend/.env
PORT=8004

# Update frontend .env.local
NEXT_PUBLIC_SANITIZER_API_URL=http://localhost:8004
```

**Frontend:**
```bash
# Run on different port
npm run dev -- -p 3001
```

### Issue: Models taking too long to download

The BART model is ~1.6GB. On slow connections:
```bash
# Pre-download model
python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='facebook/bart-large-mnli')"
```

Or use the smaller fallback model (automatically tried if main model fails).

---

## Production Deployment

### Environment Variables

**Frontend:**
```env
OPENAI_API_KEY=sk-prod-key
NEXT_PUBLIC_SANITIZER_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_SANITIZER_ENABLED=true
```

**Backend:**
```env
PORT=8003
HOST=0.0.0.0
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=WARNING
DEFAULT_SECURITY_LEVEL=high
```

### Build Frontend

```bash
cd secure_agent
npm run build
npm start
```

### Run Backend in Production

```bash
cd python-backend
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8003
```

### Docker Deployment

Create `docker-compose.yml` in `agent-ui/`:

```yaml
version: '3.8'

services:
  backend:
    build: ./python-backend
    ports:
      - "8003:8003"
    environment:
      - PORT=8003
      - DEFAULT_SECURITY_LEVEL=medium
    
  frontend:
    build: ./secure_agent
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_SANITIZER_API_URL=http://backend:8003
    depends_on:
      - backend
```

Run:
```bash
docker-compose up -d
```

---

## Next Steps

✅ Read the [Quick Start Guide](QUICKSTART.md)  
✅ Check out the [main README](README.md)  
✅ Explore the [Backend API docs](http://localhost:8003/docs)  
✅ Customize security categories  
✅ Add your own sanitization rules  

---

## Getting Help

- 📖 [Full Documentation](README.md)
- 🐛 [Troubleshooting Guide](README.md#troubleshooting)
- 💬 Open an issue on GitHub
- 📧 Contact the development team

---

**Happy coding! 🚀**
