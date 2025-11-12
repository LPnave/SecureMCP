# SecureMCP Test Suite - Complete Implementation Summary

## Overview

I've created a comprehensive automated testing framework for your SecureMCP project. The test suite validates both the **zeroshotmcp** (MCP application) and **agent-ui** (REST API backend) implementations across all security configurations.

## What Has Been Implemented

### 1. Core Test Infrastructure

#### **test_suite/config.py**
- Configuration management for all test parameters
- Server URLs (zeroshotmcp: 8002, agent-ui: 8003)
- Security levels, retry logic, timeouts
- Pass/fail criteria definitions per scope
- Directory structure initialization

#### **test_suite/mcp_client.py**
- MCP protocol client for zeroshotmcp
- Calls MCP tools via HTTP POST requests
- Security level management
- Response parsing and standardization
- Error handling with automatic retries
- Health check functionality

#### **test_suite/agentui_client.py**
- REST API client for agent-ui backend
- Standard HTTP API communication
- Security level updates via `/api/security-level`
- Sanitization via `/api/sanitize`
- Response normalization
- Retry logic and error handling

#### **test_suite/results_manager.py**
- CSV results writer
- Checkpoint system (saves every 50 tests)
- Pass/fail evaluation engine
- Statistics aggregation
- Buffer management for performance
- Resume capability

#### **test_suite/test_runner.py**
- Main orchestrator
- Test execution flow management
- Progress tracking with tqdm
- Server health verification
- Checkpoint/resume implementation
- Summary statistics display
- Command-line interface

#### **test_suite/report_generator.py**
- HTML dashboard generator
- Interactive charts (Chart.js)
- Searchable data tables (DataTables)
- Application comparison
- Responsive design
- Export capabilities

### 2. Test Data

#### **testcases.csv**
- **600 software engineering-specific test prompts**
- **6 scopes** with 100 prompts each:
  - **Injection** (001-100): Prompt injection, instruction manipulation
  - **Malicious** (101-200): Destructive commands, exploits, malware
  - **Credentials** (201-300): API keys, passwords, tokens, secrets
  - **Personal** (301-400): PII, emails, SSNs, sensitive data
  - **Jailbreak** (401-500): Manipulation tactics, authority claims
  - **Legitimate** (501-600): Normal developer questions

Each test case includes:
- Item Number (001-600)
- Scope
- Prompt
- Expected Behavior (Block/Sanitize/Allow)
- Security Level
- Priority (Low/Medium/High)
- Result (Pending - filled during testing)
- Comments (NA - filled during testing)

### 3. Documentation

- **test_suite/README.md**: Complete documentation
- **test_suite/QUICKSTART.md**: 5-minute getting started guide
- **TEST_SUITE_SUMMARY.md**: This file

## How It Works

### Test Execution Flow

```
1. Load 600 test cases from testcases.csv
2. Initialize MCP and REST API clients
3. Verify both servers are running and responsive
4. For each of 600 test cases:
   a. For zeroshotmcp application:
      - Test at LOW security level
      - Test at MEDIUM security level
      - Test at HIGH security level
   b. For agentui application:
      - Test at LOW security level
      - Test at MEDIUM security level
      - Test at HIGH security level
5. Save results to CSV after each test
6. Save checkpoint every 50 tests
7. Generate statistics
8. Display summary
```

**Total Tests: 600 × 2 applications × 3 security levels = 1,800 tests**

### Pass/Fail Evaluation

The test suite automatically evaluates results based on scope:

| Scope | Expected | Pass Criteria |
|-------|----------|--------------|
| injection | Block | `is_blocked == True` OR threats detected |
| malicious | Block | `is_blocked == True` OR threats detected |
| credentials | Sanitize | `sanitized_prompt != original_prompt` |
| personal | Sanitize | `sanitized_prompt != original_prompt` |
| jailbreak | Block | `is_blocked == True` OR threats detected |
| legitimate | Allow | `is_blocked == False` |

### Results CSV Schema

Each test generates a detailed row:

```csv
Item_Number,Scope,Prompt,Expected_Behavior,Security_Level_Config,Priority,
Application,Test_Security_Level,Sanitized_Prompt,Threats_Detected,
Confidence_Score,Is_Blocked,Execution_Time_Ms,Test_Status,
Actual_Behavior,Match_Expected,Error_Message,Timestamp,Sanitization_Details
```

