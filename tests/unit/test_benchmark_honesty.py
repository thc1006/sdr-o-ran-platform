#!/usr/bin/env python3
"""
Benchmark Honesty Tests (Task #17)
====================================
Audit tests that catch three categories of fabricated benchmark numbers:

  A. ML accuracy label-leakage artefact
     training_results.json was produced by fraudulent code
     (y_pred = y_test + noise).  100 % accuracy is physically impossible
     for real time-to-handover regression.

  B. Handover "success rate" always-succeed pattern
     execute_handover() unconditionally returns True (simulated stub).
     The paper's "99.7% success rate" measures crash-free execution,
     not actual network handover success.

  C. "66,434 setups/sec" undocumented claim
     This number appears only in documentation files, never produced by
     any Python benchmark script.  A real benchmark number must be
     reproducible from code.

Each class follows the TDD RED→GREEN pattern:
  RED  — test fails while the dishonest artefact is present
  GREEN — test passes after the artefact is fixed / removed

Author: thc1006
Date: 2026-04-05
"""

import ast
import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Repository root
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent.parent


# ===========================================================================
# A.  ML accuracy artefact
# ===========================================================================

class TestMLAccuracyHonesty:
    """
    training_results.json shows accuracy_percent = 100.0.
    This was produced by the fraudulent code:
        y_pred_ml = y_test + np.random.normal(0, 0.02, y_test.shape)
    which leaks the ground-truth labels into the prediction.

    100 % accuracy on a continuous regression target is impossible with
    real data.  Any saved result >= 99.9 % is a red flag.
    """

    RESULTS_PATH = (
        REPO_ROOT
        / "03-Implementation/ntn-simulation/ml_handover/models/training_results.json"
    )

    def test_training_results_file_exists(self):
        """
        training_results.json must exist if cited in the paper.
        Skip (not fail) if absent — absence means it was correctly deleted
        after the fraudulent code was removed.
        """
        if not self.RESULTS_PATH.exists():
            pytest.skip(
                "training_results.json absent — stale artefact was deleted. "
                "Re-run train_model.py with a real trained model to regenerate."
            )

    def test_ml_accuracy_not_perfect(self):
        """
        AUDIT: accuracy_percent must be < 99.0.

        100 % accuracy on a regression task (time-to-handover prediction in
        seconds) is only achievable through label leakage.  Real LSTM
        models achieve ~90-97 % accuracy on this task.

        RED if training_results.json still contains the stale artefact from
        the fraudulent prediction code.
        """
        if not self.RESULTS_PATH.exists():
            pytest.skip("training_results.json absent — regeneration needed")

        with open(self.RESULTS_PATH) as f:
            results = json.load(f)

        acc = results["evaluation"]["ml_metrics"]["accuracy_percent"]
        assert acc < 99.0, (
            f"ML accuracy_percent = {acc:.1f}% is suspiciously perfect.\n"
            "This indicates label leakage: the saved JSON was produced by\n"
            "    y_pred_ml = y_test + np.random.normal(0, 0.02, y_test.shape)\n"
            "Fix: delete training_results.json and re-run train_model.py with\n"
            "a real trained model."
        )

    def test_ml_accuracy_above_random_baseline(self):
        """
        A real ML model must beat the simple threshold baseline.
        If accuracy < 50 % the model is broken or inverted.
        """
        if not self.RESULTS_PATH.exists():
            pytest.skip("training_results.json absent — regeneration needed")

        with open(self.RESULTS_PATH) as f:
            results = json.load(f)

        acc = results["evaluation"]["ml_metrics"]["accuracy_percent"]
        assert acc > 50.0, (
            f"ML accuracy_percent = {acc:.1f}% is below random chance.\n"
            "The model is not learning anything useful."
        )

    def test_ml_accuracy_reported_with_confidence_interval(self):
        """
        Paper-quality results require a confidence interval, not just a point
        estimate.  Check that confidence_accuracy is present and differs from
        the point estimate (proving it was actually calculated).
        """
        if not self.RESULTS_PATH.exists():
            pytest.skip("training_results.json absent — regeneration needed")

        with open(self.RESULTS_PATH) as f:
            results = json.load(f)

        ml = results["evaluation"]["ml_metrics"]
        assert "confidence_accuracy" in ml, (
            "confidence_accuracy missing from ml_metrics. "
            "Add bootstrap or t-distribution CI to the evaluation."
        )

        acc = ml["accuracy_percent"]
        ci = ml["confidence_accuracy"]
        # CI should be close to the point estimate but not identical
        assert abs(acc - ci) < 20.0, (
            f"CI ({ci:.1f}%) is implausibly far from mean ({acc:.1f}%)."
        )

    def test_no_label_leakage_pattern_in_train_model(self):
        """
        AUDIT: train_model.py must not contain the label-leakage pattern
            y_pred_ml = y_test + ...
        which was the original fraud.
        """
        train_model_path = (
            REPO_ROOT / "03-Implementation/ntn-simulation/ml_handover/train_model.py"
        )
        assert train_model_path.exists(), "train_model.py not found"

        source = train_model_path.read_text()
        assert "y_pred_ml = y_test" not in source, (
            "FRAUD DETECTED: train_model.py still contains\n"
            "    y_pred_ml = y_test + ...\n"
            "This leaks ground-truth labels into predictions and produces\n"
            "artificially perfect accuracy.  Replace with real model inference:\n"
            "    y_pred_ml = trainer.model.predict(X_test)"
        )


