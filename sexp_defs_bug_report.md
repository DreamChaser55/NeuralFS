# SEXP Definitions Bug Report

## Issue Description
Several SEXP operators in `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/generated_code/sexp_definitions.py` have incorrect `return_type` values, causing false positive validation errors in the `Advanced SEXP Validator`.

## Observed Errors
When using `functional-if-then-else` or `num-valid-arguments` within numeric contexts (e.g., inside `+` or `>=`), the validator reports:
`Type Mismatch: Expected Number, Got Action/Void`

This happens because these operators are defined with `return_type: 2` (OPF_NULL / Action), whereas they should return a numeric value (OPF_NUMBER / 4) or a boolean value (OPF_BOOL / 3) depending on the context.

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
