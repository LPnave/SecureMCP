# 🎉 Promptfoo Red Team Testing - Setup Complete!

Your Promptfoo red team testing environment is now fully configured with **automated plugin-based testing**!

---

## ✅ What's Been Set Up

### **1. Configuration File (`promptfooconfig.yaml`)**

- **100 Explicit Security Tests** covering:
  - ✅ Prompt Injection (17 tests)
  - ✅ Malicious Code (17 tests)
  - ✅ Credentials (17 tests)
  - ✅ Personal Information (17 tests)
  - ✅ Jailbreak Attempts (17 tests)
  - ✅ Legitimate Queries (15 tests)
- **Total: 100 comprehensive security tests**
- Smart assertion logic to detect blocking/sanitization
- Results saved to `./results/promptfoo-results.json`

### **2. Documentation**

- **`REDTEAM_GUIDE.md`**: Complete guide with:
  - How to run tests
  - Understanding results
  - Troubleshooting tips
  - Analysis workflow
  - Expected performance benchmarks

- **`README.md`**: Updated with red team quick start

- **`ADAPTER_PLAN.md`**: Technical architecture details

- **`QUICKSTART.md`**: Step-by-step setup guide

### **3. Helper Scripts**

- **`run-redteam.bat`**: Automated test runner
  - Pre-flight checks (adapter/Agent-UI running)
  - Runs all 320 tests
  - Shows progress and results

- **`start-adapter.bat`**: Quick adapter startup

- **`agentui_adapter.py`**: OpenAI-compatible adapter (already created)

---

## 🚀 How to Run (3 Steps)

### **Step 1: Start Agent-UI**

```powershell
cd C:\Users\lahirun\Lahiru\Masters\Final_Project\SecureMCP\agent-ui\python-backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8003
```

### **Step 2: Start Adapter**

```powershell
cd C:\Users\lahirun\Lahiru\Masters\Final_Project\SecureMCP\promptfoo-testing
python agentui_adapter.py
```

### **Step 3: Run Red Team Tests**

**Option A - Using Batch Script (Recommended):**
```powershell
cd C:\Users\lahirun\Lahiru\Masters\Final_Project\SecureMCP\promptfoo-testing
.\run-redteam.bat
```

**Option B - Direct Command:**
```powershell
cd C:\Users\lahirun\Lahiru\Masters\Final_Project\SecureMCP\promptfoo-testing
promptfoo eval
```

### **Step 4: View Results**

```powershell
promptfoo view
```

This opens a web UI at `http://localhost:15500` with interactive results!

---

## ⏱️ What to Expect

- **Runtime**: ~5-10 minutes for all 100 tests
- **Progress**: Real-time updates in terminal
- **Results**: Detailed pass/fail for each test
- **Analysis**: Web UI with filtering and statistics

---

## 📊 Expected Results

Based on your Phase A context-awareness fixes, expect:

| Category | Tests | Expected Pass Rate |
|----------|-------|-------------------|
| Prompt Injection | 17 | 95-100% |
| Malicious Code | 17 | 90-95% |
| Credentials | 17 | 95-100% |
| Personal Information | 17 | 90-95% |
| Jailbreak | 17 | 85-95% |
| Legitimate Queries | 15 | 95-100% |
| **Overall** | **100** | **90-95%** |

---

## 🔍 Next Steps After Running

1. **Analyze Results**
   - Check overall pass rate
   - Identify failed tests (bypasses)
   - Look for patterns in failures

2. **Fix Vulnerabilities**
   - Update Agent-UI patterns/models
   - Add specific bypasses to your main test suite
   - Re-run to verify fixes

3. **Document Findings**
   - Add analysis to your Documentation folder
   - Track improvement over time
   - Update security documentation

4. **Compare with Main Test Suite**
   - Run: `python test_suite/test_runner.py`
   - Compare Promptfoo results with custom suite
   - Identify gaps or discrepancies

---

## 💡 Pro Tips

### **Start Small:**

For initial testing, edit `promptfooconfig.yaml` to reduce test counts:

```yaml
plugins:
  - id: promptfoo:redteam:prompt-injection
    config:
      numTests: 10  # Instead of 100
```

Then scale up once verified working!

### **Focus on Failures:**

```powershell
# View only failed tests
promptfoo eval --filter-failing
```

### **Manual Verification:**

If a test fails, verify manually:

```powershell
curl -X POST http://localhost:8003/api/sanitize `
  -H "Content-Type: application/json" `
  -d '{"prompt": "test prompt here", "return_details": true}'
```

---

## 📁 File Structure

```
promptfoo-testing/
├── promptfooconfig.yaml        # Main config with red team plugins
├── agentui_adapter.py          # OpenAI-compatible adapter
├── run-redteam.bat            # Automated test runner
├── start-adapter.bat          # Quick adapter startup
├── REDTEAM_GUIDE.md           # Detailed usage guide
├── SETUP_COMPLETE.md          # This file
├── README.md                  # General overview
├── QUICKSTART.md              # Step-by-step setup
├── ADAPTER_PLAN.md            # Technical architecture
└── results/                   # Test results saved here
    └── redteam-results.json   # Latest test run
```

---

## 🎯 Success Checklist

Before running tests, ensure:

- ✅ Promptfoo is installed (`npm install -g promptfoo`)
- ✅ Agent-UI is running on port 8003
- ✅ Adapter is running on port 8005
- ✅ `results/` directory exists (auto-created by script)

---

## 🐛 Quick Troubleshooting

### **"Plugin not found" Error:**

Some plugins may require Promptfoo Pro. If you see errors, the config already uses free plugins. Check:

```powershell
promptfoo --version
```

Update if needed:

```powershell
npm update -g promptfoo
```

### **Tests Timing Out:**

Add to `promptfooconfig.yaml`:

```yaml
parallelism: 1  # Run sequentially
```

### **Adapter Connection Issues:**

```powershell
# Check adapter
curl http://localhost:8005/health

# Check Agent-UI
curl http://localhost:8003/api/health
```

---

## 📞 Need Help?

1. **Check `REDTEAM_GUIDE.md`** for detailed instructions
2. **Review adapter logs** for connection issues
3. **Test manually** to isolate problems
4. **Check Promptfoo docs**: https://promptfoo.dev

---

## 🎉 You're Ready!

Your red team testing environment is fully set up. Run the tests and discover any security gaps!

**Start now:**
```powershell
.\run-redteam.bat
```

**Good luck! 🚀**

