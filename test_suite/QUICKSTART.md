# Test Suite Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
pip install httpx tqdm
```

### 2. Start Servers

**Terminal 1 - Start zeroshotmcp:**
```bash
cd zeroshotmcp
python zeroshot_secure_mcp.py
```

**Terminal 2 - Start agent-ui backend:**
```bash
cd agent-ui/python-backend
# Windows:
start.bat
# Linux/Mac:
./start.sh
```

Wait for both servers to show "Running on..."

### 3. Run Tests

**Terminal 3 - Run test suite:**
```bash
# From project root

# Quick test (100 prompts, ~5-10 minutes)
python test_suite/test_runner.py --quick

# OR Full test (600 prompts, ~30-60 minutes)
python test_suite/test_runner.py
```

### 4. View Results

The test runner will display the session ID. Use it to generate the HTML report:

```bash
python test_suite/report_generator.py <session_id>
```

Open the generated HTML file in your browser to view the interactive dashboard.

## What Happens During Tests?

1. **Loads test prompts** from CSV file (100 for quick test, 600 for full test)
2. **Tests each prompt** against:
   - zeroshotmcp (MCP application on port 8002)
   - agent-ui (REST API on port 8003)
3. **Tests each at 3 security levels:**
   - Low (lenient)
   - Medium (balanced)
   - High (strict)
4. **Total: 1,800 tests** (600 × 2 apps × 3 levels)

## Expected Timeline

- **Setup**: 2-3 minutes
- **Test Execution**: 15-30 minutes
- **Report Generation**: < 1 minute

## Sample Output

```
======================================================================
SecureMCP Test Suite
======================================================================
Test Cases: 600
Applications: zeroshotmcp, agentui
Security Levels: low, medium, high
Total Tests: 1800
Session ID: 20250102_143022
======================================================================

Verifying server connectivity...
  zeroshotmcp (port 8002): ✓ OK
  agent-ui (port 8003): ✓ OK

Running tests: 100% |███████████| 1800/1800 [15:23<00:00, 1.95test/s]

Overall Results:
  Total Tests:     1800
  Passed:          1654 ( 91.9%)
  Failed:           132 (  7.3%)
  Errors:            14 (  0.8%)
```

## Interrupt and Resume

If you need to stop tests (Ctrl+C):

```bash
# Resume later
python test_suite/test_runner.py --resume <session_id>
```

## View Dashboard

The HTML dashboard includes:
- 📊 Interactive charts
- 📈 Performance metrics
- 🔍 Searchable results table
- ⚖️ Application comparison

## Troubleshooting

**Problem**: "servers are not responding"
- **Solution**: Ensure both servers are running on ports 8002 and 8003

**Problem**: "testcases.csv not found"
- **Solution**: Run from project root directory

**Problem**: Tests are slow
- **Solution**: Normal - ML models take time. Grab a coffee! ☕

## Next Steps

- Review the HTML dashboard
- Analyze failed tests in the CSV
- Compare zeroshotmcp vs agent-ui performance
- Test with different security levels
- Add more test cases to `testcases.csv`

## Need Help?

See full documentation: `test_suite/README.md`

