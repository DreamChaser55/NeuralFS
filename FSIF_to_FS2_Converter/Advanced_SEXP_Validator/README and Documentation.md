# **FreeSpace Open Advanced SEXP Parser & Validator (Python Port)**

This project is a Python implementation of the **Symbolic Expression (SEXP)** parser and validator used in the FreeSpace Open (FSO) engine. It is designed to parse mission SEXP strings (e.g., events, arrival cues) and validate them against a strict set of rules, exactly mimicking the behavior of the FSO C++ engine.

The validator includes auto-generated argument type logic for all 678+ SEXP operators, transpiled directly from the FSO C++ source code. It implements full recursive type checking using `map_opf_to_opr` logic to bridge Argument Types (OPF) and Return Types (OPR). Return Types have been refactored into a formal `SexpReturnType` enum for improved type safety and maintainability.

## **Quick Start**

Main executable file: `advanced_sexp_validator.py`.

### **Prerequisites**

* Python 3.9 or higher.
* The tool depends on internal NeuralFS converter components (e.g., `fs_data.py`, `fs_flags_constants.py`, and `data_models.py`).

### **Running the Tool**

The tool is integrated as a core component of the `FSIF_to_FS2_Converter` and runs automatically during the conversion process.

### **Example Usage in Code**

```python
from advanced_sexp_validator import SexpParser, SexpValidator, MissionContext, OperatorDef, SexpReturnType
```

1. Set up context (mocking a mission)
```python
ctx = MissionContext()
ctx.ships.add("Alpha 1")
ctx.variables["hull_strength"] = SexpReturnType.NUMBER  # Use Enum for variable types
```

2. Parse a string
```python
parser = SexpParser()
raw_sexp = '(when (has-arrived-delay 0 "Alpha 1") (do-nothing))'
roots = parser.parse(raw_sexp)
```

3. Validate
```python
validator = SexpValidator(ctx)
# We treat the root as an Event Formula (which expects an Action/NULL return).
# For a boolean expression (like an arrival cue), use expected_type=SexpReturnType.BOOL.
errors = validator.validate(roots[0], expected_type=SexpReturnType.NULL)

if errors:
    print("Errors found:", errors)
else:
    print("SEXP is valid!")
```

## **Architecture & Documentation**

This tool mirrors the specific architecture of the FreeSpace Open C++ source code. The relevant FSO source files are included in the `/FSO code excerpts/` folder:
1. `missionparse.cpp`
2. `sexp.h`
3. Because `sexp.cpp` is a very large file, only selected excerpts needed for this tool's development are provided in `sexpdotcpp_excerpts.txt`.

There is also `FSO SEXP validation logic.md`, which contains the analysis of FSO SEXP parsing and validation logic.

**Note for AI agents:** `missionparse.cpp` and `sexpdotcpp_excerpts.txt` are large files that could fill a large fraction of your context window. Only read them if you truly need to in order to accomplish your task.

### **Project File Structure**

- `advanced_sexp_validator.py`: Main validator — parser, knowledge base, and recursive validation logic.
- `/tests/test_advanced_sexp_validator.py`: Unit tests for the validator.

#### **Generator Scripts**
Located in the `/generation_tools/` subfolder.
- `generate_sexp_db.py`: Generator script for `sexp_definitions.py`.
- `generate_opf_constants.py`: Generator script for `opf_definitions.py`.
- `generate_argument_logic.py`: C++-to-Python transpiler for argument type logic (generates `sexp_argument_logic.py`).

#### **Generated Files**
Located in the `/generated_code/` subfolder. **Do not edit manually.** Edit the generating scripts in `/generation_tools/` instead.
- `sexp_definitions.py`: Auto-generated operator definitions (678+ operators).
- `opf_definitions.py`: Auto-generated OPF type constants.
- `sexp_argument_logic.py`: Auto-generated argument type logic (transpiled from C++).

### **1. Data Structures (SexpNode)**