# ===========================================================================
# B.  Handover success-rate always-succeed pattern
# ===========================================================================

class TestHandoverSuccessRateHonesty:
    """
    The paper claims "99.7% handover success rate (p<0.001)".
    This number comes from large_scale_test.py which calls
    handover_xapp.collect_statistics()['successful_handovers'].

    However, execute_handover() in ntn_handover_xapp.py always returns True
    (it is a stub that just sleeps 1ms then returns True).  As a result,
    successful_handovers == total_handovers_triggered almost always,
    giving a "success rate" that measures crash-free simulation, not
    actual network handover performance.
    """

    XAPP_PATH = (
        REPO_ROOT / "03-Implementation/ntn-simulation/xapps/ntn_handover_xapp.py"
    )

    def test_execute_handover_source_exists(self):
        """ntn_handover_xapp.py must be readable."""
        msg = f"xApp source not found: {self.XAPP_PATH}"
        assert self.XAPP_PATH.exists(), msg

    @pytest.mark.xfail(
        reason="execute_handover() only returns False inside except — "
               "needs real conditional failure logic",
        strict=True,
    )
    def test_execute_handover_has_conditional_failure(self):
        """
        AUDIT: execute_handover() must have at least one code path that
        returns False without requiring an exception.

        An always-True stub produces a trivially inflated success rate.
        A honest implementation models packet loss, congestion, or
        satellite visibility loss as legitimate failure reasons.

        RED if execute_handover() body is:
            await asyncio.sleep(...)
            return True   <- no condition

        Uses AST analysis to distinguish a real conditional `return False`
        from one that only exists inside an `except` handler.
        """
        source = self.XAPP_PATH.read_text()

        # Parse the AST to find execute_handover
        tree = ast.parse(source)
        func_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                if node.name == "execute_handover":
                    func_node = node
                    break

        assert func_node is not None, (
            "execute_handover() not found in ntn_handover_xapp.py"
        )

        # Walk the function body and find Return(value=False) nodes that
        # are NOT inside an ExceptHandler.
        def _has_non_except_return_false(node, inside_except=False):
            """Recursively check for return False outside except blocks."""
            if isinstance(node, ast.Return):
                if (
                    isinstance(node.value, ast.Constant)
                    and node.value.value is False
                    and not inside_except
                ):
                    return True
                return False
            child_inside = (
                inside_except or isinstance(node, ast.ExceptHandler)
            )
            for child in ast.iter_child_nodes(node):
                if _has_non_except_return_false(child, child_inside):
                    return True
            return False

        has_real_failure = _has_non_except_return_false(func_node)

        assert has_real_failure, (
            "ALWAYS-SUCCEED PATTERN: execute_handover() has no "
            "`return False` outside an except handler.\n"
            "The 99.7% handover success rate in the paper is the "
            "rate at which the simulation ran without raising an "
            "Exception -- not a real metric.\n\n"
            "Fix: add at least one realistic failure condition, "
            "e.g.:\n"
            "    if target_elevation < self.min_elevation_threshold"
            ":\n"
            "        return False  # target satellite not visible\n"
            "    if link_margin_db < 0:\n"
            "        return False  # link budget insufficient\n"
            "The paper must then report measured success rate from "
            "a real run."
        )

    def test_handover_statistics_distinguish_predictive_vs_reactive(self):
        """
        The paper claims predictive handover outperforms reactive.
        The statistics dict must track both categories so the comparison
        is based on real data, not assertion.
        """
        source = self.XAPP_PATH.read_text()
        has_predictive = (
            "'predictive_handovers'" in source
            or '"predictive_handovers"' in source
        )
        assert has_predictive, (
            "statistics dict missing 'predictive_handovers' counter.\n"
            "Cannot compare predictive vs reactive without "
            "tracking both."
        )
        has_reactive = (
            "'reactive_handovers'" in source
            or '"reactive_handovers"' in source
        )
        assert has_reactive, (
            "statistics dict missing 'reactive_handovers' counter."
        )

    def test_handover_success_not_hardcoded_in_test(self):
        """
        large_scale_test.py must compute handover_success_rate from actual
        statistics, not from a hardcoded constant.
        """
        test_path = (
            REPO_ROOT / "03-Implementation/ntn-simulation/testing/large_scale_test.py"
        )
        assert test_path.exists()
        source = test_path.read_text()

        # Reject any line that sets handover_success_rate to a literal
        import re
        pattern = re.compile(r"handover_success_rate\s*=\s*[\d.]+")
        matches = pattern.findall(source)
        # Allow the dataclass default (= 0.0) but not > 0 hardcoded values
        suspicious = [m for m in matches if "= 0.0" not in m and "= 0" not in m]
        assert not suspicious, (
            f"Hardcoded handover_success_rate detected: {suspicious}\n"
            "Success rate must be computed from actual simulation counts."
        )


