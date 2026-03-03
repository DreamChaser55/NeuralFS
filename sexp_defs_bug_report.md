# SEXP Definitions Bug Report

**Important Note**: This is a suspected bug. It needs to be analyzed and confirmed before doing any code changes! The reported issue is strange, since the code in `sexp_definitions.py` is generated from FSO source code. Is there a bug in FSO source code or in the generating script?

## Issue Description
Several SEXP operators in `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/generated_code/sexp_definitions.py` have incorrect `return_type` values, causing false positive validation errors in the `Advanced SEXP Validator`.

## Observed Errors
When using `functional-if-then-else` or `num-valid-arguments` within numeric contexts (e.g., inside `+` or `>=`), the validator reports:
`Type Mismatch: Expected Number, Got Action/Void`

This happens because these operators are defined with `return_type: 2` (OPF_NULL / Action), whereas they should return a numeric value (OPF_NUMBER / 4) or a boolean value (OPF_BOOL / 3) depending on the context.

This bug was observed in Vega_Requiem campaign, in `mission_2_2.fsif`.

## Specific Incorrect Definitions
1.  **`functional-if-then-else`** (Line 195):
    - Current: `{"id": "OP_FUNCTIONAL_IF_THEN_ELSE", "min_args": 3, "max_args": 3, "return_type": 2}`
    - Correct: Should be `return_type: 4` (or `54` for flexible return type matching its arguments). In FSO, this operator returns the value of either its second or third argument.
2.  **`num-valid-arguments`** (Line 369):
    - Current: `{"id": "OP_NUM_VALID_ARGUMENTS", "min_args": 0, "max_args": 0, "return_type": 2}`
    - Correct: Should be `return_type: 4`. This operator returns the integer count of valid arguments.

## Impact
Mission authors cannot use these standard FSO counting and conditional logic SEXPs, as any mission containing them fails validation even if the logic is correct according to FSO specifications.

## Recommended Fix
Update `sexp_definitions.py` (or the generator script `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/generation_tools/generate_sexp_db.py`) to assign the correct return types for these operators.

---

Addendum: The bug has been fixed successfully.

### What was done:
1. Identified the root cause: The code generator (`generate_sexp_db.py`) mapped `functional-if-then-else`, `functional-when`, `functional-switch`, and `num-valid-arguments` strictly based on their basic categories in FSO source code. 
   - `functional-*` conditionals were mapped to `NULL/Void` (instead of a flexible type).
   - `num-valid-arguments` was categorized as an action and mapped to `NULL/Void` (instead of a number).
2. Modified `generate_sexp_db.py` to add specific rules bypassing the default category mapping for these irregular operators:
   - `functional-if-then-else`, `functional-when`, and `functional-switch` are now mapped to `17` (`AMBIGUOUS`), which serves as a flexible "Any" return type in the Advanced SEXP Validator. This prevents false positive type mismatch errors regardless of the context they are used in.
   - `num-valid-arguments` is now mapped explicitly to `4` (`NUMBER`), recognizing its integer return value.
3. Executed `generate_sexp_db.py` to regenerate the SEXP definitions file (`sexp_definitions.py`) with the new overrides.
4. Tested the converter on `Vega_Requiem/fsif/mission_2_2.fsif`, confirming that the Advanced SEXP Validator successfully passes the file with no errors.