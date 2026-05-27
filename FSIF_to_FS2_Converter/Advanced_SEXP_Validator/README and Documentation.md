# **FreeSpace Open Advanced SEXP Parser & Validator (Python Port)**

This project is a Python implementation of the **Symbolic Expression (SEXP)** parser and validator used in the FreeSpace Open (FSO) engine. It is designed to parse mission SEXP strings (e.g., events, arrival cues) and validate them using a comprehensive set of rules derived from the FSO C++ engine.

The validator includes auto-generated argument type logic for all 678+ SEXP operators, transpiled directly from the FSO C++ source code. It implements recursive type checking using `map_opf_to_opr` logic to bridge Argument Types (OPF) and Return Types (OPR). Return Types have been refactored into a formal `SexpReturnType` enum for improved type safety and maintainability.

The tool depends on internal NeuralFS converter components (e.g., `fs_data.py`, `fs_flags_constants.py`, and `data_models.py`). The tool is integrated as a core component of the `FSIF_to_FS2_Converter` and runs automatically during the conversion process.

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

### **Entry Point**
The function `validate_mission(mission)` in `advanced_sexp_validator.py` serves as the bridge. It:
1. Accepts a hydrated `data_models.Mission` object.
2. Builds a `MissionContext` containing all ships, wings, events, goals, and messages defined in the mission.
3. Iterates through every SEXP field in the mission (event formulas, goal formulas, ship/wing arrival/departure cues, AI goals).
4. Validates each SEXP against the context and strict FSO typing rules.
5. Reports errors via the `logger`.

## **Known Limitations and Validation Coverage**

The Advanced SEXP Validator is a strong preflight checker that catches most real-world authoring errors, but it is **not** a formal proof of FSO/FRED acceptance. The following limitations should be understood to avoid overconfidence in a clean validation pass.

### `map_opf_to_opr` string-like fallback

The core `map_opf_to_opr()` function maps each FSO Argument Type (`OPF_*`) to a Return Type (`OPR_*`) so the validator can check whether a nested operator expression produces the right kind of value for its parent's argument slot.

Only five OPF classes receive precise, structurally distinct mappings:

| OPF class | Maps to OPR |
|---|---|
| `OPF_BOOL` | `BOOL` |
| `OPF_NUMBER` | `NUMBER` |
| `OPF_POSITIVE` | `POSITIVE` |
| `OPF_NULL` | `NULL` |
| `OPF_AI_GOAL` | `AI_GOAL` |

All other OPF classes — including `OPF_SHIP`, `OPF_WING`, `OPF_MESSAGE`, `OPF_WEAPON_NAME`, `OPF_SHIP_CLASS_NAME`, `OPF_WAYPOINT_PATH`, `OPF_JUMP_NODE_NAME`, `OPF_CONTAINER_NAME`, `OPF_ANYTHING`, `OPF_FLEXIBLE_ARGUMENT`, and many more — fall through to a generic **`STRING`** return type.

**Why this is acceptable in practice:** FSO has no operators that produce a typed "Ship name" or "Message name" as a return value. In real missions, domain-specific argument slots are nearly always filled by literal quoted string atoms, not by nested operator calls. The STRING fallback therefore causes no false negatives for normal mission patterns.

**Where coverage is reduced:** If a nested operator expression is placed in a string-like argument slot (e.g., a numeric expression where a ship name is expected), the validator will only check that the expression returns *something string-like* rather than catching the specific semantic mismatch. This is an inherent limitation of the flat OPF→STRING mapping.

**Where coverage is precise:** When an argument is a **literal atom**, the validator's `_validate_atom_content()` dispatch table runs a dedicated, domain-specific validator (e.g., ship name lookup, weapon name lookup, subsystem name lookup). That path is strict and checks against the actual reference data. The coarser STRING fallback only applies to nested operator expressions in those slots.

### Argument-provider guard (focused fix for the most dangerous false negatives)

Although the STRING fallback cannot be fully eliminated without porting all of FSO's OPF/node-subtype validation logic, the most dangerous class of false negatives has been addressed by a targeted guard.

**The problem it solves:** FSO has a family of *argument-provider* operators (`any-of`, `every-of`, `random-of`, `random-multiple-of`, `number-of`, `first-of`, `in-sequence`, `for-counter`, `for-ship-class`, `for-ship-type`, `for-ship-team`, `for-ship-species`, `for-players`, `for-subsystems`, `for-container-data`, `for-map-container-keys`) whose sole purpose is to supply `<argument>` expansion values for the `when-argument` / `every-time-argument` mechanism. They carry `AMBIGUOUS` return types, which previously caused them to silently pass the coarse STRING check when nested inside ordinary ship/message/weapon/waypoint/etc. slots — even though FSO/FRED would reject such constructs.

For example, `( is-destroyed-delay 0 ( for-players ) )` previously passed validation silently. It now correctly produces an error.

**How the guard works:** The method `_validate_nested_expression_allowed_for_opf()` is called for every nested list argument. If the child's operator name is in `ARGUMENT_PROVIDER_OPERATORS` and the parent argument slot is in `DOMAIN_LITERAL_OPFS` (ship, wing, message, weapon, waypoint, event name, etc.), an error is emitted — unless the parent operator is one of the known legitimate argument-provider contexts (`when-argument`, `every-time-argument`).

**What remains out of scope:**
- Full FSO container/variable/dynamic argument parity.
- Arbitrary string-returning nested operators in domain-literal slots (only the named argument-provider set is blocked).
- FSO runtime behavior (lua scripts, scripted SEXPs).

### Summary

| Scenario | Validation coverage |
|---|---|
| Structural type errors (wrong number type in bool slot, etc.) | ✔ Full coverage via explicit OPF→OPR mappings |
| Literal atom content (ship names, weapon names, subsystems, events, etc.) | ✔ Full coverage via `_validate_atom_content()` |
| Nested operator in numeric/boolean/null slot | ✔ Full coverage (precise mappings) |
| Known argument-provider operators in domain-literal slots (ship, message, weapon, etc.) | ✔ Caught by `_validate_nested_expression_allowed_for_opf()` guard |
| Other nested operators in string-like slots (non-argument-provider, non-numeric) | ⚠ Coarse — STRING-level return type only |
| FSO container/variable/dynamic argument typing | ⚠ Partial — container and variable OPFs not fully modeled |
| FSO runtime behavior (e.g., lua scripts, scripted SEXPs) | ✗ Out of scope |

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
