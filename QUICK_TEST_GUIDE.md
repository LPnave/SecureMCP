# Quick Test Feature Guide

## Overview

The quick test feature allows you to run a smaller subset of tests (100 prompts instead of 600) for faster validation during development and iteration.

## Usage

### Running Quick Test

```bash
# From project root
python test_suite/test_runner.py --quick
```

### Running Full Test

```bash
# From project root
python test_suite/test_runner.py
```

## Quick Test Composition

The `testcases_quick.csv` contains **100 carefully selected prompts** that provide comprehensive coverage:

| Scope | Count | Percentage |
|-------|-------|------------|
| **Injection** | 17 | 17% |
| **Malicious** | 17 | 17% |
| **Credentials** | 17 | 17% |
| **Personal** | 16 | 16% |
| **Jailbreak** | 17 | 17% |
| **Legitimate** | 16 | 16% |
| **Total** | 100 | 100% |

### Test Execution Matrix

With 2 applications and 3 security levels:
- **Quick Test:** 100 prompts × 2 apps × 3 levels = **600 total tests**
- **Full Test:** 600 prompts × 2 apps × 3 levels = **3,600 total tests**

## Time Estimates

### Quick Test (~5-10 minutes)
- Ideal for: Development, quick validation, CI/CD pipelines
- Coverage: Representative samples from each category
- Fast feedback on major issues

### Full Test (~30-60 minutes)
- Ideal for: Final validation, comprehensive testing, release testing
- Coverage: Complete test coverage across all categories
- Thorough validation of all edge cases

## Quick Test Selection Criteria

The 100 prompts were selected to ensure:

1. **Representative Coverage** - Each scope is equally represented
2. **Priority Cases** - All HIGH priority test cases included
3. **Pattern Diversity** - Various attack patterns and techniques
4. **Realistic Scenarios** - Real-world examples from actual usage
5. **Edge Cases** - Boundary conditions and corner cases

### Examples Included

**Injection (17 prompts):**
- "Ignore previous instructions..." - Direct instruction override
- "Act as a developer..." - Role manipulation
- "Skip authentication..." - Security bypass attempts
- Context injection markers (`[SYSTEM]`, etc.)

**Malicious (17 prompts):**
- Destructive commands: `rm -rf /`, `DROP DATABASE`
- Code execution: `eval()`, `exec()`, `system()`
- Container attacks: `docker rm -f`, `kubectl delete`
- Network attacks: `nmap`, `sqlmap`

**Credentials (17 prompts):**
- API keys: AWS, GitHub, OpenAI, Stripe
- Database passwords: MongoDB, PostgreSQL, MySQL
- Service tokens: JWT, OAuth, Terraform
- SSH keys and connection strings

**Personal (16 prompts):**
- Email addresses
- SSN, phone numbers, credit cards
- Employee IDs, medical records
- IP addresses, MAC addresses

**Jailbreak (17 prompts):**
- Hypothetical framing: "Hypothetically...", "Imagine..."
- False authority: "As CTO...", "I'm authorized..."
- Urgency tactics: "Emergency...", "People will die..."
- Educational pretexts: "For research purposes..."

**Legitimate (16 prompts):**
- Security best practices questions
- Authentication/authorization queries
- OWASP and compliance questions
- Development best practices

## When to Use Each

### Use Quick Test When:
- ✅ Developing new features
- ✅ Testing pattern improvements
- ✅ Validating threshold changes
- ✅ Running in CI/CD pipelines
- ✅ Quick smoke testing
- ✅ Iterating on improvements

### Use Full Test When:
- ✅ Final validation before release
- ✅ Comprehensive regression testing
- ✅ Measuring overall performance
- ✅ Generating detailed reports
- ✅ Validating all edge cases
- ✅ Official benchmarking

## Command Line Options

```bash
# Quick test (100 prompts)
python test_suite/test_runner.py --quick

# Full test (600 prompts)
python test_suite/test_runner.py

# Resume interrupted test
python test_suite/test_runner.py --resume <session_id>

# List available checkpoints
python test_suite/test_runner.py --list-checkpoints

# Combine options (quick test resume)
python test_suite/test_runner.py --quick --resume <session_id>
```

## Output and Reports

Both quick and full tests generate:
- ✅ CSV results file with detailed metrics
- ✅ JSON statistics file
- ✅ Checkpoint files (every 50 tests)
- ✅ HTML dashboard (via report generator)

```bash
# Generate HTML report after test
python test_suite/report_generator.py <session_id>
```

## Expected Results

### Quick Test Metrics (After Improvements)

With the Phase 1 & 2 improvements implemented:

| Scope | Expected Pass Rate |
|-------|-------------------|
| Injection | 75-85% |
| Malicious | 80-90% |
| Jailbreak | 65-75% |
| Personal | 80-90% |
| Credentials | 95%+ |
| Legitimate | 97-99% |
| **Overall** | **75-85%** |

### Test Duration

**Quick Test:**
- zeroshotmcp: ~150 tests → 2-4 minutes
- agent-ui: ~150 tests → 2-4 minutes
- Both apps, all levels: ~5-10 minutes

**Full Test:**
- zeroshotmcp: ~900 tests → 15-25 minutes
- agent-ui: ~900 tests → 15-25 minutes
- Both apps, all levels: ~30-60 minutes

## File Structure

```
SecureMCP/
├── testcases.csv              # Full test set (600 prompts)
├── testcases_quick.csv        # Quick test set (100 prompts) ← NEW
├── test_suite/
│   ├── config.py              # Configuration (includes TESTCASES_QUICK_FILE)
│   ├── test_runner.py         # Main runner (supports --quick flag)
│   ├── results/               # Test results
│   ├── checkpoints/           # Checkpoint files
│   └── reports/               # HTML reports
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Quick Security Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install dependencies
        run: pip install -r test_suite/requirements.txt
      
      - name: Start servers
        run: |
          python zeroshotmcp/zeroshot_secure_mcp.py &
          cd agent-ui/python-backend && uvicorn app.main:app &
          sleep 10
      
      - name: Run quick tests
        run: python test_suite/test_runner.py --quick
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_suite/results/
```

## Troubleshooting

### Quick Test File Not Found

```bash
Error: Test cases file not found: testcases_quick.csv
```

**Solution:** Ensure `testcases_quick.csv` is in the project root:
```bash
ls testcases_quick.csv  # Should exist
```

### Tests Taking Too Long

If quick tests are slow:
1. Check server performance (CPU/memory)
2. Verify network latency is low
3. Ensure ML models are loaded (first run is slower)
4. Check if other processes are using resources

### Unexpected Results

If results differ from expectations:
1. Run quick test first to identify issues
2. Compare with full test results
3. Check specific failing prompts
4. Review HTML report for patterns

## Best Practices

1. **Development Cycle:**
   - Make changes → Run quick test → Iterate
   - Once stable → Run full test → Validate

2. **Testing Strategy:**
   - Quick test for each commit
   - Full test before merging to main
   - Full test before releases

3. **Result Comparison:**
   - Quick test gives overall health check
   - Full test provides comprehensive metrics
   - Compare trends over time

4. **Performance Optimization:**
   - Use quick test to identify bottlenecks
   - Profile specific failing prompts
   - Validate fixes with full test

---

**Quick Test Feature Status:** ✅ Implemented  
**Available Since:** November 2, 2025  
**Command:** `python test_suite/test_runner.py --quick`