### Checkpoint System

Enables resuming interrupted tests:

```json
{
  "session_id": "20250102_143022",
  "timestamp": "2025-01-02T14:35:12",
  "current_item": "285",
  "current_application": "zeroshotmcp",
  "current_security_level": "medium",
  "test_count": 850,
  "stats": {...}
}
```

### HTML Dashboard

Interactive report with:
- **Overview Cards**: Total/Passed/Failed/Errors with percentages
- **Pie Chart**: Overall pass/fail/error distribution
- **Bar Charts**: Results by scope, security level, application
- **Comparison Table**: Side-by-side zeroshotmcp vs agent-ui
- **Data Table**: Searchable, filterable, sortable results
- **Filters**: Application, Security Level, Scope, Status
- **Responsive**: Works on desktop and mobile

## Usage Instructions

### Prerequisites

```bash
# Install dependencies
pip install httpx tqdm

# Or use requirements file
pip install -r test_suite/requirements.txt
```

### Start Servers

**Terminal 1 - zeroshotmcp (port 8002):**
```bash
cd zeroshotmcp
python zeroshot_secure_mcp.py
```

**Terminal 2 - agent-ui backend (port 8003):**
```bash
cd agent-ui/python-backend
# Windows:
start.bat
# Linux/Mac:
./start.sh
```

### Run Tests

**Terminal 3 - Test suite:**
```bash
# From project root
python test_suite/test_runner.py
```

### View Results

```bash
# Generate HTML report (use session ID from test output)
python test_suite/report_generator.py 20250102_143022

# Open in browser
# Windows:
start test_suite/reports/report_20250102_143022.html
# Linux:
xdg-open test_suite/reports/report_20250102_143022.html
# Mac:
open test_suite/reports/report_20250102_143022.html
```

### Resume Interrupted Tests

```bash
# List available checkpoints
python test_suite/test_runner.py --list-checkpoints

# Resume from specific session
python test_suite/test_runner.py --resume 20250102_143022
```

## Expected Performance

### Timing
- **Setup Time**: 2-3 seconds
- **Per Test**: 300-800ms average
- **Total Duration**: 15-30 minutes for 1,800 tests
- **Throughput**: 1-2 tests/second

### Resource Usage
- **CPU**: Moderate (ML models are CPU-intensive)
- **Memory**: ~2-4 GB (ML models loaded in memory)
- **Disk**: ~5 MB for results (1,800 rows)
- **Network**: Local only (no external calls)

## Output Files

After a complete test run:

```
test_suite/
├── checkpoints/
│   └── checkpoint_20250102_143022.json    # Resume data
├── results/
│   ├── test_results_20250102_143022.csv   # Full results (1,800 rows)
│   └── stats_20250102_143022.json         # Statistics summary
└── reports/
    └── report_20250102_143022.html        # Interactive dashboard
```

## Key Features

### ✅ Comprehensive Testing
- All 600 test cases
- Both applications
- All security levels
- Real-world software engineering prompts

### ✅ Robust Error Handling
- Automatic retries (3 attempts)
- Timeout protection
- Graceful failure handling
- Error reporting in results

### ✅ Progress Tracking
- Real-time progress bar with ETA
- Current test details displayed
- Throughput metrics
- Tests remaining counter

### ✅ Checkpoint/Resume
- Save progress every 50 tests
- Resume from any checkpoint
- No lost data on interruption
- Multiple session support

### ✅ Detailed Results
- CSV for analysis
- JSON for programmatic access
- HTML for visualization
- All metrics tracked

### ✅ Interactive Dashboard
- Beautiful visualizations
- Filter and search results
- Compare applications
- Export capabilities
- Responsive design

## Customization

### Change Test Scope

Edit `test_suite/config.py`:

```python
# Test only high security
SECURITY_LEVELS = ["high"]

# Test only one application
APPLICATIONS = ["zeroshotmcp"]

# Adjust timeouts
REQUEST_TIMEOUT = 60  # seconds
```

### Add Custom Pass/Fail Rules

```python
PASS_FAIL_RULES = {
    "custom_scope": {
        "expected": "CustomBehavior",
        "pass_if": lambda result: your_logic_here(result)
    }
}
```

### Modify Checkpoint Interval

