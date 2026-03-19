# **Freespace Open Advanced SEXP Parser & Validator (Python Port)**

**Current version: 0.6**

This project is a Python implementation of the **Symbolic Expression (SEXP)** parser and validator used in the Freespace Open (FSO) engine. It is designed to parse mission SEXP strings (e.g., events, arrival cues) and validate them against a strict set of rules, exactly mimicking the behavior of the FSO C++ engine.

The validator includes auto-generated argument type logic for all 678+ SEXP operators, transpiled directly from the FSO C++ source code. It implements full recursive type checking using `map_opf_to_opr` logic to bridge Argument Types (OPF) and Return Types (OPR). Recent updates have refactored Return Types into a formal `SexpReturnType` Enum for improved type safety and maintainability.

## **Quick Start**

Main executable file: advanced_sexp_validator.py.

### **Prerequisites**

* Python 3.6 or higher.  
* No external dependencies are required.

### **Running the Tool**

To see the parser in action, simply run the script. It includes a test harness with several examples (both valid and invalid) to demonstrate the validation logic.  
`python advanced_sexp_validator.py`

### **Example Usage in Code**

```python
from advanced_sexp_validator import SexpParser, SexpValidator, MissionContext, OperatorDef, SexpReturnType, OPR_NULL
```

1. Setup Context (Mocking a Mission)  
```python
ctx = MissionContext()  
ctx.ships.add("Alpha 1")  
ctx.variables["hull_strength"] = SexpReturnType.NUMBER  # Use Enum for variable types
```

2. Parse a String  
```python
parser = SexpParser()  
raw_sexp = '(when (has-arrived-delay 0 "Alpha 1") (do-nothing))'  
roots = parser.parse(raw_sexp)
```

3. Validate  
```python
validator = SexpValidator(ctx)  
# We treat the root as an Event Formula (which expects an Action/NULL return)  
# For a boolean expression (like an arrival cue), use expected_type=SexpReturnType.BOOL
errors = validator.validate(roots[0], expected_type=SexpReturnType.NULL)

if errors:  
    print("Errors found:", errors)  
else:  
    print("SEXP is valid!")
```

## **Architecture & Documentation**

This tool mirrors the specific architecture of the Freespace Open C++ source code. The relevant FSO source code files are included in the '/FSO code excerpts/' folder:
1. missionparse.cpp
2. sexp.h
3. since sexp.cpp is a very large file, only selected excerpts needed for the development of this tool are provided in sexpdotcpp_excerpts.txt

There is also the 'FSO SEXP validation logic.md', containing the analysis of the FSO SEXP parsing and validation logic.

Note for AI agents: `missionparse.cpp` and `sexpdotcpp_excerpts.txt` are large files that could fill a large fraction of your context window if you read them. Only read them if you really need it to accomplish your tasks.

### **Project File Structure**

- `advanced_sexp_validator.py`: Main validator with parser, knowledge base, and recursive validation logic.
- `/tests/test_advanced_sexp_validator.py`: Unit tests for the validator.

#### **Generator Scripts**
Located in the `/generation_tools/` subfolder.
- `generate_sexp_db.py`: Generator script for `sexp_definitions.py`.
- `generate_opf_constants.py`: Generator script for `opf_definitions.py`.
- `generate_argument_logic.py`: C++ to Python transpiler for argument type logic (generates `sexp_argument_logic.py`).

#### **Generated Files**
Located in the `/generated_code/` subfolder. **Do not edit manually.** Edit the generating scripts (in the `/generation_tools/` folder) instead.
- `sexp_definitions.py`: Auto-generated operator definitions (678+ operators).
- `opf_definitions.py`: Auto-generated OPF type constants.
- `sexp_argument_logic.py`: Auto-generated argument type logic (transpiled from C++).

### **1. Data Structures (SexpNode)**

* **Concept:** The parser does not build an Abstract Syntax Tree (AST) of specific classes (like WhenNode or AddNode). Instead, it builds a generic tree of SexpNode objects.  
* **Structure:**  
  * text: The raw string value (e.g., "when", "100", "Alpha 1").  
  * is_list: Boolean flag. If True, this node is a container (operator); if False, it is an atom (argument).  
  * children: A list of child nodes.  
* **FSO Equivalent:** This mirrors the sexp_node struct in C++, which uses first and rest indices to form a linked list in a global array.

### **2. The Knowledge Base (OperatorDef)**

* **Concept:** The parser is data-driven. It doesn't "know" what when means in code; it looks up when in a database to find its rules.  
* **Structure:**  
  * min_args / max_args: Limits on argument counts.  
  * return_type: What this operator resolves to (Boolean, Number, Action, etc.).  
* **FSO Equivalent:** Mirrors the Operators[] array in sexp.cpp.

### **3. The Parser (SexpParser)**

* **Strategy:** Recursive Descent.  
* **Logic:**  
  1. **Tokenization:** Splits the string by spaces, parentheses, and quotes. Handles comments (;).  
  2. **Tree Building:** Iterates through tokens. When it finds (, it creates a new list node and recurses. When it finds ), it returns.  
* **FSO Equivalent:** Mirrors get_sexp_main in missionparse.cpp.

### **4. The Validator (SexpValidator)**

* **Strategy:** Recursive Type Checking.  
* **Type Logic:** The system uses `map_opf_to_opr` to map the expected Argument Type (`OPF_*`) to the required Return Type (`OPR_*`).
* **Pass 1 (Top-Down):** The parent operator determines the expected `OPF` type for each argument (using `query_operator_argument_type` from `sexp_argument_logic.py`).
* **Pass 2 (Validation):**
    *   **Operators:** Checked to ensure their `return_type` matches the expected `OPR` type.
    *   **Atoms:** Checked to ensure their content matches the specific constraints of the `OPF` type (e.g., `OPF_SHIP` must be a valid ship name, `OPF_BOOL` must be "true"/"false" or a number).
* **FSO Equivalent:** Mirrors check_sexp_syntax, query_operator_argument_type, and sexp_query_type_match.

## **Status Update**

| Task | Status |
|------|--------|
| Auto-Generate Operator Database | ✅ Complete (v0.2) |
| Port Argument Logic | ✅ Complete (v0.3) |
| Fix Type Matching | ✅ Complete (v0.4) |
| Integrate with Converter | ✅ Complete (v0.5) |
| Implement Atom Validators | ✅ Complete (v0.6) |

**Next Steps:**
- Support more complex variable types.

## **Integration with FSIF Converter**

As of v0.7, this validator is integrated with the main `FSIF_to_FS2_Converter` as a core validation step.

### **Entry Point**
The function `validate_mission(mission, log_func)` in `advanced_sexp_validator.py` serves as the bridge. It:
1.  Accepts a hydrated `data_models.Mission` object.
2.  Builds a `MissionContext` containing all ships, wings, events, goals, and messages defined in the mission.
3.  Iterates through every SEXP field in the mission (Event formulas, Goal formulas, Ship/Wing Arrival/Departure cues, AI Goals).
4.  Validates each SEXP against the context and strict FSO typing rules.
5.  Reports errors via the provided `log_func`.

### **Usage**
The validator runs automatically as part of the FSIF to FS2 conversion process.

You can also run the validator standalone for testing:
```bash
python advanced_sexp_validator.py
```
*(Note: Running standalone triggers a built-in test suite for core functionality.)*

## **Extending the System**

### **Regenerating from Updated FSO Source**

The validator's knowledge base is auto-generated from FSO C++ source code. To update when FSO adds new operators:

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
