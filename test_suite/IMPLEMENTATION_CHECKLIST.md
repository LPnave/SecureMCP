# Test Suite Implementation Checklist

## ✅ Completed Components

### Core Files
- [x] `config.py` - Configuration management
- [x] `mcp_client.py` - MCP protocol client for zeroshotmcp
- [x] `agentui_client.py` - REST API client for agent-ui
- [x] `results_manager.py` - Results tracking and checkpointing
- [x] `test_runner.py` - Main test orchestrator
- [x] `report_generator.py` - HTML dashboard generator
- [x] `verify_setup.py` - Setup verification utility

### Documentation
- [x] `README.md` - Complete documentation
- [x] `QUICKSTART.md` - 5-minute quick start guide
- [x] `IMPLEMENTATION_CHECKLIST.md` - This file
- [x] `requirements.txt` - Python dependencies

### Test Data
- [x] `../testcases.csv` - 600 test prompts across 6 scopes

### Directories
- [x] `checkpoints/` - Checkpoint storage
- [x] `results/` - Test results storage
- [x] `reports/` - HTML reports storage

## 📋 Pre-Run Checklist

Before running tests, ensure:

- [ ] Both servers are running:
  - [ ] zeroshotmcp on port 8002
  - [ ] agent-ui backend on port 8003
- [ ] Dependencies installed:
  - [ ] httpx
  - [ ] tqdm (optional but recommended)
- [ ] Test cases file exists:
  - [ ] `testcases.csv` in project root
  - [ ] Contains 600 test cases

### Verify Setup

Run the verification script:

```bash
python test_suite/verify_setup.py
```

For a quick functionality test:

```bash
python test_suite/verify_setup.py --quick-test
```

## 🚀 Running Tests

### Full Test Suite (1,800 tests)

```bash
python test_suite/test_runner.py
```

This will:
- Test all 600 prompts
- Test both applications (zeroshotmcp, agent-ui)
- Test all 3 security levels (low, medium, high)
- Take approximately 15-30 minutes

### Resume Interrupted Tests

If tests are interrupted (Ctrl+C):

```bash
# List available sessions
python test_suite/test_runner.py --list-checkpoints

# Resume specific session
python test_suite/test_runner.py --resume <session_id>
```

## 📊 Generate Report

After tests complete:

```bash
python test_suite/report_generator.py <session_id>
```

The session ID is displayed when tests start and finish.

## 📁 Output Files

After running tests, you'll have:

```
test_suite/
├── checkpoints/
│   └── checkpoint_<session_id>.json
├── results/
│   ├── test_results_<session_id>.csv
│   └── stats_<session_id>.json
└── reports/
    └── report_<session_id>.html
```

## 🔍 What Gets Tested

### Applications (2)
1. **zeroshotmcp** - MCP application on port 8002
2. **agentui** - REST API backend on port 8003

### Security Levels (3)
1. **Low** - Lenient thresholds
2. **Medium** - Balanced security
3. **High** - Strict detection

### Scopes (6)
1. **Injection** (100 tests) - Prompt injection attempts
2. **Malicious** (100 tests) - Destructive commands
3. **Credentials** (100 tests) - API keys, passwords
4. **Personal** (100 tests) - PII, emails, SSNs
5. **Jailbreak** (100 tests) - Manipulation tactics
6. **Legitimate** (100 tests) - Normal dev questions

**Total: 600 × 2 × 3 = 1,800 tests**

## ✨ Features Implemented

### Test Execution
- [x] Parallel application testing
- [x] Multiple security level testing
- [x] Automatic retry on failure (3 attempts)
- [x] Timeout protection (30 seconds)
- [x] Error handling and logging

### Progress Tracking
- [x] Real-time progress bar with ETA
- [x] Current test details display
- [x] Throughput metrics
- [x] Tests remaining counter

### Checkpoint System
- [x] Auto-save every 50 tests
- [x] Resume from any checkpoint
- [x] Multiple session support
- [x] No data loss on interruption

### Results Collection
- [x] Detailed CSV output
- [x] JSON statistics
- [x] Pass/fail evaluation
- [x] Performance metrics
- [x] Error tracking

### HTML Dashboard
- [x] Overview statistics cards
- [x] Interactive pie chart (overall results)
- [x] Bar charts (by scope, level, application)
- [x] Application comparison table
- [x] Searchable data table
- [x] Filter by: app, level, scope, status
- [x] Responsive design
- [x] Export capabilities

### Developer Experience
- [x] Clear command-line interface
- [x] Helpful error messages
- [x] Setup verification script
- [x] Comprehensive documentation
- [x] Quick start guide

## 🎯 Pass/Fail Criteria

Tests are automatically evaluated:

| Scope | Expected | Pass If |
|-------|----------|---------|
| injection | Block | Blocked OR threats detected |
| malicious | Block | Blocked OR threats detected |
| credentials | Sanitize | Prompt was modified |
| personal | Sanitize | Prompt was modified |
| jailbreak | Block | Blocked OR threats detected |
| legitimate | Allow | NOT blocked |

## 📈 Expected Results

### Performance
- **Duration**: 15-30 minutes for full suite
- **Throughput**: 1-2 tests/second
- **Per Test**: 300-800ms average

### Metrics Tracked
- Total tests run
- Pass/fail/error counts
- Pass rate percentage
- Execution time per test
- Threats detected
- Confidence scores
- Sanitization applied

### Comparisons
- zeroshotmcp vs agent-ui
- Low vs medium vs high security
- Scope-specific performance
- Application-specific pass rates

## 🛠️ Troubleshooting

### Server Not Responding
- Ensure servers are running on correct ports
- Check server logs for errors
- Verify no port conflicts

### Test Cases Not Found
- Run from project root directory
- Ensure `testcases.csv` exists
- Check file permissions

### Import Errors
- Install dependencies: `pip install httpx tqdm`
- Check Python version (3.8+)

### Timeout Errors
- Increase timeout in `config.py`
- Check server performance
- Verify ML models loaded

### Slow Performance
- Normal for ML model inference
- Consider GPU acceleration
- Reduce test scope for quick tests

## 📝 Next Steps

After running the test suite:

1. **Review Dashboard** - Open the HTML report in browser
2. **Analyze Results** - Look at pass/fail rates
3. **Compare Applications** - See zeroshotmcp vs agent-ui differences
4. **Investigate Failures** - Review failed tests in CSV
5. **Test Security Levels** - Understand behavior differences
6. **Iterate** - Improve sanitization, add tests, rerun

## 🎉 Success Criteria

Your test suite is working correctly if:

- ✅ All 1,800 tests complete
- ✅ Pass rate > 85%
- ✅ No errors (or < 1%)
- ✅ Both applications tested
- ✅ HTML dashboard generated
- ✅ Results saved to CSV

## 📚 Resources

- **Full Docs**: `test_suite/README.md`
- **Quick Start**: `test_suite/QUICKSTART.md`
- **Summary**: `TEST_SUITE_SUMMARY.md`
- **Config**: `test_suite/config.py`

## 🚦 Ready to Test!

Everything is implemented and ready. To begin:

```bash
# 1. Verify setup
python test_suite/verify_setup.py --quick-test

# 2. Run full test suite
python test_suite/test_runner.py

# 3. Generate report
python test_suite/report_generator.py <session_id>
```

Good luck! 🎯