* **Concept:** The parser does not build an Abstract Syntax Tree (AST) of specific classes (like `WhenNode` or `AddNode`). Instead, it builds a generic tree of `SexpNode` objects.
* **Structure:**
  * `text`: The raw string value (e.g., `"when"`, `"100"`, `"Alpha 1"`).
  * `is_list`: Boolean flag. If `True`, this node is a container (operator); if `False`, it is an atom (argument).
  * `children`: A list of child nodes.
* **FSO Equivalent:** Mirrors the `sexp_node` struct in C++, which uses `first` and `rest` indices to form a linked list in a global array.

### **2. The Knowledge Base (OperatorDef)**

* **Concept:** The parser is data-driven. It does not "know" what `when` means in code; it looks up `when` in a database to find its rules.
* **Structure:**
  * `min_args` / `max_args`: Limits on argument counts.
  * `return_type`: What this operator resolves to (Boolean, Number, Action, etc.).
* **FSO Equivalent:** Mirrors the `Operators[]` array in `sexp.cpp`.

### **3. The Parser (SexpParser)**

* **Strategy:** Recursive descent.
* **Logic:**
  1. **Tokenization:** Splits the string by spaces, parentheses, and quotes. Handles comments (`;`).
  2. **Tree Building:** Iterates through tokens. When it encounters `(`, it creates a new list node and recurses. When it encounters `)`, it returns.
* **FSO Equivalent:** Mirrors `get_sexp_main` in `missionparse.cpp`.

### **4. The Validator (SexpValidator)**

* **Strategy:** Recursive type checking.
* **Type Logic:** The system uses `map_opf_to_opr` to map the expected Argument Type (`OPF_*`) to the required Return Type (`OPR_*`).
* **Pass 1 (Top-Down):** The parent operator determines the expected `OPF` type for each argument (using `query_operator_argument_type` from `sexp_argument_logic.py`).
* **Pass 2 (Validation):**
    * **Operators:** Checked to ensure their `return_type` matches the expected `OPR` type.
    * **Atoms:** Checked to ensure their content matches the specific constraints of the `OPF` type (e.g., `OPF_SHIP` must be a valid ship name, `OPF_BOOL` must be `"true"`/`"false"` or a number).
* **FSO Equivalent:** Mirrors `check_sexp_syntax`, `query_operator_argument_type`, and `sexp_query_type_match`.

## **Integration with FSIF Converter**

This validator is integrated with the main `FSIF_to_FS2_Converter` as a core validation step.

### **Entry Point**
The function `validate_mission(mission)` in `advanced_sexp_validator.py` serves as the bridge. It:
1. Accepts a hydrated `data_models.Mission` object.
2. Builds a `MissionContext` containing all ships, wings, events, goals, and messages defined in the mission.
3. Iterates through every SEXP field in the mission (event formulas, goal formulas, ship/wing arrival/departure cues, AI goals).
4. Validates each SEXP against the context and strict FSO typing rules.
5. Reports errors via the `logger`.

### **Usage**
The validator runs automatically as part of the FSIF to FS2 conversion process.

## **Extending the System**

### **Regenerating from Updated FSO Source**

The validator's knowledge base is auto-generated from FSO C++ source code. To update it when FSO adds new operators:

1. **Update `sexpdotcpp_excerpts.txt`** with the latest FSO source excerpts.

2. **Regenerate Operator Definitions:**
   ```bash
   python generate_sexp_db.py
   ```
   This updates `sexp_definitions.py` with operator metadata (name, min/max args, return type).

3. **Regenerate Argument Type Logic:**
   ```bash
   python generate_argument_logic.py
   ```
   This transpiles the `query_operator_argument_type` C++ function to Python, updating `sexp_argument_logic.py`.

4. **Regenerate OPF Constants (if needed):**
   ```bash
   python generate_opf_constants.py
   ```
   This updates `opf_definitions.py` with any new OPF type constants.
