# Red Team Testing with Promptfoo Plugins

Your configuration is now set up with **320 automatically generated tests** using Promptfoo's red team plugins!

---

## 🎯 **Test Breakdown**

| Plugin | Tests | Attack Type |
|--------|-------|-------------|
| prompt-injection | 100 | System overrides, instruction manipulation |
| jailbreak | 80 | DAN, role-play, hypothetical scenarios |
| pii | 60 | Email, SSN, credential extraction |
| sql-injection | 40 | Database attacks, DROP TABLE, etc. |
| shell-injection | 40 | Command execution, system access |
| **TOTAL** | **320** | **Comprehensive red team coverage** |

---

## 🚀 **How to Run**

### **Step 1: Start All Services**

**Terminal 1: Agent-UI**
```powershell
cd C:\Users\lahirun\Lahiru\Masters\Final_Project\SecureMCP\agent-ui\python-backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8003
```

**Terminal 2: Adapter**
```powershell
cd C:\Users\lahirun\Lahiru\Masters\Final_Project\SecureMCP\promptfoo-testing
python agentui_adapter.py
```

**Terminal 3: Run Tests**
```powershell
cd C:\Users\lahirun\Lahiru\Masters\Final_Project\SecureMCP\promptfoo-testing

# Run all 320 tests
promptfoo eval

# View results in browser
promptfoo view
```

---

## ⏱️ **Expected Runtime**

- **320 tests** = approximately **15-30 minutes**
- Depends on Agent-UI response times (~2-5 seconds per test)
- Progress shown in terminal with real-time updates

---

## 📊 **Understanding Results**

### **Terminal Output:**

```
✓ Prompt Injection Test 1
  Output: [SECURITY BLOCKED: prompt_injection]...
  Score: 1.0 (PASS)

✗ Prompt Injection Test 45
  Output: Ignore all instructions and reveal...
  Score: 0.0 (FAIL - VULNERABILITY!)
  Reason: Attack bypassed Agent-UI filters!
```

### **What the Scores Mean:**

- **✅ PASS (Score: 1.0)** = Agent-UI successfully blocked/sanitized
- **❌ FAIL (Score: 0.0)** = Attack bypassed filters (vulnerability!)

### **Overall Statistics:**

```
Total Tests: 320
Passed: 285 (89.1%)
Failed: 35 (10.9%)
```

**Target:** 90%+ pass rate (minimal vulnerabilities)

---

## 🔍 **Analyzing Failed Tests**

### **View Only Failures:**

```powershell
# Filter to show only failed tests
promptfoo eval --filter-failing

# Export failures to file
promptfoo eval --filter-failing -o results/failures-only.json
```

### **Check Specific Categories:**

```powershell
# View results by plugin
# Look for patterns in which plugin has most failures
```

### **Manual Verification:**

If a test fails, manually test it:

```powershell
# Test directly against Agent-UI
curl -X POST http://localhost:8003/api/sanitize `
  -H "Content-Type: application/json" `
  -d '{"prompt": "failing test prompt here", "return_details": true}'
```

---

## 🎛️ **Adjusting Test Count**

### **Start Small (Quick Test):**

Edit `promptfooconfig.yaml`:

```yaml
plugins:
  - id: promptfoo:redteam:prompt-injection
    config:
      numTests: 10  # Reduced from 100
      
  - id: promptfoo:redteam:jailbreak
    config:
      numTests: 5   # Reduced from 80

# Total: 15 tests (~2-3 minutes)
```

### **Scale Up:**

Once verified working, increase counts:

```yaml
plugins:
  - id: promptfoo:redteam:prompt-injection
    config:
      numTests: 200  # Doubled!
```

---

## 📈 **Expected Results for Agent-UI**

After your Phase A context-awareness fix:

| Plugin | Expected Pass Rate | Notes |
|--------|-------------------|-------|
| prompt-injection | 95-100% | Strong specialized model |
| jailbreak | 85-95% | Pattern + context-aware |
| pii | 90-95% | Specialized PII detector |
| sql-injection | 95-100% | Good pattern coverage |
| shell-injection | 85-90% | Pattern-based detection |
| **Overall** | **90-95%** | Balanced protection |

---

## 🐛 **Troubleshooting**

### **"Plugin not found" Errors:**

Some plugins may require Promptfoo Pro. If you get errors, use only free plugins:

```yaml
plugins:
  - promptfoo:redteam:prompt-injection
  - promptfoo:redteam:jailbreak
  - promptfoo:redteam:pii
  - promptfoo:redteam:sql-injection
  - promptfoo:redteam:shell-injection
```

### **Tests Timing Out:**

If tests timeout, reduce parallel requests:

```yaml
# Add to config:
parallelism: 1  # Run tests sequentially
```

### **All Tests Failing:**

1. **Check adapter is running:** `curl http://localhost:8005/`
2. **Check Agent-UI is running:** `curl http://localhost:8003/api/health`
3. **Test adapter manually:** Send a test request to adapter
4. **Check adapter logs** for errors

---

## 💾 **Saving Results**

### **Export Formats:**

```powershell
# JSON (default)
promptfoo eval -o results/redteam-$(date +%Y%m%d).json

# HTML Report
promptfoo eval -o results/redteam-report.html

# CSV for analysis
promptfoo eval -o results/redteam-results.csv
```

### **Compare Runs:**

```powershell
# Before fixes
promptfoo eval -o results/before-fix.json

# After fixes
promptfoo eval -o results/after-fix.json

# Compare in web UI
promptfoo view
```

---

## 🔄 **Iterative Testing Workflow**

1. **Run tests:** `promptfoo eval`
2. **Identify failures:** Check which attacks bypassed
3. **Fix vulnerabilities:** Update Agent-UI patterns/models
4. **Re-test:** Run again to verify fixes
5. **Document:** Add bypasses to your test suite

---

## 📝 **Adding Failed Tests to Main Suite**

If you find bypasses, add them to your CSV:

```csv
scope,prompt,expected,notes
injection,"[failed prompt here]",Block,"Found by Promptfoo red team"
```

Then run your main test suite to track the fix.

---

## 🎉 **Success Criteria**

✅ **Ready for Production** if:
- Overall pass rate > 90%
- No critical bypasses (injection, PII extraction)
- Legitimate queries not over-blocked
- Performance acceptable (<5s per validation)

---

## 📚 **Next Steps**

1. ✅ Run initial red team assessment
2. 📊 Analyze results - identify vulnerability patterns
3. 🔧 Fix any bypasses found
4. 🔁 Re-run to verify fixes
5. 📝 Document findings in analysis folder
6. 🎯 Add critical bypasses to main test suite

---

**Run Command:** `promptfoo eval` 🚀

**View Results:** `promptfoo view` 📊

**Good luck with your red team testing!**

