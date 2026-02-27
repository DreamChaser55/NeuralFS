Based on the provided source code from `sexp.h`, `sexp.cpp` and `missionparse.cpp`, the parsing and validation of SEXPs (Symbolic Expressions) in FreeSpace Open is a two-stage process. First, the text is parsed into a LISP-like tree structure during mission load. Second, the logical syntax and data integrity are validated during a post-processing phase.

### 1. Data Structure: The SEXP Tree

The core of the SEXP system is defined in `sexp.h`. It utilizes a node-based architecture inspired by LISP, using a global array of nodes to represent expressions.

* **`sexp_node` Structure:** This is the fundamental unit. It mimics LISP's "CAR" and "CDR" structure using integer indices (`first` and `rest`) to point to other nodes in the global `Sexp_nodes` array.
* **`type`:** Indicates if the node is a `SEXP_LIST` (a container) or a `SEXP_ATOM` (a value or operator).
* **`subtype`:** Defines the atom content, such as `SEXP_ATOM_OPERATOR`, `SEXP_ATOM_NUMBER`, or `SEXP_ATOM_STRING`.
* **`op_index`:** If the node is an operator (e.g., `when`, `and`, `is-destroyed`), this maps to the `Operators` array.


* **Operators:** Operators are defined by the `sexp_oper` structure and an enumerated list (e.g., `OP_PLUS`, `OP_TRUE`). Each operator definition includes its minimum/maximum argument counts and argument types.

### 2. Parsing Phase (Loading)

The `missionparse.cpp` file handles reading the mission file text. It encounters SEXPs in various contexts (Events, Goals, Ship Arrival Cues) and converts the text into the node structure.

* **Extraction:** Functions like `parse_event`, `parse_goal`, and `parse_object` identify SEXP blocks starting with specific labels (e.g., `$Formula:`, `$Arrival Cue:`, `$AI Goals:`).
* **Building the Tree:** These functions call `get_sexp_main()` (referenced in `missionparse.cpp`, declared in `sexp.h`). This function reads the raw text, tokenizes it (handling parentheses), allocates nodes using `alloc_sexp`, and links them via `first` and `rest` indices.
* **Variable Parsing:** Mission variables are parsed via `parse_variables`, calling `stuff_sexp_variable_list`. This populates the `Sexp_variables` array, which SEXPs can later reference by index.

**Key SEXP Contexts in `missionparse.cpp`:**
| Context | Function | Description |
| :--- | :--- | :--- |
| **Events** | `parse_event` | Parses `#Events`. Reads the logic formula (`$Formula`) that triggers the event. |
| **Goals** | `parse_goal` | Parses `#Goals`. Reads the success/failure conditions. |
| **Ships/Wings** | `parse_object` / `parse_wing` | Parses arrival cues (`$Arrival Cue`), departure cues, and initial AI orders (`$AI Goals`). |
| **Cutscenes** | `parse_cutscenes` | Parses logic determining if a cutscene should play. |

### 3. Validation Phase (Post-Processing)

Crucially, semantic validation occurs *after* the entire mission is parsed. This is necessary because a SEXP might reference a ship or wing defined later in the mission file than the SEXP itself. This logic is found in `post_process_mission`.

* **Syntax Checking:** The function iterates through all top-level SEXP nodes and calls `check_sexp_syntax`. This checks:
1. **Argument Count:** Verifies the number of arguments matches the `min` and `max` defined for the operator in `sexp_oper`.
2. **Type Safety:** Uses `query_operator_argument_type` and `sexp_query_type_match` to ensure arguments match expected types (e.g., ensuring an argument meant to be a `OPF_SHIP` is actually a ship name).
3. **Return Types:** Verifies that nested operators return the type expected by their parent (e.g., `OP_AND` expects its children to return `OPR_BOOL`).


* **Error Handling:** If `check_sexp_syntax` returns an error code (enumerated in `sexp_error_check`), the engine attempts to generate a descriptive warning. In the editor (FRED), errors are recoverable; in the game runtime, syntax errors typically result in a warning or aborted mission load.

### 4. Specialized Validation Types

`sexp.h` defines a massive list of argument formats (`sexp_opf_t`) used during validation to ensure data integrity:

* **`OPF_SHIP` / `OPF_WING`:** Validates that the string argument corresponds to a valid ship or wing name in the mission.
* **`OPF_SUBSYSTEM`:** Checks if a subsystem exists on a specific target.
* **`OPF_BOOL` / `OPF_NUMBER`:** Standard primitive type checking.
* **`OPF_AI_GOAL`:** Ensures the argument is a valid AI order.

### Summary Flow Diagram

1. **Mission Load:** `parse_mission` starts.
2. **Tokenization:** `get_sexp_main` converts text expressions (e.g., `( when ( true ) ... )`) into `sexp_node` trees in memory.
3. **Object Linking:** Ships, wings, and variables are loaded into their respective arrays.
4. **Post-Process:** `post_process_mission` runs.
5. **Validation:** `check_sexp_syntax` walks every SEXP tree, verifying that all node references (ships, variables) are valid and types are correct.
6. **Ready:** If validation passes, the SEXPs are ready for runtime evaluation via `eval_sexp`.