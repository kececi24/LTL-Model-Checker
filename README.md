# BLG 345E — Term Project Phase 1: Explicit-State LTL Model Checker

**Course:** BLG 345E — Logic and Computability  
**Phase 1:** Structural Modeling, Parsing, and Oracle Validation  

---

## 1. Project Overview

The objective of this term project is to build an **Explicit-State Linear Temporal Logic (LTL) Model Checker**. Phase 1 establishes the mathematical and structural foundation of the system:
1. **JSON Ingestion & Schema Validation:** Parse standardized system models representing Kripke structures, enforcing strict schema compliance.
2. **Custom Graph Data Structure:** Construct an explicit in-memory directed graph (nodes, atomic proposition labels, and adjacency transitions) without external graph libraries.
3. **Structural Safety & Semantic Verification:** Verify structural integrity (transition totality, dangling transition detection, undeclared atomic propositions, duplicate entry rejection, and initial state validity).
4. **Graph Reachability Exploration:** Perform Breadth-First Search (BFS) starting from initial states to classify reachable and unreachable states.
5. **Oracle Validation:** Validate models against the industry-standard model checker **NuSMV**.

---

## 2. Directory Structure

```text
├── CMakeLists.txt              # Cross-platform GCC build configuration
├── .gitignore                  # Git ignore rules for build artifacts and binaries
├── example.json                # Reference 2-state light switch model (Example 0)
├── BLG345E_Term_Project_1-4.pdf# Project Phase 1 specification
├── include/                    # Header files
│   ├── graph.hpp               # Custom ModelGraph class and BFS declaration
│   ├── parser.hpp              # State/Model declarations and JSON Schema definition
│   ├── valijson_nlohmann_bundled.hpp # JSON Schema validator (Valijson)
│   └── nlohmann/               # nlohmann/json library
│       ├── json.hpp
│       └── json_fwd.hpp
├── src/                        # Source files
│   ├── main.cpp                # CLI entry point (--parse argument handling)
│   ├── parser.cpp              # Model parsing, schema & semantic validation
│   └── graph.cpp               # Custom graph construction and BFS reachability
└── tests/                      # Automated test suite
    ├── schema.json             # Official JSON Schema (Draft-07)
    ├── tests_manifest.json     # Test cases metadata and expected outputs
    ├── test_runner.py          # Python test runner script
    ├── README.md               # Detailed test suite documentation
    ├── valid/                  # Valid Kripke structures (6 test cases)
    ├── syntax_error/           # Malformed JSON syntax tests (5 test cases)
    ├── schema_error/           # Schema violation tests (14 test cases)
    └── semantic_error/         # Semantic violation tests (10 test cases)
```

---

## 3. Standard Model JSON Schema

All system models strictly follow the standardized JSON schema:

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

- **Transition Totality:** Deadlock states must have a self-loop transition back to themselves.
- **Strict Keys:** No unexpected top-level or state-level keys are permitted (`additionalProperties: false`).

---

## 4. Building the Project

### Prerequisites
- **C++ Compiler:** GCC / G++ supporting **C++17** (e.g. MinGW-w64 on Windows, GCC 11+ on Linux)
- **Build System:** CMake (v3.15 or newer)

All build files stay inside `build/`, while the final compiled executable is automatically placed directly in the **project root directory**.

### Build on Windows (MinGW / GCC)

```powershell
# 1. Configure build directory
cmake -G "MinGW Makefiles" -B build

# 2. Compile native Windows binary (my_checker.exe in project root)
cmake --build build

# 3. (Optional) Compile 64-bit Linux ELF binary using WSL
cmake --build build --target my_checker_linux

# Or compile both Windows and Linux binaries simultaneously:
cmake --build build --target all_platforms
```

### Build on Linux

```bash
# 1. Configure build directory
cmake -B build

# 2. Compile native Linux binary (my_checker in project root)
cmake --build build
```

---

## 5. Running the Model Checker

The executable accepts the `--parse` argument followed by the path to a JSON model file:

```bash
# On Linux / Git Bash / WSL:
./my_checker --parse example.json

# On Windows PowerShell / Command Prompt:
.\my_checker.exe --parse example.json
```

### Expected Output on Success (Exit Code: 0)

```text
[PARSER]: Loaded example.json successfully.
[METRICS]: Total declared states: 2
[METRICS]: Total transitions found: 4
[REACHABILITY]: Reachable states from initial node(s): 2
[DIAGNOSTICS]: Unreachable states detected: 0
```

### Expected Output on Failure (Exit Code: Nonzero)
All validation errors print to `stderr` with strict prefixes:
- `[SYNTAX ERROR]: <description>` — Malformed JSON syntax or unreadable file.
- `[SCHEMA ERROR]: <description>` — Missing required keys, unexpected properties, or incorrect data types.
- `[SEMANTIC ERROR]: <description>` — Dangling transitions, undeclared APs, empty transitions (deadlock without self-loop), invalid initial states, duplicate declarations, or empty state space.

---

## 6. Running Tests

The test suite includes **35 automated test cases** covering valid models, syntax errors, schema violations, and semantic rules.

```powershell
# Validate all test cases against specification (pure Python, no dependencies):
python tests/test_runner.py --validate-only -v

# Run test suite against the compiled executable:
python tests/test_runner.py --checker ./my_checker.exe

# Run a specific test category (valid, syntax_error, schema_error, semantic_error):
python tests/test_runner.py --category valid
```

---

## 7. Deliverables & Required Models (WIP) 

For the final project submission, 5 pairs of model files (`.json` and `.smv`) must be placed in a `/models` folder:
1. `philosophers.json` & `philosophers.smv` (Dining Philosophers, 3 philosophers)
2. `peterson.json` & `peterson.smv` (Peterson's Mutual Exclusion, 2 processes)
3. `abp.json` & `abp.smv` (Alternating Bit Protocol)
4. `railway.json` & `railway.smv` (Railway Crossing Controller)
5. `elevator.json` & `elevator.smv` (Three-Floor Elevator Controller)
