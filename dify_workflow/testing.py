"""
Workflow Testing Framework
Unit testing for workflows with fixtures, assertions, and mocks
"""
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class TestResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class WorkflowTest:
    """Single workflow test case"""
    name: str
    inputs: Dict[str, Any]
    expected_outputs: Dict[str, Any]
    description: str = ""
    timeout: float = 30.0
    tags: List[str] = field(default_factory=list)


@dataclass
class TestReport:
    """Test execution report"""
    test_name: str
    result: TestResult
    duration_ms: float
    actual_outputs: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)


class WorkflowTestSuite:
    """Test suite for workflows"""

    def __init__(self, workflow):
        self.workflow = workflow
        self.tests: List[WorkflowTest] = []
        self.fixtures: Dict[str, Any] = {}
        self.mocks: Dict[str, Callable] = {}
        self.reports: List[TestReport] = []

    def add_test(
        self,
        name: str,
        inputs: Dict[str, Any],
        expected_outputs: Dict[str, Any],
        description: str = "",
        timeout: float = 30.0,
        tags: Optional[List[str]] = None
    ) -> WorkflowTest:
        """Add a test case"""
        test = WorkflowTest(
            name=name,
            inputs=inputs,
            expected_outputs=expected_outputs,
            description=description,
            timeout=timeout,
            tags=tags or []
        )
        self.tests.append(test)
        return test

    def add_fixture(self, name: str, value: Any):
        """Add a test fixture"""
        self.fixtures[name] = value

    def add_mock(self, node_id: str, mock_func: Callable):
        """Add a mock for a specific node"""
        self.mocks[node_id] = mock_func

    async def run_all(self, stop_on_fail: bool = False) -> Dict[str, Any]:
        """Run all tests"""
        self.reports = []
        passed = 0
        failed = 0
        skipped = 0
        errors = 0

        for test in self.tests:
            report = await self._run_test(test)
            self.reports.append(report)

            if report.result == TestResult.PASS:
                passed += 1
            elif report.result == TestResult.FAIL:
                failed += 1
                if stop_on_fail:
                    break
            elif report.result == TestResult.SKIP:
                skipped += 1
            else:
                errors += 1

        return {
            "total": len(self.tests),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "reports": self.reports
        }

    async def run_test(self, test_name: str) -> Optional[TestReport]:
        """Run a specific test by name"""
        for test in self.tests:
            if test.name == test_name:
                return await self._run_test(test)
        return None

    async def _run_test(self, test: WorkflowTest) -> TestReport:
        """Execute a single test"""
        from .executor import WorkflowExecutor

        start_time = time.time()

        try:
            # Merge fixtures with inputs
            test_inputs = {**self.fixtures, **test.inputs}

            # Execute workflow
            executor = WorkflowExecutor(self.workflow)

            # Apply mocks
            for node_id, mock_func in self.mocks.items():
                # In real implementation, inject mocks into executor
                pass

            result = await executor.execute(test_inputs)

            duration_ms = (time.time() - start_time) * 1000

            # Check outputs
            if result.status.value == "completed":
                actual = result.outputs
                expected = test.expected_outputs

                # Compare outputs
                if self._compare_outputs(actual, expected):
                    return TestReport(
                        test_name=test.name,
                        result=TestResult.PASS,
                        duration_ms=duration_ms,
                        actual_outputs=actual
                    )
                else:
                    return TestReport(
                        test_name=test.name,
                        result=TestResult.FAIL,
                        duration_ms=duration_ms,
                        actual_outputs=actual,
                        error_message=f"Expected {expected}, got {actual}"
                    )
            else:
                return TestReport(
                    test_name=test.name,
                    result=TestResult.ERROR,
                    duration_ms=duration_ms,
                    error_message=result.error or "Execution failed"
                )

        except Exception as e:
            return TestReport(
                test_name=test.name,
                result=TestResult.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )

    def _compare_outputs(self, actual: Dict, expected: Dict) -> bool:
        """Compare actual vs expected outputs"""
        for key, expected_value in expected.items():
            if key not in actual:
                return False

            actual_value = actual[key]

            # Handle different comparison types
            if isinstance(expected_value, dict):
                if "_contains" in expected_value:
                    # Check if actual contains substring
                    if expected_value["_contains"] not in str(actual_value):
                        return False
                elif "_regex" in expected_value:
                    import re
                    if not re.search(expected_value["_regex"], str(actual_value)):
                        return False
                elif "_type" in expected_value:
                    if type(actual_value).__name__ != expected_value["_type"]:
                        return False
                else:
                    if actual_value != expected_value:
                        return False
            else:
                if actual_value != expected_value:
                    return False

        return True

    def assert_contains(self, text: str) -> Dict[str, str]:
        """Assertion helper - check if output contains text"""
        return {"_contains": text}

    def assert_regex(self, pattern: str) -> Dict[str, str]:
        """Assertion helper - check if output matches regex"""
        return {"_regex": pattern}

    def assert_type(self, type_name: str) -> Dict[str, str]:
        """Assertion helper - check output type"""
        return {"_type": type_name}

    def export_results(self, filename: str):
        """Export test results to file"""
        results = {
            "workflow": self.workflow.name,
            "tests_run": len(self.reports),
            "tests": [
                {
                    "name": r.test_name,
                    "result": r.result.value,
                    "duration_ms": r.duration_ms,
                    "error": r.error_message
                }
                for r in self.reports
            ]
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)


class WorkflowMock:
    """Mock utilities for testing"""

    @staticmethod
    def mock_llm_response(response_text: str) -> Callable:
        """Create mock LLM response"""
        def mock(*args, **kwargs):
            return {"text": response_text}
        return mock

    @staticmethod
    def mock_http_response(status: int = 200, body: str = "{}") -> Callable:
        """Create mock HTTP response"""
        def mock(*args, **kwargs):
            return {
                "status_code": status,
                "body": body,
                "headers": {"Content-Type": "application/json"}
            }
        return mock

    @staticmethod
    def mock_code_execution(result: Dict) -> Callable:
        """Create mock code execution"""
        def mock(*args, **kwargs):
            return result
        return mock


# Convenience functions
def create_test_suite(workflow) -> WorkflowTestSuite:
    """Create a test suite for a workflow"""
    return WorkflowTestSuite(workflow)


def load_test_suite(workflow, test_file: str) -> WorkflowTestSuite:
    """Load test suite from file"""
    suite = WorkflowTestSuite(workflow)

    with open(test_file) as f:
        data = json.load(f)

    for test_data in data.get("tests", []):
        suite.add_test(
            name=test_data["name"],
            inputs=test_data["inputs"],
            expected_outputs=test_data["expected_outputs"],
            description=test_data.get("description", ""),
            tags=test_data.get("tags", [])
        )

    return suite


def run_tests(workflow, tests_file: str) -> Dict[str, Any]:
    """Run tests from file"""
    import asyncio

    suite = load_test_suite(workflow, tests_file)
    return asyncio.run(suite.run_all())
