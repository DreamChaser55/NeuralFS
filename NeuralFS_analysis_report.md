# NeuralFS Analysis Report

Date: 2026-05-20

## Scope

This report reviews the NeuralFS project code and documentation with emphasis on correctness, maintainability, code organization, documentation accuracy, naming, comments/docstrings, and cruft. The review covered the FSIF-to-FS2 converter, FCIF-to-FC2 converter, Fiction Viewer validator, shared utilities, data generation scripts, tests, and the main documentation set.

No code changes were made during this review. This file is the only new artifact.

## Verification Performed

- Repository inventory: reviewed 189 non-git files.
- Static syntax check: `python -m compileall -q common FCIF_to_FC2_Converter Fiction_Viewer_Validator FSIF_to_FS2_Converter` completed without Python syntax errors. It emitted a cache warning for `FSIF_to_FS2_Converter\.pytest_cache`, which is local cruft rather than source syntax failure.
- AST scan: all tracked Python files parsed successfully.
- Test execution could not be completed in this environment:
  - `python` and `py` are not on PATH.
  - The bundled runtime Python is available, but it does not include `pytest`, `PyYAML`, or `pydantic`.
  - `python -m pytest -q -p no:cacheprovider` failed because `pytest` is missing.
  - `python -m unittest discover -v` failed because `yaml` is missing.

## Executive Summary

NeuralFS is thoughtfully structured around a useful intermediate-format workflow: FSIF and FCIF are concise, AI-friendly authoring formats, and the converters perform meaningful domain validation before emitting FreeSpace Open assets. The strongest areas are the breadth of FSIF validation, the separation of validation mixins, the advanced SEXP validation integration, and the practical documentation for mission authors.

The main remaining risks fall into a few categories:
- **Refactoring and testability**: several large files have grown to the point where extracting pure functions would enable better unit testing.
- **Docstring and comment debt**: many public surfaces lack docstrings, and generated files lack provenance headers.
- **CI**: no automated CI pipeline runs tests on commit.
- **Documentation polish**: a few remaining authoring-guide and CLI doc gaps after the initial corrections round.

## Per-Area Review Notes

### Root Project Files

#### `opencode.json` and VS Code prompt files

The agent prompts are central to the project and mostly align with the documented workflow. They are long, domain-specific assets rather than executable code.

Potential maintenance issue:

- Prompt instructions duplicate many FSIF/FCIF rules from Markdown docs. That is useful for agent performance but creates drift risk. Consider generating prompt excerpts from canonical docs or adding a short "last synced with docs" marker.

### Shared Code

#### `common/validation_utils.py`

Provides reusable ASCII validation and `AsciiStr`. It is a simple, good central abstraction. It keeps repeated ASCII checks out of individual models.

Improvement:

- Add examples in the docstring for how validators should compose this with Pydantic fields.

#### `common/text_styling_utils.py`

The styling tag helper has a clear module-level docstring and a focused API. It is appropriately shared between converters and the Fiction Viewer validator.

Improvement:

- If more tag syntax is added, consider adding table-driven tests for nested/adjacent tag cases.

#### `common/utils.py`

The utility functions are small and practical. The module should get a short docstring explaining that these are converter-facing helpers rather than general project utilities.

Improvement:

- Avoid letting this file become a catch-all. If future helpers are domain-specific, keep them near the converter that owns the behavior.

#### `common/converter_gui_base.py`

The shared Tk logging and clipboard mixin is a useful extraction. `TkLogHandler` is well documented.

Potential issue:

- `LogMixin.conversion_runner()` catches all exceptions and logs them, then lets the GUI reset. That is reasonable for UX, but callers do not get a structured failure result. If future GUI flows need success/failure state beyond log color, return or store an explicit run outcome.

### Data Generation Scripts

#### `common/parsers_and_generators/parse_tables.py`

The module docstring explains the expected input tables and generated outputs. The regex approach is acceptable for a generator script but should be treated as brittle.

Improvement:

- Add function-level docstrings for major parsing helpers.
- Add a "regenerate and diff" test or documented workflow for validating generated output after parser changes.

