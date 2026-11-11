#!/usr/bin/env python3
"""
Test Runner for BLG 345E Term Project Phase 1
Tests Kripke structure JSON files against the project specification and/or the compiled checker binary.

Usage:
    python tests/test_runner.py                  # Auto-detects checker binary, falls back to spec validation
    python tests/test_runner.py --validate-only  # Validates JSON files and test suite integrity using pure Python
    python tests/test_runner.py --checker ./my_checker.exe  # Tests against a specific checker binary
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path
from collections import deque

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
MANIFEST_PATH = TESTS_DIR / "tests_manifest.json"
SCHEMA_PATH = TESTS_DIR / "schema.json"


def validate_json_schema_pure_python(data, schema):
    """
    Validates data against schema without external dependencies.
    Covers the required BLG 345E schema rules:
      - object with required: atomic_propositions, initial_states, states
      - additionalProperties: false
      - array of strings for APs and initial_states
      - states: dict of objects with labels and transitions (arrays of strings)
    Returns: (is_valid: bool, error_message: str)
    """
    if not isinstance(data, dict):
        return False, f"Expected top-level object, got {type(data).__name__}"

    required_keys = {"atomic_propositions", "initial_states", "states"}
    missing = required_keys - set(data.keys())
    if missing:
        return False, f"Missing required top-level key(s): {', '.join(sorted(missing))}"

    extra = set(data.keys()) - required_keys
    if extra:
        return False, f"Unexpected top-level key(s): {', '.join(sorted(extra))}"

    # atomic_propositions
    aps = data["atomic_propositions"]
    if not isinstance(aps, list):
        return False, f"'atomic_propositions' must be an array, got {type(aps).__name__}"
    for i, item in enumerate(aps):
        if not isinstance(item, str):
            return False, f"'atomic_propositions[{i}]' must be a string, got {type(item).__name__}"

    # initial_states
    inits = data["initial_states"]
    if not isinstance(inits, list):
        return False, f"'initial_states' must be an array, got {type(inits).__name__}"
    for i, item in enumerate(inits):
        if not isinstance(item, str):
            return False, f"'initial_states[{i}]' must be a string, got {type(item).__name__}"

    # states
    states = data["states"]
    if not isinstance(states, dict):
        return False, f"'states' must be an object/dict, got {type(states).__name__}"

    for s_name, s_val in states.items():
        if not isinstance(s_val, dict):
            return False, f"State '{s_name}' must be an object, got {type(s_val).__name__}"
        s_req = {"labels", "transitions"}
        s_missing = s_req - set(s_val.keys())
        if s_missing:
            return False, f"State '{s_name}' missing required key(s): {', '.join(sorted(s_missing))}"
        s_extra = set(s_val.keys()) - s_req
        if s_extra:
            return False, f"State '{s_name}' contains unexpected key(s): {', '.join(sorted(s_extra))}"

        labels = s_val["labels"]
        if not isinstance(labels, list):
            return False, f"State '{s_name}' 'labels' must be an array, got {type(labels).__name__}"
        for i, item in enumerate(labels):
            if not isinstance(item, str):
                return False, f"State '{s_name}' label[{i}] must be a string, got {type(item).__name__}"

        trans = s_val["transitions"]
        if not isinstance(trans, list):
            return False, f"State '{s_name}' 'transitions' must be an array, got {type(trans).__name__}"
        for i, item in enumerate(trans):
            if not isinstance(item, str):
                return False, f"State '{s_name}' transition[{i}] must be a string, got {type(item).__name__}"

    return True, ""


def check_semantics_python(data):
    """
    Performs Phase 2 semantic validation in Python to verify test fixtures:
      1. Dangling transitions
      2. Undeclared atomic propositions in labels
      3. Transition totality (dead-ends)
      4. Invalid / empty initial states
      5. Duplicate entries in APs, initial_states, labels, transitions
      6. Empty state space
    Returns: (is_valid: bool, error_message: str)
    """
    aps = data.get("atomic_propositions", [])
    inits = data.get("initial_states", [])
    states = data.get("states", {})

    # Check empty state space
    if len(states) == 0:
        return False, "Semantic error: State space is empty"

    # Check empty initial states
    if len(inits) == 0:
        return False, "Semantic error: Initial states list is empty"

    # Check duplicates in APs
    if len(aps) != len(set(aps)):
        return False, "Semantic error: Duplicate atomic propositions declared"

    # Check duplicates in initial states
    if len(inits) != len(set(inits)):
        return False, "Semantic error: Duplicate initial states declared"

    # Check initial states existence
    for init_st in inits:
        if init_st not in states:
            return False, f"Semantic error: Initial state '{init_st}' not found in declared states"

    valid_aps = set(aps)
    all_states = set(states.keys())

    for s_name, s_body in states.items():
        labels = s_body.get("labels", [])
        trans = s_body.get("transitions", [])

        # Check duplicate labels
        if len(labels) != len(set(labels)):
            return False, f"Semantic error: Duplicate labels in state '{s_name}'"

        # Check undeclared labels
        for lbl in labels:
            if lbl not in valid_aps:
                return False, f"Semantic error: State '{s_name}' has undeclared atomic proposition '{lbl}'"

        # Check transition totality
        if len(trans) == 0:
            return False, f"Semantic error: State '{s_name}' has no outgoing transitions (dead-end)"

        # Check duplicate transitions
        if len(trans) != len(set(trans)):
            return False, f"Semantic error: Duplicate transitions in state '{s_name}'"

        # Check dangling transitions
        for target in trans:
            if target not in all_states:
                return False, f"Semantic error: State '{s_name}' transitions to undeclared state '{target}'"

    return True, ""


def compute_reachability(data):
    """
    Computes reachable and unreachable states via BFS.
    """
    inits = data.get("initial_states", [])
    states = data.get("states", {})

    visited = set(inits)
    queue = deque(inits)

    while queue:
        curr = queue.popleft()
        if curr in states:
            for nxt in states[curr].get("transitions", []):
                if nxt in states and nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

    all_states = set(states.keys())
    unreachable = all_states - visited
    return len(visited), len(unreachable)


def run_test_on_executable(checker_path, test_path, test_meta):
    """
    Runs the checker binary with '--parse <test_path>' and verifies stdout/stderr/exit_code.
    """
    cmd = [str(checker_path), "--parse", str(test_path)]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            cwd=PROJECT_ROOT
        )
    except subprocess.TimeoutExpired:
        return False, "Execution timed out (10s)"
    except Exception as e:
        return False, f"Execution failed: {e}"

    category = test_meta["category"]
    expected_exit = test_meta["expected_exit_code"]

    # Check exit code
    if expected_exit == 0 and proc.returncode != 0:
        return False, f"Expected exit code 0, got {proc.returncode}. Stderr: {proc.stderr.strip()}"
    if expected_exit != 0 and proc.returncode == 0:
        return False, f"Expected nonzero exit code, got 0. Stdout: {proc.stdout.strip()}"

    # For valid tests, verify required stdout headers
    if category == "valid":
        for prefix in test_meta.get("expected_output_prefixes", []):
            if prefix not in proc.stdout:
                return False, f"Missing expected stdout prefix '{prefix}'. Got:\n{proc.stdout.strip()}"

    # For error tests, verify error prefix in stderr
    expected_prefix = test_meta.get("expected_error_prefix")
    if expected_prefix:
        combined_err = proc.stderr + proc.stdout
        if expected_prefix not in combined_err:
            return False, f"Expected error prefix '{expected_prefix}' not found in output. Stderr: {proc.stderr.strip()}"

    return True, "Passed"


def find_checker_binary(explicit_path=None):
    if explicit_path:
        p = Path(explicit_path)
        if p.exists():
            return p
        return None

    candidates = [
        PROJECT_ROOT / "my_checker.exe",
        PROJECT_ROOT / "my_checker",
        PROJECT_ROOT / "build" / "my_checker.exe",
        PROJECT_ROOT / "build" / "my_checker",
        PROJECT_ROOT / "bin" / "my_checker.exe",
        PROJECT_ROOT / "bin" / "my_checker",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def main():
    parser = argparse.ArgumentParser(description="BLG 345E Project Phase 1 Test Runner")
    parser.add_argument("--checker", help="Path to compiled checker executable")
    parser.add_argument("--validate-only", action="store_true", help="Only validate test JSON fixtures against spec")
    parser.add_argument("--category", choices=["valid", "syntax_error", "schema_error", "semantic_error"], help="Filter by category")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"[ERROR] Test manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    tests = manifest["tests"]
    if args.category:
        tests = [t for t in tests if t["category"] == args.category]

    print("=" * 70)
    print("BLG 345E Phase 1: Test Suite Runner")
    print(f"Total test cases loaded: {len(tests)}")
    print("=" * 70)

    # 1. Spec validation of test files themselves
    print("\n--- Phase A: Validating Test Fixture Files Against Specification ---")
    spec_passed = 0
    spec_failed = 0

    for t in tests:
        t_path = TESTS_DIR / t["file"]
        t_cat = t["category"]
        t_id = t["id"]

        if not t_path.exists():
            print(f"  [FAIL] {t_id}: File does not exist: {t_path}")
            spec_failed += 1
            continue

        # Check Syntax
        raw_text = t_path.read_text(encoding="utf-8")
        parsed_json = None
        syntax_err = None
        try:
            parsed_json = json.loads(raw_text)
        except Exception as e:
            syntax_err = str(e)

        if t_cat == "syntax_error":
            if syntax_err:
                spec_passed += 1
                if args.verbose:
                    print(f"  [OK]   {t_id} correctly triggered syntax error: {syntax_err[:40]}...")
            else:
                spec_failed += 1
                print(f"  [FAIL] {t_id} was expected to fail syntax parsing, but parsed successfully!")
            continue

        if syntax_err:
            spec_failed += 1
            print(f"  [FAIL] {t_id} unexpected JSON syntax error: {syntax_err}")
            continue

        # Check Schema
        is_schema_valid, schema_msg = validate_json_schema_pure_python(parsed_json, schema)
        if t_cat == "schema_error":
            if not is_schema_valid:
                spec_passed += 1
                if args.verbose:
                    print(f"  [OK]   {t_id} correctly triggered schema error: {schema_msg}")
            else:
                spec_failed += 1
                print(f"  [FAIL] {t_id} was expected to fail schema validation, but passed!")
            continue

        if not is_schema_valid:
            spec_failed += 1
            print(f"  [FAIL] {t_id} unexpected schema error: {schema_msg}")
            continue

        # Check Semantic
        is_semantic_valid, semantic_msg = check_semantics_python(parsed_json)
        if t_cat == "semantic_error":
            if not is_semantic_valid:
                spec_passed += 1
                if args.verbose:
                    print(f"  [OK]   {t_id} correctly triggered semantic error: {semantic_msg}")
            else:
                spec_failed += 1
                print(f"  [FAIL] {t_id} was expected to fail semantic validation, but passed!")
            continue

        if not is_semantic_valid:
            spec_failed += 1
            print(f"  [FAIL] {t_id} unexpected semantic error: {semantic_msg}")
            continue

        # Valid model checks
        if t_cat == "valid":
            reach, unreach = compute_reachability(parsed_json)
            exp_metrics = t.get("expected_metrics", {})
            if exp_metrics.get("reachable_states") == reach and exp_metrics.get("unreachable_states") == unreach:
                spec_passed += 1
                if args.verbose:
                    print(f"  [OK]   {t_id} valid model verified (reachable={reach}, unreachable={unreach})")
            else:
                spec_failed += 1
                print(f"  [FAIL] {t_id} reachability mismatch: expected {exp_metrics}, got reach={reach}, unreach={unreach}")

    print(f"Phase A Result: {spec_passed} passed, {spec_failed} failed.")

    if args.validate_only:
        print("\n[INFO] --validate-only requested. Skipping executable testing.")
        sys.exit(0 if spec_failed == 0 else 1)

    # 2. Executable testing
    checker = find_checker_binary(args.checker)
    print("\n--- Phase B: Testing Executable Binary ---")
    if not checker:
        print("[INFO] No compiled checker binary found (searched project root and build/).")
        print("       Once your parser/checker is built (e.g. ./my_checker.exe), re-run:")
        print("       python tests/test_runner.py --checker <path_to_binary>")
        sys.exit(0 if spec_failed == 0 else 1)

    print(f"Testing against checker executable: {checker}")
    bin_passed = 0
    bin_failed = 0

    for t in tests:
        t_path = TESTS_DIR / t["file"]
        t_id = t["id"]
        t_desc = t["description"]

        ok, msg = run_test_on_executable(checker, t_path, t)
        if ok:
            bin_passed += 1
            print(f"  [PASS] {t_id:<12} {t_desc[:45]:<45} : {msg}")
        else:
            bin_failed += 1
            print(f"  [FAIL] {t_id:<12} {t_desc[:45]:<45} : {msg}")

    print("\n" + "=" * 70)
    print(f"Phase B Executable Test Result: {bin_passed} passed, {bin_failed} failed out of {len(tests)}")
    print("=" * 70)

    sys.exit(0 if (spec_failed == 0 and bin_failed == 0) else 1)


if __name__ == "__main__":
    main()
