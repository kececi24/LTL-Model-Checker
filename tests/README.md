# Test Suite for BLG 345E Phase 1 (Explicit-State LTL Model Checker)

This directory contains the automated test suite and test cases for **BLG 345E Term Project Phase 1: Structural Modeling, Parsing and Oracle Validation**.

The JSON structure and validation rules strictly follow the project specification (`BLG345E_Term_Project_1-4.pdf`) and the reference model (`example.json`).

---

## 1. Directory Structure

```text
tests/
├── schema.json                 # Formal JSON Schema (Draft-07) for models
├── tests_manifest.json         # Structured metadata & expected outputs for all tests
├── test_runner.py              # Automated test runner script (Pure Python)
├── README.md                   # This documentation
├── valid/                      # Structurally valid models
│   ├── 01_light_switch.json
│   ├── 02_unreachable_states.json
│   ├── 03_multiple_initial_states.json
│   ├── 04_single_state_self_loop.json
│   ├── 05_dining_philosophers_sample.json
│   └── 06_complex_branching_and_cycles.json
├── syntax_error/               # Malformed JSON syntax (Prefix: [SYNTAX ERROR])
│   ├── syntax_unclosed_brace.json
│   ├── syntax_trailing_comma.json
│   ├── syntax_missing_colon.json
│   ├── syntax_unquoted_key.json
│   └── syntax_empty_file.json
├── schema_error/               # Schema violations (Prefix: [SCHEMA ERROR])
│   ├── schema_missing_atomic_propositions.json
│   ├── schema_missing_initial_states.json
│   ├── schema_missing_states.json
│   ├── schema_unexpected_toplevel_key.json
│   ├── schema_unexpected_state_key.json
│   ├── schema_missing_state_labels.json
│   ├── schema_missing_state_transitions.json
│   ├── schema_wrong_type_atomic_propositions.json
│   ├── schema_wrong_type_initial_states.json
│   ├── schema_wrong_type_states.json
│   ├── schema_wrong_type_ap_element.json
│   ├── schema_wrong_type_initial_states_element.json
│   ├── schema_wrong_type_labels_element.json
│   └── schema_wrong_type_transitions_element.json
└── semantic_error/             # Semantic rule violations (Prefix: [SEMANTIC ERROR])
    ├── semantic_case1_dangling_transition.json
    ├── semantic_case2_undeclared_atomic_proposition.json
    ├── semantic_case3_no_outgoing_transitions.json
    ├── semantic_case4_undeclared_initial_state.json
    ├── semantic_empty_initial_states.json
    ├── semantic_empty_states.json
    ├── semantic_duplicate_atomic_propositions.json
    ├── semantic_duplicate_initial_states.json
    ├── semantic_duplicate_state_labels.json
    └── semantic_duplicate_state_transitions.json
```

---

## 2. Standardized JSON Schema (`tests/schema.json`)

Derived from `example.json` and PDF Section 1.3:

```json
{
  "atomic_propositions": ["is_lit"],
  "initial_states": ["s_off"],
  "states": {
    "s_off": {
      "labels": [],
      "transitions": ["s_on", "s_off"]
    },
    "s_on": {
      "labels": ["is_lit"],
      "transitions": ["s_off", "s_on"]
    }
  }
}
```

Key rules enforced:
- **Required keys**: `"atomic_propositions"`, `"initial_states"`, `"states"`
- **Strict keys (`additionalProperties: false`)**: Any unknown key at root or inside state objects triggers a schema error.
- **Types**: Arrays of strings for propositions, initial states, labels, and transitions. Dict/object mapping strings to state objects.

---

## 3. Test Cases Overview

### A. Valid Test Cases (`tests/valid/`)
These models must parse successfully, pass semantic verification, and execute reachability analysis with exit code `0`.
- **`01_light_switch.json`**: Reference Example 0 from PDF Section 2 (2 states, 4 transitions, 2 reachable, 0 unreachable).
- **`02_unreachable_states.json`**: PDF Additional Parser Test Case #5. Valid model containing states unreachable from initial states. Must report unreachable count > 0 in diagnostics without terminating.
- **`03_multiple_initial_states.json`**: Multiple initial states (`init_a`, `init_b`) converging into a common state.
- **`04_single_state_self_loop.json`**: Minimal valid Kripke structure (1 state with self-loop).
- **`05_dining_philosophers_sample.json`**: Sample dining philosophers model illustrating the required deadlock state self-loop convention (PDF Section 3.1 & Section 4).
- **`06_complex_branching_and_cycles.json`**: Complex state-space with branchings, cycles, and an isolated unreachable component.

### B. Syntax Error Test Cases (`tests/syntax_error/`)
Invalid JSON files that cannot be parsed by a standard JSON parser.
- **Expected exit code**: Nonzero (`!= 0`)
- **Required prefix on stderr**: `[SYNTAX ERROR]: <description>`

### C. Schema Error Test Cases (`tests/schema_error/`)
Valid JSON syntax, but violates structural requirements (missing keys, unknown keys, or invalid types).
- **Expected exit code**: Nonzero (`!= 0`)
- **Required prefix on stderr**: `[SCHEMA ERROR]: <description>`

### D. Semantic Error Test Cases (`tests/semantic_error/`)
Valid JSON and schema, but violates Kripke structure semantic rules:
- **`semantic_case1_dangling_transition.json`**: (PDF Case 1) State transitions to undeclared state.
- **`semantic_case2_undeclared_atomic_proposition.json`**: (PDF Case 2) State label references undeclared proposition.
- **`semantic_case3_no_outgoing_transitions.json`**: (PDF Case 3) Dead-end state (violates transition totality).
- **`semantic_case4_undeclared_initial_state.json`**: (PDF Case 4) Initial state references undeclared state.
- **`semantic_empty_initial_states.json`**: `initial_states` list is empty (`[]`).
- **`semantic_empty_states.json`**: `states` dictionary is empty (`{}`).
- **`semantic_duplicate_atomic_propositions.json`**: Duplicate entries in `atomic_propositions`.
- **`semantic_duplicate_initial_states.json`**: Duplicate entries in `initial_states`.
- **`semantic_duplicate_state_labels.json`**: Duplicate entries in a state's `labels`.
- **`semantic_duplicate_state_transitions.json`**: Duplicate entries in a state's `transitions`.
- **Expected exit code**: Nonzero (`!= 0`)
- **Required prefix on stderr**: `[SEMANTIC ERROR]: <description>`

---

## 4. Running the Tests

The test runner script (`test_runner.py`) uses **standard library Python only** (no extra `pip` dependencies needed).

### Validate test files against specification (standalone):
```bash
python tests/test_runner.py --validate-only -v
```

### Run against the compiled checker executable:
```bash
python tests/test_runner.py --checker ./my_checker.exe
```

### Run only a specific test category:
```bash
python tests/test_runner.py --category valid
python tests/test_runner.py --category semantic_error
```

---

## 5. Summary of Required Console Outputs

### On Success:
```text
[PARSER]: Loaded <file_path> successfully.
[METRICS]: Total declared states: <int>
[METRICS]: Total transitions found: <int>
[REACHABILITY]: Reachable states from initial node(s): <int>
[DIAGNOSTICS]: Unreachable states detected: <int>
```

### On Failure (to stderr):
- `[SYNTAX ERROR]: <description>`
- `[SCHEMA ERROR]: <description>`
- `[SEMANTIC ERROR]: <description>`
