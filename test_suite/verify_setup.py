"""
Setup Verification Script
Verifies that the test suite is properly configured and ready to run
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from test_suite.mcp_client import MCPClient
    from test_suite.agentui_client import AgentUIClient
    from test_suite.config import TESTCASES_FILE, ZEROSHOTMCP_URL, AGENTUI_URL
except ImportError:
    # Try relative imports if running from test_suite directory
    from mcp_client import MCPClient
    from agentui_client import AgentUIClient
    from config import TESTCASES_FILE, ZEROSHOTMCP_URL, AGENTUI_URL


async def verify_setup():
    """Verify all components are ready"""
    
    print("=" * 70)
    print("SecureMCP Test Suite - Setup Verification")
    print("=" * 70)
    
    all_good = True
    
    # 1. Check test cases file
    print("\n1. Checking test cases file...")
    testcases_path = Path(TESTCASES_FILE)
    if testcases_path.exists():
        # Count lines
        with open(testcases_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f) - 1  # Subtract header
        print(f"   [OK] Found: {TESTCASES_FILE}")
        print(f"   [OK] Test cases: {line_count}")
        if line_count < 600:
            print(f"   [WARNING] Expected at least 600 test cases, found {line_count}")
    else:
        print(f"   [FAIL] NOT FOUND: {TESTCASES_FILE}")
        print(f"   Please ensure testcases.csv is in the project root")
        all_good = False
    
    # 2. Check zeroshotmcp server
    print("\n2. Checking zeroshotmcp server...")
    print(f"   URL: {ZEROSHOTMCP_URL}")
    mcp_client = MCPClient()
    mcp_ok = await mcp_client.health_check()
    if mcp_ok:
        print(f"   [OK] Server is responding on port 8002")
    else:
        print(f"   [FAIL] Server NOT responding")
        print(f"   Please start zeroshotmcp:")
        print(f"     cd zeroshotmcp")
        print(f"     python zeroshot_secure_mcp.py")
        all_good = False
    
    # 3. Check agent-ui backend
    print("\n3. Checking agent-ui backend...")
    print(f"   URL: {AGENTUI_URL}")
    agentui_client = AgentUIClient()
    agentui_ok = await agentui_client.health_check()
    if agentui_ok:
        print(f"   [OK] Server is responding on port 8003")
    else:
        print(f"   [FAIL] Server NOT responding")
        print(f"   Please start agent-ui backend:")
        print(f"     cd agent-ui/python-backend")
        print(f"     ./start.sh  (or start.bat on Windows)")
        all_good = False
    
    # 4. Check dependencies
    print("\n4. Checking Python dependencies...")
    try:
        import httpx
        print(f"   [OK] httpx: {httpx.__version__}")
    except ImportError:
        print(f"   [FAIL] httpx not installed")
        print(f"     pip install httpx")
        all_good = False
    
    try:
        import tqdm
        print(f"   [OK] tqdm: {tqdm.__version__}")
    except ImportError:
        print(f"   [WARNING] tqdm not installed (optional, but recommended)")
        print(f"     pip install tqdm")
    
    # 5. Check directories
    print("\n5. Checking directory structure...")
    try:
        from test_suite.config import RESULTS_DIR, CHECKPOINTS_DIR, REPORTS_DIR
    except ImportError:
        from config import RESULTS_DIR, CHECKPOINTS_DIR, REPORTS_DIR
    
    for dir_path, dir_name in [
        (RESULTS_DIR, "results"),
        (CHECKPOINTS_DIR, "checkpoints"),
        (REPORTS_DIR, "reports")
    ]:
        if dir_path.exists():
            print(f"   [OK] {dir_name}/ directory exists")
        else:
            print(f"   [WARNING] {dir_name}/ directory missing (will be created)")
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   [OK] Created {dir_name}/ directory")
    
    # Summary
    print("\n" + "=" * 70)
    if all_good:
        print("[SUCCESS] All checks passed! You're ready to run tests.")
        print("\nRun the test suite with:")
        print("  python test_suite/test_runner.py")
    else:
        print("[FAILED] Some checks failed. Please fix the issues above.")
        print("\nOnce fixed, run this verification again:")
        print("  python test_suite/verify_setup.py")
    print("=" * 70 + "\n")
    
    return all_good


async def quick_test():
    """Run a quick test to verify everything works"""
    print("\n" + "=" * 70)
    print("Running Quick Test")
    print("=" * 70)
    
    test_prompt = "How do I implement authentication in Express.js?"
    
    # Test zeroshotmcp
    print("\n1. Testing zeroshotmcp...")
    mcp_client = MCPClient()
    try:
        result = await mcp_client.validate_prompt(test_prompt, "medium")
        if result.get("success"):
            print(f"   [OK] zeroshotmcp responding correctly")
            print(f"   - Execution time: {result['execution_time_ms']:.0f}ms")
            print(f"   - Blocked: {result['is_blocked']}")
        else:
            print(f"   [FAIL] zeroshotmcp returned error: {result.get('error_message')}")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
    
    # Test agent-ui
    print("\n2. Testing agent-ui...")
    agentui_client = AgentUIClient()
    try:
        result = await agentui_client.sanitize_prompt(test_prompt, "medium")
        if result.get("success"):
            print(f"   [OK] agent-ui responding correctly")
            print(f"   - Execution time: {result['execution_time_ms']:.0f}ms")
            print(f"   - Blocked: {result['is_blocked']}")
        else:
            print(f"   [FAIL] agent-ui returned error: {result.get('error_message')}")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
    
    print("\n" + "=" * 70)
    print("Quick test complete!")
    print("=" * 70 + "\n")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify test suite setup")
    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Run a quick test after verification"
    )
    
    args = parser.parse_args()
    
    # Run verification
    all_good = await verify_setup()
    
    # Run quick test if requested and verification passed
    if args.quick_test and all_good:
        await quick_test()
    elif args.quick_test and not all_good:
        print("Skipping quick test due to verification failures.\n")


if __name__ == "__main__":
    asyncio.run(main())