#### `common/parsers_and_generators/extract_hardpoints.py`

Focused script with a clear purpose. It would benefit from the same root path assertion pattern as the other generators.

#### `common/parsers_and_generators/generate_weapons_compatibility.py`

Useful generator, but parser assumptions are domain-specific and should be protected with a small fixture test.

#### `common/parsers_and_generators/generate_fs_data.py`

Central generated-data builder. The generated `common/fs_data.py` is intentionally large and should remain generated.

Minor cleanup:

- Generated comments currently include repeated section numbering around section 10/11. This is harmless but noisy. **ALREADY ADDRESSED**
- Add a generated-file header to `common/fs_data.py` with the exact generator command.

### FSIF Converter

#### `FSIF_to_FS2_Converter/data_models.py`

This file is the main schema contract. It is doing a lot: input schema models, runtime models, validators, normalization helpers, and compatibility aliases.

Strengths:

- Pydantic v2 strictness and `extra='forbid'` are strong safeguards.
- Version normalization is handled explicitly.
- Many domain defaults are centralized.

Issues:

- `EnvironmentInput.suns` and `background_bitmaps` are typed as `Optional[List[Any]]`; the surrounding comment says runtime models are reused, but they are not. Loader/runtime validation may still catch bad values later, but the strict input model is looser than advertised.
- Many Pydantic model classes lack class docstrings. Since the file mixes input and runtime models, short class docstrings would make the intent much clearer.

Refactor suggestion:

- Split input schema models and runtime mission models into separate modules once the file grows again, for example:
  - `schema_models.py` for YAML-facing models.
  - `runtime_models.py` for normalized mission objects.
  - `normalizers.py` for vector/orientation/SEXP helpers.

Do this only if it reduces friction; a partial split can be worse than one large coherent file.

#### `FSIF_to_FS2_Converter/mission_loader.py`

This is one of the most important files. It applies templates, expands wings, normalizes initial orders, computes briefing cameras, and builds runtime models.

Strengths:

- The loader owns the right responsibilities: transform authoring-friendly YAML into writer-friendly structures.
- Template application and wing expansion are understandable.
- Briefing camera computation is domain-specific and belongs near mission normalization.

Issues:

- Some support for standalone ship dock alias keys appears unreachable because strict `ShipInput` forbids those extra fields before the loader can normalize them. This is likely leftover cruft. **ALREADY ADDRESSED**
- `_normalize_initial_orders()` strips semicolon comments only to detect an existing `( goals ... )` wrapper but returns the original string when already wrapped. If semicolon comments are not accepted by the target FS2 SEXP parser in that location, this may leak unsupported syntax. Confirm with FSO behavior before changing.

Refactor suggestion:

- Extract briefing camera math into a named helper class or a small pure function if more briefing logic is added.

#### `FSIF_to_FS2_Converter/fs2_writer.py`

This file emits the final FS2 sections. It is necessarily verbose because FS2 is verbose.

Strengths:

- Section writers are grouped in a sensible order.
- The writer is mostly deterministic and simple to follow.
- Complex player loadout emission has local explanatory docstrings.

Issues:

- **ALREADY ADDRESSED** `open(self.output_path, 'w')` uses the platform default encoding and newline behavior. The converter validates ASCII, but explicit `encoding='utf-8', newline='\n'` would make output deterministic across Windows and Linux. *(Fixed: `write_mission()` now opens the output file with `encoding='utf-8', newline='\n'`, ensuring byte-for-byte identical output on both Windows and Linux. Three regression tests in `FSIF_to_FS2_Converter/tests/test_fs2_writer_output_encoding.py` verify no CRLF sequences, presence of LF newlines, and valid UTF-8 encoding.)*
- Several helpers and section writers lack docstrings, especially private formatting/sanitization methods.

Refactor suggestion:

- Extract player weapon pool calculation into a pure function that returns the final pools. This would make the highest-risk writer logic much easier to test without writing a full `.fs2`.

#### `FSIF_to_FS2_Converter/fsif_to_fs2.py`

