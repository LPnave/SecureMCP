"""
Results Manager
Handles CSV writing, checkpointing, and result evaluation
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from test_suite.config import (
        RESULTS_COLUMNS, CHECKPOINTS_DIR, RESULTS_DIR,
        CHECKPOINT_INTERVAL, PASS_FAIL_RULES
    )
except ImportError:
    # Try relative imports if running from test_suite directory
    from config import (
        RESULTS_COLUMNS, CHECKPOINTS_DIR, RESULTS_DIR,
        CHECKPOINT_INTERVAL, PASS_FAIL_RULES
    )


class ResultsManager:
    """Manages test results, checkpoints, and CSV output"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = RESULTS_DIR / f"test_results_{self.session_id}.csv"
        self.checkpoint_file = CHECKPOINTS_DIR / f"checkpoint_{self.session_id}.json"
        self.results_buffer: List[Dict] = []
        self.test_count = 0
        self.start_time = datetime.now()
        
        # Statistics
        self.stats = {
            "total_tests": 0,
            "Pass": 0,
            "Fail": 0,
            "Error": 0,
            "by_scope": {},
            "by_security_level": {},
            "by_application": {}
        }
        
        # Initialize CSV file with headers
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Create the CSV file with headers"""
        with open(self.results_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=RESULTS_COLUMNS)
            writer.writeheader()
    
    def add_result(self, test_case: Dict, result: Dict, application: str, test_security_level: str):
        """
        Add a test result and evaluate pass/fail
        
        Args:
            test_case: Original test case from CSV
            result: Result from client (MCP or AgentUI)
            application: Which application was tested
            test_security_level: Security level used for this test
        """
        # Evaluate pass/fail based on scope
        scope = test_case["Scope"].lower()
        test_status = self._evaluate_result(scope, result, test_case)
        
        # Prepare row data
        row = {
            "Item_Number": test_case["Item Number"],
            "Scope": test_case["Scope"],
            "Prompt": test_case["Prompt"],
            "Expected_Behavior": test_case["Expected Behavior"],
            "Security_Level_Config": test_case["Security Level"],
            "Priority": test_case["Priority"],
            "Application": application,
            "Test_Security_Level": test_security_level,
            "Sanitized_Prompt": result.get("sanitized_prompt", ""),
            "Threats_Detected": ", ".join(result.get("threats_detected", [])),
            "Confidence_Score": f"{result.get('confidence_score', 0.0):.3f}",
            "Is_Blocked": str(result.get("is_blocked", False)),
            "Execution_Time_Ms": f"{result.get('execution_time_ms', 0):.2f}",
            "Test_Status": test_status,
            "Actual_Behavior": result.get("actual_behavior", "Unknown"),
            "Match_Expected": str(test_status == "Pass"),
            "Error_Message": result.get("error_message", ""),
            "Timestamp": datetime.now().isoformat(),
            "Sanitization_Details": result.get("sanitization_details", "{}")
        }
        
        # Add to buffer
        self.results_buffer.append(row)
        self.test_count += 1
        
        # Update statistics
        self._update_stats(row)
        
        # Write to CSV if buffer is full
        if len(self.results_buffer) >= 10:
            self._flush_buffer()
        
        # Save checkpoint if needed
        if self.test_count % CHECKPOINT_INTERVAL == 0:
            self.save_checkpoint(test_case, application, test_security_level)
    
    def _evaluate_result(self, scope: str, result: Dict, test_case: Dict) -> str:
        """
        Evaluate if the test passed or failed based on scope and expected behavior
        
        Args:
            scope: Test scope (injection, malicious, etc.)
            result: Test result
            test_case: Original test case
            
        Returns:
            "Pass", "Fail", or "Error"
        """
        # If there was an error, mark as Error
        if result.get("test_status") == "Error" or not result.get("success"):
            return "Error"
        
        # Get pass/fail rules for this scope
        rule = PASS_FAIL_RULES.get(scope, PASS_FAIL_RULES.get("legitimate"))
        
        if not rule:
            return "Pass"  # Default to pass if no rule defined
        
        # Apply the rule
        try:
            passed = rule["pass_if"](result)
            return "Pass" if passed else "Fail"
        except Exception as e:
            print(f"Error evaluating result: {e}")
            return "Error"
    
    def _update_stats(self, row: Dict):
        """Update statistics with the new result"""
        self.stats["total_tests"] += 1
        
        # Update status counts
        status = row["Test_Status"]
        
        if status in ["Pass", "Fail", "Error"]:
            self.stats[status] += 1
        
        # Update by scope
        scope = row["Scope"]
        if scope not in self.stats["by_scope"]:
            self.stats["by_scope"][scope] = {"total": 0, "Pass": 0, "Fail": 0, "Error": 0}
        self.stats["by_scope"][scope]["total"] += 1
        if status in ["Pass", "Fail", "Error"]:
            self.stats["by_scope"][scope][status] += 1
        
        # Update by security level
        level = row["Test_Security_Level"]
        if level not in self.stats["by_security_level"]:
            self.stats["by_security_level"][level] = {"total": 0, "Pass": 0, "Fail": 0, "Error": 0}
        self.stats["by_security_level"][level]["total"] += 1
        if status in ["Pass", "Fail", "Error"]:
            self.stats["by_security_level"][level][status] += 1
        
        # Update by application
        app = row["Application"]
        if app not in self.stats["by_application"]:
            self.stats["by_application"][app] = {"total": 0, "Pass": 0, "Fail": 0, "Error": 0}
        self.stats["by_application"][app]["total"] += 1
        if status in ["Pass", "Fail", "Error"]:
            self.stats["by_application"][app][status] += 1
    
    def _flush_buffer(self):
        """Write buffered results to CSV"""
        if not self.results_buffer:
            return
        
        with open(self.results_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=RESULTS_COLUMNS)
            writer.writerows(self.results_buffer)
        
        self.results_buffer = []
    
    def save_checkpoint(self, current_test: Dict, application: str, security_level: str):
        """Save a checkpoint for resume capability"""
        checkpoint_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "current_item": current_test["Item Number"],
            "current_application": application,
            "current_security_level": security_level,
            "test_count": self.test_count,
            "stats": self.stats
        }
        
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
    
    @classmethod
    def load_checkpoint(cls, session_id: str) -> Optional[Dict]:
        """Load a checkpoint to resume testing"""
        checkpoint_file = CHECKPOINTS_DIR / f"checkpoint_{session_id}.json"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return None
    
    @classmethod
    def list_checkpoints(cls) -> List[str]:
        """List available checkpoints"""
        checkpoints = []
        for file in CHECKPOINTS_DIR.glob("checkpoint_*.json"):
            session_id = file.stem.replace("checkpoint_", "")
            checkpoints.append(session_id)
        return sorted(checkpoints, reverse=True)
    
    def finalize(self):
        """Finalize results - flush buffer and save final checkpoint"""
        self._flush_buffer()
        
        # Save final stats
        stats_file = RESULTS_DIR / f"stats_{self.session_id}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            # Add summary info
            summary_stats = {
                "session_id": self.session_id,
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "results_file": str(self.results_file),
                "statistics": self.stats
            }
            json.dump(summary_stats, f, indent=2)
        
        return str(self.results_file), str(stats_file)
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        return {
            **self.stats,
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "tests_per_second": self.test_count / max((datetime.now() - self.start_time).total_seconds(), 1)
        }

