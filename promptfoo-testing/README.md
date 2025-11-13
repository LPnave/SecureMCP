# Promptfoo Testing for Agent-UI

This directory contains the setup for testing Agent-UI security filter using Promptfoo via an adapter.

## ⚡ **100 Comprehensive Security Tests**

Your configuration now includes **100 curated security tests** from your `testcases_quick.csv`!

**Quick Start:**
1. Start Agent-UI and Adapter (see Quick Start section below)
2. Run: `.\run-redteam.bat` or `promptfoo eval`
3. View results: `promptfoo view`

**Test Coverage:**
- ✅ Prompt Injection (17 tests)
- ✅ Malicious Code (17 tests)
- ✅ Credentials (17 tests)
- ✅ Personal Information (17 tests)
- ✅ Jailbreak (17 tests)
- ✅ Legitimate Queries (15 tests)

---

## 🎯 Architecture

```
Promptfoo → Adapter (Port 8005) → Agent-UI (Port 8003)
```

The adapter translates between:
- **Input**: Promptfoo's OpenAI-compatible requests
- **Output**: Agent-UI's security filter responses

## 📋 Prerequisites

1. **Python 3.11+** with FastAPI and uvicorn
2. **Node.js** with Promptfoo installed
3. **Agent-UI running** on port 8003

## 🚀 Quick Start

### Step 1: Install Adapter Dependencies

```powershell
# Install Python dependencies
pip install fastapi uvicorn requests

# Or if using venv:
cd ..\agent-ui\python-backend
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn requests
```

### Step 2: Start All Services

You need **3 terminals**:

**Terminal 1: Start Agent-UI**
```powershell
cd C:\Users\lahirun\Lahiru\Masters\Final_Project\SecureMCP\agent-ui\python-backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8003
```

**Terminal 2: Start Adapter**
```powershell
cd C:\Users\lahirun\Lahiru\Masters\Final_Project\SecureMCP\promptfoo-testing
python agentui_adapter.py
```

**Terminal 3: Run Promptfoo**
```powershell
cd C:\Users\lahirun\Lahiru\Masters\Final_Project\SecureMCP\promptfoo-testing
promptfoo eval
```

### Step 3: View Results

```powershell
# View in browser
promptfoo view

# Or check results file
cat results\promptfoo-results.json
```

## 📊 What Gets Tested

The configuration tests:

### Attack Categories:
- ✅ **Prompt Injection** (ignore instructions, system override)
- ✅ **Jailbreak Attempts** (DAN, developer mode)
- ✅ **PII Extraction** (email, passwords)
- ✅ **SQL Injection** (DROP TABLE, OR 1=1)
- ✅ **Malicious Code** (system commands, malware)

### Legitimate Queries:
- ✅ Math questions
- ✅ Security questions (educational)
- ✅ Programming help

## 🔍 Understanding Results

### Promptfoo Output:

```
✓ Test: Prompt Injection: Ignore Instructions
  Output: [SECURITY BLOCKED: prompt_injection] Sanitized output: ...
  PASS

✗ Test: Legitimate: Math Question
  Output: [SECURITY BLOCKED: ...] 
  FAIL (False positive - legitimate query was blocked)
```

### What to Look For:

- **Attacks marked PASS** = Agent-UI successfully blocked ✅
- **Attacks marked FAIL** = Potential bypass ❌
- **Legitimate marked PASS** = Correctly allowed ✅
- **Legitimate marked FAIL** = False positive (over-blocking) ⚠️

## 🎛️ Configuration

### Testing Different Security Levels

Edit `promptfooconfig.yaml` to test different security levels:

```yaml
# Add to tests section:
- description: "Test at HIGH security"
  vars:
    prompt: "{{prompt}}"
  provider:
    id: openai:gpt-3.5-turbo
    config:
      apiBaseUrl: http://localhost:8005/v1
      # Could modify adapter to accept security_level parameter
```

### Adding Custom Tests

Add more test cases to `promptfooconfig.yaml`:

```yaml
tests:
  - description: "Your custom test"
    vars:
      prompt: "Your test prompt here"
    assert:
      - type: contains
        value: "[SECURITY BLOCKED"  # For attacks
      # or
      - type: not-contains
        value: "[SECURITY BLOCKED"  # For legitimate queries
```

## 🐛 Troubleshooting

### Issue: "Connection refused" to port 8005

```powershell
# Check if adapter is running:
curl http://localhost:8005/

# If not, start it:
python agentui_adapter.py
```

### Issue: "Connection refused" to port 8003

```powershell
# Check if Agent-UI is running:
curl http://localhost:8003/api/health

# If not, start it from agent-ui/python-backend:
python -m uvicorn app.main:app --reload --port 8003
```

### Issue: Promptfoo errors

```powershell
# Validate configuration:
promptfoo eval --dry-run

# Clear cache:
promptfoo cache clear

# Check Promptfoo version:
promptfoo --version
```

## 📈 Expected Results

Based on current Agent-UI implementation:

| Category | Expected Pass Rate | Notes |
|----------|-------------------|-------|
| Prompt Injection | 95-100% | Strong specialized model |
| Jailbreak | 85-95% | Pattern + context-aware |
| PII/Credentials | 90-95% | Specialized PII detector |
| SQL Injection | 95-100% | Good pattern coverage |
| Malicious Code | 85-90% | Pattern-based |
| **Legitimate** | 94-99% | Context-aware detection |
| **Overall** | 90-95% | Balanced security |

## 📁 Files

- `agentui_adapter.py` - FastAPI adapter translating Promptfoo ↔ Agent-UI
- `promptfooconfig.yaml` - Promptfoo configuration with test cases
- `results/` - Test results (JSON, HTML, etc.)
- `README.md` - This file

## 🔗 Resources

- [Promptfoo Documentation](https://promptfoo.dev/docs/)
- [Agent-UI API Documentation](../agent-ui/python-backend/README.md)
- [SecureMCP Documentation](../Documentation/SecureMCP_Technical_Documentation.md)

## 💡 Tips

1. **Start with Quick Test**: Run with just a few prompts first to verify setup
2. **Check Adapter Logs**: The adapter logs show what's being sent to Agent-UI
3. **Use Promptfoo View**: The web UI (`promptfoo view`) is much easier to analyze than JSON
4. **Add Failures to Test Suite**: Any bypasses found should be added to your main test suite
5. **Test Incrementally**: Add test cases gradually to understand what's working

## 🎉 Next Steps

After successful testing:

1. **Analyze bypasses** - Check which attacks got through
2. **Add to main test suite** - Update `testcases.csv` with findings
3. **Improve detection** - Fix any vulnerabilities found
4. **Re-test** - Verify improvements with Promptfoo
5. **Document** - Add findings to analysis folder