This entry point is compact and readable. The CLI options cover output, TTS provider, dry run, overwrite, API key, and voice filename mode.

Issues:

- **ALREADY ADDRESSED** Internal logic checks for CLI provider `"fsif"`, but argparse choices do not include it. The GUI uses `"fsif"` and maps it to `None`, so this is likely leftover tolerance. Either add a CLI `fsif` choice or remove the branch for clarity. *(Fixed: the ambiguous `!= 'fsif'` branch was replaced by `resolve_tts_provider()`, a named pure helper in `fsif_to_fs2.py` that encodes the full precedence — CLI/caller > FSIF file > built-in default — in one documented, tested place. GUI callers already pass `None` for "From FSIF File"; `'fsif'` as a string is no longer tolerated.)*
- **ALREADY ADDRESSED** TTS provider precedence should be documented in one place and tested. *(Fixed: `resolve_tts_provider()` is the single source of truth; its docstring specifies all four priority levels, and 27 unit tests in `FSIF_to_FS2_Converter/tests/test_tts_provider_resolution.py` cover every combination of enabled/disabled, CLI override, FSIF fallback, built-in default, case insensitivity, and return-shape invariants.)*

#### `FSIF_to_FS2_Converter/validator/core.py`

The validator class composes multiple mixins and runs validation passes in a fixed sequence.

Strengths:

- Good separation by domain: environment, ship/wing, briefing, SEXP, ASCII, and misc checks.
- Shared warning/error state is straightforward.

Improvement:

- `validate()` is a long fixed sequence of method calls. Consider a table of `(name, callable)` validation passes. That would make it easier to test ordering, log progress, and disable/enable checks in future debug modes.

#### `FSIF_to_FS2_Converter/validator/environment.py`

The environment checks cover backgrounds, nebula, asteroid fields, and related constraints. The file is logically placed.

Improvement:

- Add concise docstrings on each public `validate_*` method, especially where FSO-specific constraints are not obvious.

#### `FSIF_to_FS2_Converter/validator/ship_wing_checks.py`

This is a high-value validator area. It checks entity naming, docking, reinforcements, player setup, and weapon compatibility.

Improvement:

- The file is doing enough that a short section header comment per validation cluster would help.
- If docking and reinforcement logic grow, split them into separate mixins.

#### `FSIF_to_FS2_Converter/validator/spatial.py`

This file is large and contains collision, distance, waypoint, arrival/departure, and scale checks.

Issues:

- Duplicate effective-position resolution logic appears in more than one validation path.
- Several substantial nested helpers would be easier to test as private methods.

Refactor suggestion:

- Extract shared position resolution into one helper.
- Add docstrings to the public validation methods describing the physical/gameplay invariant being enforced.

#### `FSIF_to_FS2_Converter/validator/briefing.py`

Briefing validation is appropriately isolated. It checks map icons, display classes, teams, camera values, and debriefing conditions.

Issues:

- The validator warns on debriefing `( true )` display conditions, while the loader defaults omitted conditions to `( true )`. This is coherent as a warning policy, but the spec should be explicit.

#### `FSIF_to_FS2_Converter/validator/sexp_checks.py`

The basic SEXP check is a useful first-line screen before the advanced validator. It appears to handle escaped quotes more carefully than the advanced parser tokenizer.

Improvement:

- Keep the boundaries between "syntax sanity check" and "semantic advanced check" documented so contributors know where to add new validation.

#### `FSIF_to_FS2_Converter/validator/ascii_checks.py`

Good dedicated pass for FSO-facing text constraints.

Improvement:

- Consider sharing a little more implementation with `Fiction_Viewer_Validator` if the rules intentionally remain identical.

#### `FSIF_to_FS2_Converter/validator/misc.py`

The name `misc` is starting to hide responsibility. It currently handles a subset of checks while documentation says it validates more than it does.

Recommendation:

- Rename once responsibilities settle, or keep `misc` very small.

#### `FSIF_to_FS2_Converter/validate_sexp_scalar_styles.py`

