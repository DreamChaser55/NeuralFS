import re

class SexpChecksMixin:
    def validate_sexps(self):
        """
        Perform structural validation of all SEXP formulas in the mission.

        Checks:
        - Event formulas, goal formulas, ship/wing arrival_condition and
          departure_condition fields, and initial_orders.
        - Parenthesis balance.
        - YAML comment leakage.
        - Token length limits.
        - Basic operator validity (outermost operator only).

        Note: Deep semantic analysis of nested operators, argument types, and
        entity references is delegated to the Advanced SEXP Validator.
        """
        # Gather all SEXP strings with context
        sexps = []
        
        # Events
        for e in self.mission.events:
            if e.formula: sexps.append((f"Event '{e.name}' formula", e.formula))
            
        # Goals
        for g in self.mission.goals:
            if g.formula: sexps.append((f"Goal '{g.name}' formula", g.formula))
            
        # Ships/Wings conditions and initial_orders
        for s in self.mission.ships:
            if s.arrival_condition: sexps.append((f"Ship '{s.name}' arrival_condition", s.arrival_condition))
            if s.departure_condition: sexps.append((f"Ship '{s.name}' departure_condition", s.departure_condition))
            if s.initial_orders: sexps.append((f"Ship '{s.name}' initial_orders", s.initial_orders))
            
        for w in self.mission.wings:
            if w.arrival_condition: sexps.append((f"Wing '{w.name}' arrival_condition", w.arrival_condition))
            if w.departure_condition: sexps.append((f"Wing '{w.name}' departure_condition", w.departure_condition))
            if w.initial_orders: sexps.append((f"Wing '{w.name}' initial_orders", w.initial_orders))
            
        for ctx, sexp in sexps:
            self._check_sexp_string(ctx, sexp)

    def _check_sexp_string(self, context, sexp):
        """
        Helper method to perform basic structural checks on a single SEXP string.
        """
        if not sexp: return
        
        # 1. Parens
        open_p = sexp.count('(')
        close_p = sexp.count(')')
        if open_p != close_p:
            self.log_error(f"SEXP error: {context}: Mismatched parentheses (Open: {open_p}, Close: {close_p})")
            
        # Regex to strip string literals, respecting escaped quotes/backslashes
        clean = re.sub(r'"(\\.|[^"\\])*"', '""', sexp)

        # 2. YAML Comments (# space)
        if re.search(r'#\s', clean):
             self.log_error(f"SEXP error: {context}: Likely YAML comment leakage ('# ' found).")
             
        # 3. Token Length & Operator Validity
        # Parse first token (Outermost Operator)
        match = re.search(r'\(\s*([^\s)]+)', clean)
        if match:
             operator = match.group(1)
             if self.allowed_sexp_operators and operator not in self.allowed_sexp_operators:
                  try:
                      float(operator)
                  except ValueError:
                      if operator not in ('true', 'false'):
                           self.log_error(f"SEXP error: {context}: Unknown operator '{operator}'.")

        # Split by delimiters (parens, whitespace) for length check
        tokens = re.split(r'[\s()]+', clean)
        for t in tokens:
            if not t: continue
            if len(t) >= 30:
                self.log_error(f"SEXP error: {context}: Token '{t[:15]}...' length {len(t)} exceeds limit (<30).")

    def validate_directive_text_sexp_compatibility(self):
        """
        Warn if events with hud_directive_text use is-event-true-delay, is-event-false-delay,
        or similar event/goal-referencing SEXPs in their formula.

        The FSO engine cannot initially evaluate the possibility of an event becoming
        true/false when its formula references other events or goals via these operators.
        As a result, the grey 'pending' directive is never displayed on the HUD.

        Events with hud_directive_text should use simple, directly-evaluable conditions
        (e.g., is-destroyed-delay, has-arrived-delay, percent-ships-destroyed).
        """
        DIRECTIVE_INCOMPATIBLE_SEXPS = [
            "is-event-true-delay",
            "is-event-false-delay",
            "is-event-true-msecs-delay",
            "is-event-false-msecs-delay",
            "is-goal-true-delay",
            "is-goal-false-delay",
        ]

        for i, event in enumerate(self.mission.events):
            if not event.hud_directive_text or not event.formula:
                continue

            # Strip quoted string literals to avoid false positives from event/goal
            # name arguments that happen to contain an operator name as a substring.
            formula_clean = re.sub(r'"(\\.|[^"\\])*"', '""', event.formula)

            found_ops = [op for op in DIRECTIVE_INCOMPATIBLE_SEXPS if op in formula_clean]

            if found_ops:
                event_name = event.name if event.name else f"(unnamed, index {i})"
                ops_str = ", ".join(f"'{op}'" for op in found_ops)
                self.log_warning(
                    f"Event '{event_name}' has hud_directive_text but its formula uses "
                    f"{ops_str}. HUD directive text does not work correctly when the formula "
                    f"references other events or goals via these SEXPs: the engine cannot "
                    f"initially determine whether the event could become true or false, so "
                    f"the grey directive will never be displayed on the HUD. "
                    f"Use simpler, directly-evaluable conditions (e.g., is-destroyed-delay, "
                    f"has-arrived-delay, percent-ships-destroyed) in events with hud_directive_text."
                )