```python
CHECKPOINT_INTERVAL = 100  # Save every 100 tests instead of 50
```

## Troubleshooting

### Issue: Servers not responding

```
Error: One or more servers are not responding.
```

**Solution**: Ensure both servers are running:
- zeroshotmcp on port 8002
- agent-ui backend on port 8003

### Issue: Test cases not found

```
Error: Test cases file not found: testcases.csv
```

**Solution**: Run from project root directory where `testcases.csv` exists.

### Issue: Import errors

```
ModuleNotFoundError: No module named 'tqdm'
```

**Solution**: Install dependencies:
```bash
pip install httpx tqdm
```

### Issue: Timeout errors

If many tests timeout:

1. Check server logs for errors
2. Increase timeout in `config.py`:
   ```python
   REQUEST_TIMEOUT = 60
   ```
3. Verify ML models are loaded correctly

## Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: Security Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start zeroshotmcp
        run: python zeroshotmcp/zeroshot_secure_mcp.py &
      - name: Start agent-ui
        run: cd agent-ui/python-backend && ./start.sh &
      - name: Run tests
        run: python test_suite/test_runner.py
      - name: Generate report
        run: python test_suite/report_generator.py $(ls -t test_suite/results/test_results_*.csv | head -1 | cut -d'_' -f3 | cut -d'.' -f1)
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_suite/results/
```

## Next Steps

1. **Run Initial Test**: Execute the full test suite to establish baseline
2. **Review Results**: Analyze the HTML dashboard to identify patterns
3. **Investigate Failures**: Look at failed tests in the CSV for debugging
4. **Compare Applications**: See how zeroshotmcp and agent-ui differ
5. **Test Security Levels**: Understand LOW vs MEDIUM vs HIGH behavior
6. **Iterate**: Add more test cases, improve sanitization, retest

## Architecture Diagram

```
┌─────────────────┐
│  testcases.csv  │ (600 prompts)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      test_runner.py             │
│  (Main Orchestrator)            │
└─────┬───────────────────┬───────┘
      │                   │
      ▼                   ▼
┌─────────────┐     ┌──────────────┐
│ mcp_client  │     │agentui_client│
│  (Port 8002)│     │  (Port 8003) │
└─────┬───────┘     └──────┬───────┘
      │                    │
      ▼                    ▼
┌────────────────────────────────┐
│     results_manager.py         │
│  - CSV Writer                  │
│  - Checkpoints                 │
│  - Pass/Fail Eval              │
└──────────┬─────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Output Files:                  │
│  - test_results_*.csv           │
│  - stats_*.json                 │
│  - checkpoint_*.json            │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   report_generator.py           │
│  - Charts                       │
│  - Tables                       │
│  - Dashboard                    │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   report_*.html                 │
│  (Interactive Dashboard)        │
└─────────────────────────────────┘
```

## File Structure

```
SecureMCP/
├── testcases.csv                     # 600 test prompts
├── TEST_SUITE_SUMMARY.md             # This file
└── test_suite/
    ├── __init__.py
    ├── config.py                     # Configuration
    ├── mcp_client.py                 # MCP client
    ├── agentui_client.py             # REST API client
    ├── results_manager.py            # Results & checkpoints
    ├── test_runner.py                # Main orchestrator
    ├── report_generator.py           # HTML generator
    ├── requirements.txt              # Dependencies
    ├── README.md                     # Full documentation
    ├── QUICKSTART.md                 # Quick start guide
    ├── checkpoints/                  # Checkpoint files
    │   └── checkpoint_*.json
    ├── results/                      # Test results
    │   ├── test_results_*.csv
    │   └── stats_*.json
    └── reports/                      # HTML reports
        └── report_*.html
```

## Summary

You now have a **production-ready, enterprise-grade test suite** that:

✅ Tests 600 prompts across 6 security scopes
✅ Validates both zeroshotmcp and agent-ui implementations  
✅ Tests all 3 security levels (1,800 total tests)
✅ Provides checkpoint/resume for long test runs
✅ Generates detailed CSV results for analysis
✅ Creates interactive HTML dashboards
✅ Includes comprehensive documentation
✅ Handles errors gracefully with retries
✅ Tracks performance metrics
✅ Enables easy comparison between applications

**Ready to test your SecureMCP implementation! 🚀**