This is a useful guardrail for authoring consistency. It protects against YAML folded/flow scalars in SEXP fields.

Improvement:

- Add a short README note near the schema explaining why block scalars matter. The authoring guide already explains the rule well.

#### `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/advanced_sexp_validator.py`

This is a sophisticated and valuable subsystem. It validates SEXP structure, return types, operator arguments, and mission-context references.

Potential issues:

- The tokenizer appears not to handle escaped quotes inside quoted strings. Basic SEXP validation has escape-aware logic, so the advanced parser may reject or mis-tokenize inputs that the simpler check allows.
- `_validate_positive()` allows zero by checking only `< 0`. Confirm whether FSO `OPF_POSITIVE` means strictly positive or non-negative. **ALREADY ADDRESSED**
- `map_opf_to_opr()` maps many argument classes to string-like return types. This may be pragmatic, but limitations should be documented to avoid overconfidence in SEXP validation coverage. **ALREADY ADDRESSED: but can this limitation be removed?**
- A TODO notes that variables are not explicitly defined in FSIF yet. This limitation should appear in the advanced validator docs.

Refactor suggestion:

- Keep generated operator code generated.
- Add tests for escaped strings, positive-number boundaries, and variable-like SEXP references.

#### `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/generated_code/*`

These files are large and generated. Do not hand-edit them. Add or improve generated-file headers with source command, source FSO code version, and generator script path.

#### `FSIF_to_FS2_Converter/tts_provider_base.py`

The base provider handles item collection and common orchestration well.

Issues:

- `TTSConfig.provider` comment says only `'google' | 'elevenlabs'`, but the project supports `inworld` and `none` in FSIF/CLI contexts.
- `get_provider()` catches provider module import errors and replaces them with generic messages. This can hide optional dependency details unless each provider uses guarded imports and explicit `is_available()`.

#### `FSIF_to_FS2_Converter/tts_google.py`

The provider handles API key lookup and Vertex fallback. Style instructions are integrated into the prompt.

Improvement:

- The model name is hardcoded. Consider making it configurable in `TTSConfig` or documenting the upgrade process when Google changes TTS model names.

#### `FSIF_to_FS2_Converter/tts_elevenlabs.py`

The optional import pattern is good. Style instructions are prepended in a provider-specific way.

Improvement:

- Add a docstring explaining the voice name to ID mapping source.

#### `FSIF_to_FS2_Converter/tts_inworld.py`

The `style` argument is accepted for interface consistency but effectively ignored by the Inworld REST request. The authoring guide notes that Inworld style support is currently not utilized, so this is documented behavior.

#### `FSIF_to_FS2_Converter/voice_manager.py`

Voice filename assignment is useful and domain-aware. Collision handling is conservative.

Potential refinement:

- Collision tracking appears global across voice output subfolders. That avoids ambiguity but may add suffixes when the same base filename would be safe in different folders. Decide whether global uniqueness is a hard project policy and document it.

#### `FSIF_to_FS2_Converter/fs_flags_constants.py`

Centralizing flag definitions is good. It reduces magic strings in writer/validator logic.

Improvement:

- Add comments identifying which flags are common author-facing flags versus engine compatibility flags.

#### `FSIF_to_FS2_Converter/briefing_icon_types.py`

Good canonical mapping source. The docs correctly point to it as the source of truth.

Improvement:

- Add a generated/static-data note if the mapping was derived from FSO sources.

#### `FSIF_to_FS2_Converter/fsif_converter_gui.py`

The GUI is practical and mostly a thin wrapper around `process_mission()`.

Issues:

- Many GUI methods lack docstrings. GUI callbacks do not need verbose docstrings, but important callbacks such as conversion start, batch processing, and TTS settings assembly should have one-line purpose comments/docstrings.

### FCIF Converter

#### `FCIF_to_FC2_Converter/fcif_to_fc2.py`

This converter is compact but dense: models, validation, formula generation, FSIF cross-checking, loadout tracking, writing, and CLI live in one file.

Strengths:

