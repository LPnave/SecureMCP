"""
HTML Report Generator
Generates interactive dashboard with charts and detailed results
"""

import csv
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from test_suite.config import RESULTS_DIR, REPORTS_DIR
except ImportError:
    # Try relative imports if running from test_suite directory
    from config import RESULTS_DIR, REPORTS_DIR


class ReportGenerator:
    """Generate HTML dashboard from test results"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.results_file = RESULTS_DIR / f"test_results_{session_id}.csv"
        self.stats_file = RESULTS_DIR / f"stats_{session_id}.json"
        self.report_file = REPORTS_DIR / f"report_{session_id}.html"
        
        self.results: List[Dict] = []
        self.stats: Dict = {}
    
    def load_data(self):
        """Load results and stats"""
        # Load CSV results
        if not self.results_file.exists():
            print(f"Error: Results file not found: {self.results_file}")
            sys.exit(1)
        
        with open(self.results_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.results = list(reader)
        
        # Load stats
        if self.stats_file.exists():
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
        else:
            # Generate stats from results
            self.stats = self._generate_stats_from_results()
        
        print(f"Loaded {len(self.results)} test results")
    
    def _generate_stats_from_results(self) -> Dict:
        """Generate statistics from results if stats file doesn't exist"""
        stats = {
            "total_tests": len(self.results),
            "Pass": sum(1 for r in self.results if r["Test_Status"] == "Pass"),
            "Fail": sum(1 for r in self.results if r["Test_Status"] == "Fail"),
            "Error": sum(1 for r in self.results if r["Test_Status"] == "Error"),
            "by_scope": {},
            "by_security_level": {},
            "by_application": {}
        }
        
        # Group by scope
        for result in self.results:
            scope = result["Scope"]
            if scope not in stats["by_scope"]:
                stats["by_scope"][scope] = {"total": 0, "Pass": 0, "Fail": 0, "Error": 0}
            
            stats["by_scope"][scope]["total"] += 1
            status = result["Test_Status"]
            if status in ["Pass", "Fail", "Error"]:
                stats["by_scope"][scope][status] += 1
        
        # Group by security level
        for result in self.results:
            level = result["Test_Security_Level"]
            if level not in stats["by_security_level"]:
                stats["by_security_level"][level] = {"total": 0, "Pass": 0, "Fail": 0, "Error": 0}
            
            stats["by_security_level"][level]["total"] += 1
            status = result["Test_Status"]
            if status in ["Pass", "Fail", "Error"]:
                stats["by_security_level"][level][status] += 1
        
        # Group by application
        for result in self.results:
            app = result["Application"]
            if app not in stats["by_application"]:
                stats["by_application"][app] = {"total": 0, "Pass": 0, "Fail": 0, "Error": 0}
            
            stats["by_application"][app]["total"] += 1
            status = result["Test_Status"]
            if status in ["Pass", "Fail", "Error"]:
                stats["by_application"][app][status] += 1
        
        return stats
    
    def generate_html(self):
        """Generate the HTML report"""
        html = self._get_html_template()
        
        # Replace placeholders
        html = html.replace("{{SESSION_ID}}", self.session_id)
        html = html.replace("{{GENERATED_TIME}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        html = html.replace("{{STATS_JSON}}", json.dumps(self.stats))
        html = html.replace("{{RESULTS_JSON}}", json.dumps(self.results))
        
        # Write to file
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\nHTML report generated: {self.report_file}")
        print(f"Open in browser: file://{self.report_file.absolute()}")
    
    def _get_html_template(self) -> str:
        """Get the HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SecureMCP Test Report - {{SESSION_ID}}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            color: #2d3748;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .subtitle {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2d3748;
        }
        
        .stat-subtitle {
            font-size: 0.9rem;
            color: #a0aec0;
            margin-top: 5px;
        }
        
        .stat-pass { color: #48bb78; }
        .stat-fail { color: #f56565; }
        .stat-error { color: #ed8936; }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .chart-card h2 {
            font-size: 1.3rem;
            margin-bottom: 20px;
            color: #2d3748;
        }
        
        .table-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .table-card h2 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #2d3748;
        }
        
        .filters {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .filter-group {
            flex: 1;
            min-width: 200px;
        }
        
        .filter-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #4a5568;
        }
        
        .filter-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid #cbd5e0;
            border-radius: 5px;
            font-size: 1rem;
        }
        
        table.dataTable {
            width: 100% !important;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .badge-pass {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .badge-fail {
            background: #fed7d7;
            color: #742a2a;
        }
        
        .badge-error {
            background: #feebc8;
            color: #7c2d12;
        }
        
        .export-buttons {
            margin-bottom: 20px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a67d8;
        }
        
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .comparison-table th,
        .comparison-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .comparison-table th {
            background: #f7fafc;
            font-weight: 600;
            color: #4a5568;
        }
        
        .comparison-table tbody tr:hover {
            background: #f7fafc;
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            .filters {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 SecureMCP Test Report</h1>
            <div class="subtitle">Session: {{SESSION_ID}} | Generated: {{GENERATED_TIME}}</div>
        </header>
        
        <!-- Overview Stats -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Tests</div>
                <div class="stat-value" id="total-tests">0</div>
                <div class="stat-subtitle">Across all configurations</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Passed</div>
                <div class="stat-value stat-pass" id="passed-tests">0</div>
                <div class="stat-subtitle" id="passed-percent">0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Failed</div>
                <div class="stat-value stat-fail" id="failed-tests">0</div>
                <div class="stat-subtitle" id="failed-percent">0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Errors</div>
                <div class="stat-value stat-error" id="error-tests">0</div>
                <div class="stat-subtitle" id="error-percent">0%</div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="charts-grid">
            <div class="chart-card">
                <h2>Overall Results</h2>
                <canvas id="overallChart"></canvas>
            </div>
            <div class="chart-card">
                <h2>Results by Scope</h2>
                <canvas id="scopeChart"></canvas>
            </div>
            <div class="chart-card">
                <h2>Results by Security Level</h2>
                <canvas id="securityLevelChart"></canvas>
            </div>
            <div class="chart-card">
                <h2>Results by Application</h2>
                <canvas id="applicationChart"></canvas>
            </div>
        </div>
        
        <!-- Comparison Table -->
        <div class="table-card">
            <h2>Application Comparison</h2>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>zeroshotmcp</th>
                        <th>agent-ui</th>
                    </tr>
                </thead>
                <tbody id="comparison-tbody">
                </tbody>
            </table>
        </div>
        
        <!-- Detailed Results Table -->
        <div class="table-card">
            <h2>Detailed Test Results</h2>
            
            <div class="filters">
                <div class="filter-group">
                    <label for="filter-app">Application</label>
                    <select id="filter-app">
                        <option value="">All</option>
                        <option value="zeroshotmcp">zeroshotmcp</option>
                        <option value="agentui">agentui</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-level">Security Level</label>
                    <select id="filter-level">
                        <option value="">All</option>
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-scope">Scope</label>
                    <select id="filter-scope">
                        <option value="">All</option>
                        <option value="injection">Injection</option>
                        <option value="malicious">Malicious</option>
                        <option value="credentials">Credentials</option>
                        <option value="personal">Personal</option>
                        <option value="jailbreak">Jailbreak</option>
                        <option value="legitimate">Legitimate</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-status">Status</label>
                    <select id="filter-status">
                        <option value="">All</option>
                        <option value="Pass">Pass</option>
                        <option value="Fail">Fail</option>
                        <option value="Error">Error</option>
                    </select>
                </div>
            </div>
            
            <table id="resultsTable" class="display" style="width:100%">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Scope</th>
                        <th>Prompt</th>
                        <th>App</th>
                        <th>Level</th>
                        <th>Status</th>
                        <th>Expected</th>
                        <th>Actual</th>
                        <th>Threats</th>
                        <th>Time (ms)</th>
                    </tr>
                </thead>
                <tbody id="results-tbody">
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Load data
        const stats = {{STATS_JSON}};
        const results = {{RESULTS_JSON}};
        
        // Update overview stats
        document.getElementById('total-tests').textContent = stats.total_tests || stats.statistics?.total_tests || 0;
        const passed = stats.Pass || stats.statistics?.Pass || 0;
        const failed = stats.Fail || stats.statistics?.Fail || 0;
        const errors = stats.Error || stats.statistics?.Error || 0;
        const total = stats.total_tests || stats.statistics?.total_tests || 1;
        
        document.getElementById('passed-tests').textContent = passed;
        document.getElementById('failed-tests').textContent = failed;
        document.getElementById('error-tests').textContent = errors;
        
        document.getElementById('passed-percent').textContent = `${(passed/total*100).toFixed(1)}%`;
        document.getElementById('failed-percent').textContent = `${(failed/total*100).toFixed(1)}%`;
        document.getElementById('error-percent').textContent = `${(errors/total*100).toFixed(1)}%`;
        
        // Overall Pie Chart
        new Chart(document.getElementById('overallChart'), {
            type: 'pie',
            data: {
                labels: ['Passed', 'Failed', 'Errors'],
                datasets: [{
                    data: [passed, failed, errors],
                    backgroundColor: ['#48bb78', '#f56565', '#ed8936']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        });
        
        // Scope Chart
        const scopeStats = stats.by_scope || stats.statistics?.by_scope || {};
        const scopeLabels = Object.keys(scopeStats);
        const scopeData = {
            labels: scopeLabels,
            datasets: [
                {
                    label: 'Passed',
                    data: scopeLabels.map(s => scopeStats[s].Pass || 0),
                    backgroundColor: '#48bb78'
                },
                {
                    label: 'Failed',
                    data: scopeLabels.map(s => scopeStats[s].Fail || 0),
                    backgroundColor: '#f56565'
                },
                {
                    label: 'Errors',
                    data: scopeLabels.map(s => scopeStats[s].Error || 0),
                    backgroundColor: '#ed8936'
                }
            ]
        };
        
        new Chart(document.getElementById('scopeChart'), {
            type: 'bar',
            data: scopeData,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true }
                }
            }
        });
        
        // Security Level Chart
        const levelStats = stats.by_security_level || stats.statistics?.by_security_level || {};
        const levelLabels = Object.keys(levelStats);
        const levelData = {
            labels: levelLabels,
            datasets: [
                {
                    label: 'Passed',
                    data: levelLabels.map(l => levelStats[l].Pass || 0),
                    backgroundColor: '#48bb78'
                },
                {
                    label: 'Failed',
                    data: levelLabels.map(l => levelStats[l].Fail || 0),
                    backgroundColor: '#f56565'
                },
                {
                    label: 'Errors',
                    data: levelLabels.map(l => levelStats[l].Error || 0),
                    backgroundColor: '#ed8936'
                }
            ]
        };
        
        new Chart(document.getElementById('securityLevelChart'), {
            type: 'bar',
            data: levelData,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true }
                }
            }
        });
        
        // Application Chart
        const appStats = stats.by_application || stats.statistics?.by_application || {};
        const appLabels = Object.keys(appStats);
        const appData = {
            labels: appLabels,
            datasets: [
                {
                    label: 'Passed',
                    data: appLabels.map(a => appStats[a].Pass || 0),
                    backgroundColor: '#48bb78'
                },
                {
                    label: 'Failed',
                    data: appLabels.map(a => appStats[a].Fail || 0),
                    backgroundColor: '#f56565'
                },
                {
                    label: 'Errors',
                    data: appLabels.map(a => appStats[a].Error || 0),
                    backgroundColor: '#ed8936'
                }
            ]
        };
        
        new Chart(document.getElementById('applicationChart'), {
            type: 'bar',
            data: appData,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true }
                }
            }
        });
        
        // Comparison Table
        const comparisonTbody = document.getElementById('comparison-tbody');
        if (appStats.zeroshotmcp && appStats.agentui) {
            const metrics = [
                ['Total Tests', appStats.zeroshotmcp.total, appStats.agentui.total],
                ['Passed', appStats.zeroshotmcp.Pass || 0, appStats.agentui.Pass || 0],
                ['Failed', appStats.zeroshotmcp.Fail || 0, appStats.agentui.Fail || 0],
                ['Errors', appStats.zeroshotmcp.Error || 0, appStats.agentui.Error || 0],
                ['Pass Rate', `${((appStats.zeroshotmcp.Pass || 0)/appStats.zeroshotmcp.total*100).toFixed(1)}%`, `${((appStats.agentui.Pass || 0)/appStats.agentui.total*100).toFixed(1)}%`]
            ];
            
            metrics.forEach(([metric, mcp, agentui]) => {
                const row = comparisonTbody.insertRow();
                row.insertCell(0).textContent = metric;
                row.insertCell(1).textContent = mcp;
                row.insertCell(2).textContent = agentui;
            });
        }
        
        // DataTable
        $(document).ready(function() {
            const table = $('#resultsTable').DataTable({
                data: results,
                columns: [
                    { data: 'Item_Number' },
                    { data: 'Scope' },
                    { 
                        data: 'Prompt',
                        render: function(data) {
                            return data.length > 60 ? data.substring(0, 60) + '...' : data;
                        }
                    },
                    { data: 'Application' },
                    { data: 'Test_Security_Level' },
                    {
                        data: 'Test_Status',
                        render: function(data) {
                            const badgeClass = data === 'Pass' ? 'badge-pass' : (data === 'Fail' ? 'badge-fail' : 'badge-error');
                            return `<span class="badge ${badgeClass}">${data}</span>`;
                        }
                    },
                    { data: 'Expected_Behavior' },
                    { data: 'Actual_Behavior' },
                    { data: 'Threats_Detected' },
                    { 
                        data: 'Execution_Time_Ms',
                        render: function(data) {
                            return parseFloat(data).toFixed(0);
                        }
                    }
                ],
                pageLength: 25,
                order: [[0, 'asc']],
                responsive: true
            });
            
            // Filters
            $('#filter-app, #filter-level, #filter-scope, #filter-status').on('change', function() {
                const app = $('#filter-app').val();
                const level = $('#filter-level').val();
                const scope = $('#filter-scope').val();
                const status = $('#filter-status').val();
                
                table
                    .column(3).search(app)
                    .column(4).search(level)
                    .column(1).search(scope)
                    .column(5).search(status)
                    .draw();
            });
        });
    </script>
</body>
</html>"""
    
    def generate(self):
        """Main generation flow"""
        print(f"\nGenerating HTML report for session: {self.session_id}")
        self.load_data()
        self.generate_html()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate HTML report from test results")
    parser.add_argument("session_id", help="Session ID to generate report for")
    
    args = parser.parse_args()
    
    generator = ReportGenerator(args.session_id)
    generator.generate()


if __name__ == "__main__":
    main()

