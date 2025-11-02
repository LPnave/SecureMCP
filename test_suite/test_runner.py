"""
Main Test Runner
Orchestrates test execution, progress tracking, and result collection
"""

import asyncio
import csv
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# For progress bar
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("Warning: tqdm not installed. Install with 'pip install tqdm' for progress bars")

try:
    from test_suite.config import (
        TESTCASES_FILE, SECURITY_LEVELS, APPLICATIONS,
        SHOW_PROGRESS_BAR
    )
    from test_suite.mcp_client import MCPClient
    from test_suite.agentui_client import AgentUIClient
    from test_suite.results_manager import ResultsManager
except ImportError:
    # Try relative imports if running from test_suite directory
    from config import (
        TESTCASES_FILE, SECURITY_LEVELS, APPLICATIONS,
        SHOW_PROGRESS_BAR
    )
    from mcp_client import MCPClient
    from agentui_client import AgentUIClient
    from results_manager import ResultsManager


class TestRunner:
    """Main test orchestrator"""
    
    def __init__(self, resume_session: Optional[str] = None):
        self.mcp_client = MCPClient()
        self.agentui_client = AgentUIClient()
        
        # Load or create results manager
        if resume_session:
            checkpoint = ResultsManager.load_checkpoint(resume_session)
            if checkpoint:
                print(f"Resuming session {resume_session} from test {checkpoint['test_count']}")
                self.results_manager = ResultsManager(session_id=resume_session)
                self.resume_from = checkpoint
            else:
                print(f"Checkpoint {resume_session} not found. Starting fresh.")
                self.results_manager = ResultsManager()
                self.resume_from = None
        else:
            self.results_manager = ResultsManager()
            self.resume_from = None
        
        self.test_cases: List[Dict] = []
        self.total_tests = 0
    
    def load_test_cases(self) -> List[Dict]:
        """Load test cases from CSV"""
        test_cases = []
        
        try:
            with open(TESTCASES_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    test_cases.append(row)
            
            print(f"Loaded {len(test_cases)} test cases from {TESTCASES_FILE}")
            return test_cases
        
        except FileNotFoundError:
            print(f"Error: Test cases file not found: {TESTCASES_FILE}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading test cases: {e}")
            sys.exit(1)
    
    async def verify_servers(self) -> bool:
        """Verify both servers are running"""
        print("\nVerifying server connectivity...")
        
        # Check zeroshotmcp
        mcp_ok = await self.mcp_client.health_check()
        print(f"  zeroshotmcp (port 8002): {'✓ OK' if mcp_ok else '✗ NOT RESPONDING'}")
        
        # Check agent-ui
        agentui_ok = await self.agentui_client.health_check()
        print(f"  agent-ui (port 8003): {'✓ OK' if agentui_ok else '✗ NOT RESPONDING'}")
        
        if not mcp_ok or not agentui_ok:
            print("\nError: One or more servers are not responding.")
            print("Please ensure both servers are running before starting tests.")
            return False
        
        print("All servers are responsive.\n")
        return True
    
    def should_skip_test(self, test_case: Dict, application: str, security_level: str) -> bool:
        """Determine if a test should be skipped based on checkpoint"""
        if not self.resume_from:
            return False
        
        # Get checkpoint info
        checkpoint_item = self.resume_from.get("current_item")
        checkpoint_app = self.resume_from.get("current_application")
        checkpoint_level = self.resume_from.get("current_security_level")
        
        current_item = test_case["Item Number"]
        
        # Skip if we haven't reached the checkpoint yet
        if int(current_item) < int(checkpoint_item):
            return True
        
        # If we're at the checkpoint item, check app and level
        if int(current_item) == int(checkpoint_item):
            # Skip if application comes before checkpoint app
            if APPLICATIONS.index(application) < APPLICATIONS.index(checkpoint_app):
                return True
            
            # If same app, skip if level comes before checkpoint level
            if application == checkpoint_app:
                if SECURITY_LEVELS.index(security_level) <= SECURITY_LEVELS.index(checkpoint_level):
                    return True
        
        return False
    
    async def run_test(self, test_case: Dict, application: str, security_level: str) -> Dict:
        """
        Run a single test
        
        Args:
            test_case: Test case dictionary
            application: 'zeroshotmcp' or 'agentui'
            security_level: 'low', 'medium', or 'high'
            
        Returns:
            Test result dictionary
        """
        prompt = test_case["Prompt"]
        
        if application == "zeroshotmcp":
            result = await self.mcp_client.validate_prompt(prompt, security_level)
        elif application == "agentui":
            result = await self.agentui_client.sanitize_prompt(prompt, security_level)
        else:
            return {
                "success": False,
                "error_message": f"Unknown application: {application}",
                "test_status": "Error"
            }
        
        return result
    
    async def run_all_tests(self):
        """Run all tests with progress tracking"""
        # Load test cases
        self.test_cases = self.load_test_cases()
        
        # Calculate total tests
        self.total_tests = len(self.test_cases) * len(APPLICATIONS) * len(SECURITY_LEVELS)
        
        print(f"\n{'='*70}")
        print(f"SecureMCP Test Suite")
        print(f"{'='*70}")
        print(f"Test Cases: {len(self.test_cases)}")
        print(f"Applications: {', '.join(APPLICATIONS)}")
        print(f"Security Levels: {', '.join(SECURITY_LEVELS)}")
        print(f"Total Tests: {self.total_tests}")
        print(f"Session ID: {self.results_manager.session_id}")
        print(f"{'='*70}\n")
        
        # Verify servers
        if not await self.verify_servers():
            sys.exit(1)
        
        # Create progress bar
        if SHOW_PROGRESS_BAR and HAS_TQDM:
            pbar = tqdm(total=self.total_tests, desc="Running tests", unit="test")
        else:
            pbar = None
            print("Starting test execution...\n")
        
        tests_run = 0
        tests_skipped = 0
        
        try:
            # Iterate through all combinations
            for test_case in self.test_cases:
                for application in APPLICATIONS:
                    for security_level in SECURITY_LEVELS:
                        # Check if we should skip this test (resuming)
                        if self.should_skip_test(test_case, application, security_level):
                            tests_skipped += 1
                            if pbar:
                                pbar.update(1)
                            continue
                        
                        # Update progress description
                        if pbar:
                            pbar.set_description(
                                f"Item {test_case['Item Number']}/{len(self.test_cases)} | "
                                f"{test_case['Scope'][:12]:12} | {application[:10]:10} | {security_level:6}"
                            )
                        else:
                            if tests_run % 10 == 0:
                                print(f"Progress: {tests_run}/{self.total_tests} tests completed")
                        
                        # Run the test
                        result = await self.run_test(test_case, application, security_level)
                        
                        # Add result
                        self.results_manager.add_result(test_case, result, application, security_level)
                        
                        tests_run += 1
                        
                        # Update progress bar
                        if pbar:
                            pbar.update(1)
                        
                        # Small delay to avoid overwhelming servers
                        await asyncio.sleep(0.1)
            
            # Close progress bar
            if pbar:
                pbar.close()
            
            print(f"\n{'='*70}")
            print(f"Test Execution Complete!")
            print(f"{'='*70}")
            print(f"Tests Run: {tests_run}")
            if tests_skipped > 0:
                print(f"Tests Skipped (resumed): {tests_skipped}")
            print(f"{'='*70}\n")
        
        except KeyboardInterrupt:
            print("\n\nTest execution interrupted by user.")
            print("Progress has been saved. You can resume with:")
            print(f"  python test_suite/test_runner.py --resume {self.results_manager.session_id}")
            if pbar:
                pbar.close()
            sys.exit(1)
        
        except Exception as e:
            print(f"\n\nError during test execution: {e}")
            if pbar:
                pbar.close()
            raise
    
    def print_summary(self):
        """Print test summary statistics"""
        stats = self.results_manager.get_stats()
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        # Overall stats
        total = stats["total_tests"]
        passed = stats["Pass"]
        failed = stats["Fail"]
        errors = stats["Error"]
        
        print(f"\nOverall Results:")
        print(f"  Total Tests:   {total:6d}")
        print(f"  Passed:        {passed:6d} ({passed/max(total,1)*100:5.1f}%)")
        print(f"  Failed:        {failed:6d} ({failed/max(total,1)*100:5.1f}%)")
        print(f"  Errors:        {errors:6d} ({errors/max(total,1)*100:5.1f}%)")
        
        # Performance
        duration = stats["duration_seconds"]
        tests_per_sec = stats["tests_per_second"]
        print(f"\nPerformance:")
        print(f"  Duration:      {duration:6.1f} seconds")
        print(f"  Throughput:    {tests_per_sec:6.2f} tests/second")
        print(f"  Avg Time:      {1000/max(tests_per_sec,0.001):6.0f} ms/test")
        
        # By scope
        print(f"\nResults by Scope:")
        for scope, scope_stats in stats["by_scope"].items():
            total_scope = scope_stats["total"]
            passed_scope = scope_stats["Pass"]
            print(f"  {scope:15} {passed_scope:4d}/{total_scope:4d} ({passed_scope/max(total_scope,1)*100:5.1f}%)")
        
        # By security level
        print(f"\nResults by Security Level:")
        for level, level_stats in stats["by_security_level"].items():
            total_level = level_stats["total"]
            passed_level = level_stats["Pass"]
            print(f"  {level:15} {passed_level:4d}/{total_level:4d} ({passed_level/max(total_level,1)*100:5.1f}%)")
        
        # By application
        print(f"\nResults by Application:")
        for app, app_stats in stats["by_application"].items():
            total_app = app_stats["total"]
            passed_app = app_stats["Pass"]
            print(f"  {app:15} {passed_app:4d}/{total_app:4d} ({passed_app/max(total_app,1)*100:5.1f}%)")
        
        print("="*70 + "\n")
    
    async def run(self):
        """Main execution flow"""
        await self.run_all_tests()
        
        # Finalize results
        results_file, stats_file = self.results_manager.finalize()
        
        # Print summary
        self.print_summary()
        
        # Print file locations
        print(f"Results saved to:")
        print(f"  CSV:   {results_file}")
        print(f"  Stats: {stats_file}")
        print(f"\nGenerate HTML report with:")
        print(f"  python test_suite/report_generator.py {self.results_manager.session_id}")
        print()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SecureMCP Test Suite Runner")
    parser.add_argument(
        "--resume",
        type=str,
        help="Resume from a previous session (provide session ID)"
    )
    parser.add_argument(
        "--list-checkpoints",
        action="store_true",
        help="List available checkpoints"
    )
    
    args = parser.parse_args()
    
    # List checkpoints if requested
    if args.list_checkpoints:
        checkpoints = ResultsManager.list_checkpoints()
        if checkpoints:
            print("\nAvailable checkpoints:")
            for cp in checkpoints:
                print(f"  {cp}")
        else:
            print("\nNo checkpoints found.")
        sys.exit(0)
    
    # Create and run test runner
    runner = TestRunner(resume_session=args.resume)
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())