- Strict Pydantic models with `extra='forbid'`.
- Good filename validation.
- Campaign advance-condition reference validation is valuable and well tested.
- Loadout tracking across missions is a meaningful campaign-level correctness check.

Refactor suggestion:

- Split into:
  - `models.py`
  - `formula_writer.py`
  - `reference_checks.py`
  - `loadout_checks.py`
  - `cli.py`

This is not urgent, but it would make the converter easier to test as features grow.

#### `FCIF_to_FC2_Converter/fcif_converter_gui.py`

Simple and clear. Same GUI docstring cleanup applies here.

#### `FCIF_to_FC2_Converter/tests/*`

The FCIF tests cover ASCII validation, advance-condition references, loadout checks, and formula generation. This is a good foundation.

Improvement:

- Add tests that pin the intended missing-FSIF behavior for loadout checks.

### Fiction Viewer Validator

#### `Fiction_Viewer_Validator/fiction_viewer_validator.py`

This tool is small, focused, and easy to understand. It intentionally reads raw bytes so exact non-ASCII byte offsets can be reported, then decodes for text-level checks.

Strengths:

- Good rationale comments around raw-byte handling.
- Clear distinction between errors and warnings.
- Useful CLI behavior.

#### `Fiction_Viewer_Validator/README.md`

Accurate and useful. Could be expanded with a short example of a failing output and fixed text.

### Documentation

#### `Documentation/index.md`

Good navigation page. It makes the project approachable.

Improvement:

- Convert prose paths into clickable Markdown links where practical.

#### `Documentation/fsif/specification.md`

This should remain the canonical FSIF contract. It is mostly clear.

Recommendation:

- Treat this file as normative and update code/docs/prompts from it, not the other way around.
- Add a small schema changelog section at the bottom for future FSIF versions.

#### `Documentation/fsif/authoring-guide.md`

This is one of the strongest docs: it contains practical authoring guidance, common mistakes, and domain constraints.

Issues:

- Some path examples use backslashes. Prefer portable relative paths.
- It repeats many rules from the spec. That is okay for usability, but add a note that the spec is canonical.

#### `Documentation/fsif/converter/cli.md`

The CLI doc is mostly accurate and helpful.

Improvements:

- **ALREADY ADDRESSED** Document TTS provider precedence clearly. *(The "Effective TTS Provider Resolution" section in `cli.md` already lists all three priority levels explicitly. The `resolve_tts_provider()` refactor in the converter code now matches this documented order exactly.)*
- **ALREADY ADDRESSED** If CLI keeps no `fsif` provider choice, explain that omitting `--tts-provider` uses the FSIF file setting. *(The `cli.md` "Effective TTS Provider Resolution" section already states that omitting `--tts-provider` falls back to `audio.tts_provider` in the FSIF file. The `_KNOWN_PROVIDERS` constant and `resolve_tts_provider()` docstring in the converter code confirm this contract: `None` means "defer to FSIF file"; the literal string `'fsif'` is not accepted.)*

#### `Documentation/fsif/converter/implementation_details.md`

This is detailed and valuable for contributors. One remaining stale item:

- Says briefing/debriefing must include a `stages` key if present; code accepts omitted stages through defaults in several paths.

#### `Documentation/fcif/specification.md`

- The campaign-wide loadout check is described as always verifying all missions and throwing fatal errors for missing grants. It does not mention that missing/unparseable FSIF files are warning-only in the current implementation.

#### `Documentation/fcif/converter/cli.md`

Mostly accurate. It distinguishes advance-condition reference behavior well.

Mismatch:

- The campaign loadout section says each used but ungranted item aborts conversion, which is true only when the mission FSIF was actually parsed. Missing/unparseable FSIF files are skipped with warnings.

#### `Documentation/fcif/converter/implementation_details.md`

This is the most accurate FCIF implementation doc because it explicitly says the loadout check treats missing FSIF as non-fatal.

#### `FSIF_to_FS2_Converter/README.md`

Good high-level converter overview. It correctly lists Inworld TTS and FSIF 1.0 support.

Issues:

- Some rendered output in PowerShell appears mojibaked because of console encoding, but the file itself contains Unicode arrows. This is not a source bug; still, ASCII arrows would render more robustly in old Windows consoles.

#### `FCIF_to_FC2_Converter/README.md`

Good high-level overview and feature list.

Issues:

- It says a missing FSIF file is fatal for advance-condition reference validation, which is true only for missions with an advance condition. The wording could be read as broader.
- It says campaign-wide loadout check rejects missing grants, but does not mention missing/unparseable FSIF files are warning-only.

#### `common/parsers_and_generators/parsers_and_generators.md`

Useful operational doc for data regeneration.

Improvement:

- Add the expected working directory and a final verification step, for example regenerate, inspect diff, then run converter tests.
- Mention `fetch_inworld_voices.py`, since it is also in this folder and generates provider docs.

### Tests and Tooling

Strengths:

- There are many targeted tests under both converters.
- FCIF has focused tests for campaign references and loadout behavior.
- FSIF has broad integration-style tests.

Problems:

- Local `.venv` is unusable from this Windows shell, which makes contributor setup harder.

Recommendations:

1. Add CI that runs syntax and tests on Windows and Linux.
2. Keep generated output tests separate from fast unit tests if they require large docs/table fixtures.

## Comments and Docstrings

The codebase has good module-level comments in some files, but important functions/classes are inconsistent. The user-facing requirement should be:

- Each important module has a module docstring.
- Each public class has a class docstring.
- Each important public function/method has a docstring explaining purpose, high-level behavior, arguments, and return values.
- Private helper docstrings are added when the helper performs non-obvious domain logic.
- Generated files are exempt, but should have generated-file headers.

High-priority docstring gaps:

- `FSIF_to_FS2_Converter/data_models.py`: most model classes need concise purpose docstrings, especially to distinguish input models from normalized runtime models.
- `FSIF_to_FS2_Converter/fs2_writer.py`: the writer class and section writers need consistent docstrings.
- `FSIF_to_FS2_Converter/validator/*.py`: public validation methods should describe the invariant they check.
- `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/advanced_sexp_validator.py`: key parser/type-checker helpers need docstrings.
- `FCIF_to_FC2_Converter/fcif_to_fc2.py`: Pydantic model classes and major check functions need complete docstrings.
- GUI files: important callbacks should have short docstrings.

Comment cleanup:

- Avoid comments that restate a direct assignment; keep comments for FreeSpace/FSO domain intent and tricky transformations.

## Naming Review

Most domain names are clear and match FSIF/FCIF concepts. Suggested improvements:

- Rename `misc.py` or keep it small; "misc" is no longer descriptive enough if it owns important validation.
- Consider renaming `flow` local variables to `mission_flow_raw` where both raw and normalized mission flow exist.
- Consider renaming `t_props` to `template_props` in `mission_loader.py`.
- Consider renaming `props` to `ship_props` / `wing_props` in loader methods for readability.
- In FCIF, split helper names around "reference checks" and "loadout checks" if the file is modularized.
- In TTS, clarify whether `provider='none'` belongs in `TTSConfig` or only in CLI/FSIF settings. A disabled provider is not exactly a provider.

## Cruft and Bloat

Potential cruft:

- Possible unreachable alias-handling code in `mission_loader.py` due to strict Pydantic `extra='forbid'`.

Potential bloat:

- `FSIF_to_FS2_Converter/data_models.py`, `fs2_writer.py`, `mission_loader.py`, and `validator/spatial.py` are large. This is not automatically bad; they are domain-heavy. Split only where it creates clearer tests and ownership.
- `Advanced_SEXP_Validator/generated_code/sexp_argument_logic.py` is large because it is generated. Do not refactor manually.
- The prompt files duplicate docs heavily. This is useful for agent performance but should be maintained deliberately.

## Suggested Improvement Roadmap

### Phase 1: Tooling and Testability

1. Add CI that runs syntax and tests on Windows and Linux.
2. Extract pure functions for player weapon pool calculation and shared spatial position resolution.
3. Add generator smoke tests or regenerate-and-diff docs.