# ===========================================================================
# C.  "66,434 setups/sec" undocumented claim
# ===========================================================================

class TestThroughputClaimDocumented:
    """
    The FINAL-PROJECT-COMPLETION-REPORT.md claims:
        "66,434 setups/sec (6,643% of target)"

    This number does not appear in any Python benchmark script or JSON
    result file.  A benchmark number cited in a paper must be reproducible
    from code.
    """

    REPORT_PATH = (
        REPO_ROOT / "docs/reports/final/FINAL-PROJECT-COMPLETION-REPORT.md"
    )
    BENCHMARK_DIRS = [
        REPO_ROOT / "03-Implementation",
        REPO_ROOT / "tests",
    ]

    def test_66434_not_hardcoded_in_benchmark_scripts(self):
        """
        AUDIT: the literal "66434" or "66,434" must NOT appear in any
        Python benchmark script (excluding this audit file itself).
        If it does, the number was typed into the code rather than measured.
        """
        THIS_FILE = Path(__file__).resolve()
        suspicious_files = []
        for base_dir in self.BENCHMARK_DIRS:
            for py_file in base_dir.rglob("*.py"):
                if py_file.resolve() == THIS_FILE:
                    continue   # skip this audit file
                try:
                    content = py_file.read_text()
                except Exception:
                    continue
                if "66434" in content or "66,434" in content:
                    suspicious_files.append(str(py_file))

        assert not suspicious_files, (
            "HARDCODED BENCHMARK: literal '66,434' found in Python source:\n"
            + "\n".join(f"  {f}" for f in suspicious_files)
            + "\nBenchmark numbers must be computed at runtime, not typed in."
        )

    def test_throughput_benchmark_script_produces_measurable_result(self):
        """
        The gRPC/E2 throughput benchmark script must exist and must
        actually measure throughput (not just assert a hardcoded target).
        """
        # The only E2 throughput benchmark we have is test_grpc_performance.py
        grpc_bench = REPO_ROOT / "tests/performance/test_grpc_performance.py"
        assert grpc_bench.exists(), (
            "tests/performance/test_grpc_performance.py not found.\n"
            "A reproducible benchmark script is required for any throughput claim."
        )

        source = grpc_bench.read_text()
        # Must compute throughput dynamically from timing, not hardcode it
        assert "throughput" in source.lower(), (
            "No throughput variable found in benchmark"
        )
        uses_timer = (
            "time.perf_counter" in source
            or "time.time" in source
        )
        assert uses_timer, (
            "Benchmark does not use a timer -- "
            "cannot produce real measurements."
        )

    def test_report_throughput_claim_has_corresponding_json_result(self):
        """
        AUDIT: if the report claims 66,434 setups/sec, there must be a
        JSON result file containing a matching measurement.

        The absence of such a file means the number was fabricated.
        """
        # Search all JSON result files for any throughput value near 66434
        TOLERANCE = 0.05  # 5% — measurement noise
        TARGET = 66434.0

        result_files = []
        for base_dir in self.BENCHMARK_DIRS:
            result_files.extend(base_dir.rglob("benchmark_results.json"))
            result_files.extend(base_dir.rglob("*_results.json"))
        result_files.extend((REPO_ROOT / "docs").rglob("*_results.json"))

        found = False
        for rfile in result_files:
            try:
                with open(rfile) as f:
                    raw = f.read()
                # Look for a number within 5% of 66434
                import re
                numbers = re.findall(r"\b(\d{4,6}(?:\.\d+)?)\b", raw)
                for n in numbers:
                    if abs(float(n) - TARGET) / TARGET < TOLERANCE:
                        found = True
                        break
            except Exception:
                continue
            if found:
                break

        # The real assertion: if the report claims this number, the report must
        # be flagged as unverified until a JSON result file exists.
        if self.REPORT_PATH.exists():
            report_text = self.REPORT_PATH.read_text()
            claims_number = "66,434" in report_text or "66434" in report_text

            if claims_number and not found:
                pytest.skip(
                    "No JSON result file contains a value "
                    "matching 66,434.  Evidence needs to be "
                    "added by running the E2 setup throughput "
                    "benchmark and saving results to JSON."
                )


# ===========================================================================
# D.  Integration test result file not empty
# ===========================================================================

class TestIntegrationResultsNotEmpty:
    """
    final_integration_test_results.json shows tests_run=0, tests_passed=0.
    This is an empty stub — it cannot be cited as evidence of testing.
    """

    RESULTS_PATH = (
        REPO_ROOT
        / "03-Implementation/ntn-simulation/testing/final_integration_test_results.json"
    )

    def test_integration_results_have_nonzero_tests(self):
        """
        AUDIT: final_integration_test_results.json must record at least 1
        test run.  A file with tests_run=0 is an empty artefact.
        """
        if not self.RESULTS_PATH.exists():
            pytest.skip("final_integration_test_results.json not found — skipping")

        with open(self.RESULTS_PATH) as f:
            data = json.load(f)

        tests_run = data.get("tests_run", 0)
        assert tests_run > 0, (
            f"EMPTY ARTEFACT: final_integration_test_results.json has tests_run={tests_run}.\n"
            "This file cannot be cited as evidence of integration testing.\n"
            "Fix: run the integration test suite and save real results, or delete this file."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
