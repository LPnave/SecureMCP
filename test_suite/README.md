# SecureMCP Test Suite

Comprehensive automated testing framework for the SecureMCP project, testing both the **zeroshotmcp** (MCP application) and **agent-ui** (REST API) implementations.

## Features

- ✅ **600 Test Cases** across 6 security scopes
- ✅ **1,800 Total Tests** (600 × 2 applications × 3 security levels)
- ✅ **Automated Execution** with progress tracking
- ✅ **Checkpoint/Resume** capability for interrupted tests
- ✅ **Detailed CSV Results** for analysis
- ✅ **Interactive HTML Dashboard** with charts and statistics
- ✅ **Pass/Fail Evaluation** based on scope-specific rules
- ✅ **Performance Metrics** (execution time, throughput)

## Architecture

```
test_suite/
├── config.py              # Test configuration
├── mcp_client.py          # MCP protocol client for zeroshotmcp
├── agentui_client.py      # REST API client for agent-ui
├── results_manager.py     # Results tracking and checkpointing
├── test_runner.py         # Main orchestrator
├── report_generator.py    # HTML dashboard generator
├── checkpoints/           # Checkpoint files
├── results/               # CSV results and stats
└── reports/               # Generated HTML reports
```

## Prerequisites

### 1. Install Dependencies

```bash
pip install -r test_suite/requirements.txt
```

### 2. Start Both Servers

**zeroshotmcp** (Port 8002):
```bash
cd zeroshotmcp
python zeroshot_secure_mcp.py
```

**agent-ui backend** (Port 8003):
```bash
cd agent-ui/python-backend
./start.sh  # or start.bat on Windows
```

### 3. Prepare Test Cases

Ensure `testcases.csv` exists in the project root with 600 test prompts.

## Usage

### Run Complete Test Suite

```bash
python test_suite/test_runner.py
```

This will:
- Test all 600 prompts
- Test both applications (zeroshotmcp + agent-ui)
- Test all 3 security levels (low, medium, high)
- Total: **1,800 tests**

### Resume from Checkpoint

If tests are interrupted (Ctrl+C), resume from the last checkpoint:

```bash
# List available checkpoints
python test_suite/test_runner.py --list-checkpoints

# Resume specific session
python test_suite/test_runner.py --resume 20250102_143022
```

### Generate HTML Report

After tests complete, generate an interactive dashboard:

```bash
python test_suite/report_generator.py <session_id>
```

The session ID is displayed at the start of the test run (e.g., `20250102_143022`).

## Test Execution Flow

```
1. Load 600 test cases from testcases.csv
2. Verify both servers are running
3. For each test case:
   For each application (zeroshotmcp, agentui):
     For each security level (low, medium, high):
       a. Update server security level
       b. Send prompt for sanitization
       c. Collect results
       d. Evaluate pass/fail
       e. Save to CSV
4. Generate statistics
5. Create HTML dashboard
```

## Progress Display

The test runner shows real-time progress:

```
Running tests: 47% |███████░░░| 850/1800 [05:23<06:02, 2.62test/s]
Item 285/600 | credentials  | zeroshotmcp | medium
```

- Progress bar with ETA
- Current test details
- Throughput (tests/second)

## Checkpointing

Checkpoints are saved every **50 tests** to enable resume:

```json
{
  "session_id": "20250102_143022",
  "timestamp": "2025-01-02T14:35:12",
  "current_item": "285",
  "current_application": "zeroshotmcp",
  "current_security_level": "medium",
  "test_count": 850
}
```

## Results CSV Format

Each test produces a row with these columns:

| Column | Description |
|--------|-------------|
| Item_Number | Test case number (001-600) |
| Scope | Test scope (injection, malicious, etc.) |
| Prompt | Original test prompt |
| Expected_Behavior | Expected outcome (Block/Sanitize/Allow) |
| Security_Level_Config | Configured security level |
| Priority | Test priority (Low/Medium/High) |
| Application | Tested application (zeroshotmcp/agentui) |
| Test_Security_Level | Security level used for test |
| Sanitized_Prompt | Sanitized version of prompt |
| Threats_Detected | List of detected threats |
| Confidence_Score | Detection confidence (0.0-1.0) |
| Is_Blocked | Whether prompt was blocked |
| Execution_Time_Ms | Time taken (milliseconds) |
| Test_Status | Pass/Fail/Error |
| Actual_Behavior | What actually happened |
| Match_Expected | Does actual match expected? |
| Error_Message | Error details (if any) |
| Timestamp | When test was run |
| Sanitization_Details | JSON of sanitization applied |

## Pass/Fail Criteria

Tests are evaluated based on scope:

| Scope | Expected | Pass Criteria |
|-------|----------|--------------|
| injection | Block | Blocked OR threats detected |
| malicious | Block | Blocked OR threats detected |
| credentials | Sanitize | Prompt was modified |
| personal | Sanitize | Prompt was modified |
| jailbreak | Block | Blocked OR threats detected |
| legitimate | Allow | NOT blocked |

## HTML Dashboard

The generated dashboard includes:

### Overview Section
- Total tests, pass rate, fail rate, error rate
- Color-coded statistics cards

### Interactive Charts
- **Overall Results**: Pie chart (Pass/Fail/Error)
- **By Scope**: Stacked bar chart
- **By Security Level**: Stacked bar chart
- **By Application**: Comparison chart

### Comparison Table
- Side-by-side application comparison
- Pass rates, error rates

### Detailed Results Table
- Searchable, sortable, paginated
- Filters: Application, Security Level, Scope, Status
- Expandable rows for full prompt text

## Configuration

Edit `test_suite/config.py` to customize:

```python
# Server URLs
ZEROSHOTMCP_URL = "http://localhost:8002"
AGENTUI_URL = "http://localhost:8003"

# Test execution
CHECKPOINT_INTERVAL = 50  # Save every N tests
REQUEST_TIMEOUT = 30      # Request timeout (seconds)
RETRY_ATTEMPTS = 3        # Max retries on failure
RETRY_DELAY = 2           # Delay between retries

# Progress display
SHOW_PROGRESS_BAR = True
LOG_LEVEL = "INFO"
```

## Expected Runtime

For 1,800 tests with both servers running locally:

- **Estimated Time**: 15-30 minutes
- **Throughput**: 1-2 tests/second
- **Bottleneck**: ML model inference

Factors affecting speed:
- Server hardware (CPU/GPU)
- Network latency
- Model loading time
- Security level (higher = more processing)

## Troubleshooting

### Servers Not Responding
```
Error: One or more servers are not responding.
Please ensure both servers are running before starting tests.
```

**Solution**: Start both zeroshotmcp (8002) and agent-ui (8003) servers.

### Import Errors
```
ModuleNotFoundError: No module named 'tqdm'
```

**Solution**: Install dependencies:
```bash
pip install -r test_suite/requirements.txt
```

### Test Cases Not Found
```
Error: Test cases file not found: testcases.csv
```

**Solution**: Ensure `testcases.csv` exists in project root.

### Timeout Errors
If many tests timeout, increase timeout in `config.py`:
```python
REQUEST_TIMEOUT = 60  # Increase to 60 seconds
```

## Output Files

After a test run, you'll have:

```
test_suite/
├── checkpoints/
│   └── checkpoint_20250102_143022.json
├── results/
│   ├── test_results_20250102_143022.csv    # Full results
│   └── stats_20250102_143022.json          # Statistics
└── reports/
    └── report_20250102_143022.html         # Dashboard
```

## Example Session

```bash
# Start test run
$ python test_suite/test_runner.py

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
All servers are responsive.

Running tests: 100% |███████████| 1800/1800 [15:23<00:00, 1.95test/s]

======================================================================
Test Execution Complete!
======================================================================
Tests Run: 1800
======================================================================

======================================================================
TEST SUMMARY
======================================================================

Overall Results:
  Total Tests:     1800
  Passed:          1654 ( 91.9%)
  Failed:           132 (  7.3%)
  Errors:            14 (  0.8%)

Performance:
  Duration:       923.4 seconds
  Throughput:      1.95 tests/second
  Avg Time:        513 ms/test

Results saved to:
  CSV:   test_suite/results/test_results_20250102_143022.csv
  Stats: test_suite/results/stats_20250102_143022.json

Generate HTML report with:
  python test_suite/report_generator.py 20250102_143022
```

## Advanced Usage

### Test Specific Subset

To test only specific configurations, modify `config.py`:

```python
# Test only high security level
SECURITY_LEVELS = ["high"]

# Test only zeroshotmcp
APPLICATIONS = ["zeroshotmcp"]

# Test only injection and malicious scopes
# (Would require filtering test cases)
```

### Custom Pass/Fail Rules

Edit `PASS_FAIL_RULES` in `config.py`:

```python
PASS_FAIL_RULES = {
    "custom_scope": {
        "expected": "CustomBehavior",
        "pass_if": lambda result: custom_logic(result)
    }
}
```

### Integration with CI/CD

```bash
# Run tests and check exit code
python test_suite/test_runner.py
EXIT_CODE=$?

# Generate report
python test_suite/report_generator.py <session_id>

# Fail CI if pass rate < 90%
if [ $EXIT_CODE -ne 0 ]; then
    echo "Tests failed"
    exit 1
fi
```

## License

Same as SecureMCP project.

## Support

For issues or questions, refer to the main SecureMCP documentation.