### Phase 2: Docstrings and Organization

1. Add class/function docstrings to important public surfaces.
2. Add generated-file headers.
3. Split large files only after tests cover the behavior being moved.
4. Tighten comments to explain intent rather than restating code.

## Appendix: Important Files Reviewed

Root and configuration:

- `.gitignore`
- `.vscode/settings.json`
- `README.md`
- `opencode.json`

Shared code:

- `common/utils.py`
- `common/validation_utils.py`
- `common/text_styling_utils.py`
- `common/converter_gui_base.py`
- `common/fs_data.py`
- `common/weapons_compatibility_data.py`
- `common/parsers_and_generators/parsers_and_generators.md`
- `common/parsers_and_generators/parse_tables.py`
- `common/parsers_and_generators/extract_hardpoints.py`
- `common/parsers_and_generators/generate_weapons_compatibility.py`
- `common/parsers_and_generators/generate_fs_data.py`
- `common/parsers_and_generators/fetch_inworld_voices.py`

FSIF converter:

- `FSIF_to_FS2_Converter/README.md`
- `FSIF_to_FS2_Converter/setup.py`
- `FSIF_to_FS2_Converter/data_models.py`
- `FSIF_to_FS2_Converter/mission_loader.py`
- `FSIF_to_FS2_Converter/fs2_writer.py`
- `FSIF_to_FS2_Converter/fsif_to_fs2.py`
- `FSIF_to_FS2_Converter/fsif_converter_gui.py`
- `FSIF_to_FS2_Converter/fs_flags_constants.py`
- `FSIF_to_FS2_Converter/briefing_icon_types.py`
- `FSIF_to_FS2_Converter/voice_manager.py`
- `FSIF_to_FS2_Converter/tts_provider_base.py`
- `FSIF_to_FS2_Converter/tts_google.py`
- `FSIF_to_FS2_Converter/tts_elevenlabs.py`
- `FSIF_to_FS2_Converter/tts_inworld.py`
- `FSIF_to_FS2_Converter/validate_sexp_scalar_styles.py`
- `FSIF_to_FS2_Converter/validator/core.py`
- `FSIF_to_FS2_Converter/validator/environment.py`
- `FSIF_to_FS2_Converter/validator/misc.py`
- `FSIF_to_FS2_Converter/validator/sexp_checks.py`
- `FSIF_to_FS2_Converter/validator/ship_wing_checks.py`
- `FSIF_to_FS2_Converter/validator/ascii_checks.py`
- `FSIF_to_FS2_Converter/validator/briefing.py`
- `FSIF_to_FS2_Converter/validator/spatial.py`
- `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/advanced_sexp_validator.py`
- `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/generation_tools/*.py`
- `FSIF_to_FS2_Converter/Advanced_SEXP_Validator/generated_code/*.py`
- FSIF converter test files, with special attention to integration and validation tests.

FCIF converter:

- `FCIF_to_FC2_Converter/README.md`
- `FCIF_to_FC2_Converter/fcif_to_fc2.py`
- `FCIF_to_FC2_Converter/fcif_converter_gui.py`
- `FCIF_to_FC2_Converter/tests/*.py`

Fiction Viewer validator:

- `Fiction_Viewer_Validator/README.md`
- `Fiction_Viewer_Validator/fiction_viewer_validator.py`

Documentation:

- `Documentation/index.md`
- `Documentation/fsif/specification.md`
- `Documentation/fsif/authoring-guide.md`
- `Documentation/fsif/migration-guide.md`
- `Documentation/fsif/converter/cli.md`
- `Documentation/fsif/converter/implementation_details.md`
- `Documentation/fsif/converter/additional_flags.md`
- `Documentation/fcif/specification.md`
- `Documentation/fcif/converter/cli.md`
- `Documentation/fcif/converter/implementation_details.md`
- `Documentation/FSO and fs2 format/FSO_Tokens_Reference.md`
- Selected TTS voice documentation and generated FSO/token reference files as needed for validation drift checks.
