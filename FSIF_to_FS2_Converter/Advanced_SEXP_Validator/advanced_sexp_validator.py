import re
import sys
from enum import IntEnum
from pathlib import Path
from typing import List, Set, Dict, Any, Optional, Union

# Try relative imports (Package Mode)
try:
    from common import fs_data
    from .. import fs_flags_constants
    from .generated_code.sexp_definitions import SEXP_DEFINITIONS, INT_MAX
    from .generated_code.opf_definitions import *
    from .generated_code.sexp_argument_logic import get_argument_type
except (ImportError, ValueError):
    # Fallback for standalone execution (Script Mode)
    # This allows running the script directly without -m package.module syntax
    _current_dir = Path(__file__).resolve().parent
    
    # Add Advanced_SEXP_Validator to path for local imports
    if str(_current_dir) not in sys.path:
        sys.path.append(str(_current_dir))
        
    # Add parent to path for fs_data
    _parent_dir = _current_dir.parent
    if str(_parent_dir) not in sys.path:
        sys.path.append(str(_parent_dir))
        
    _root_dir = _parent_dir.parent
    if str(_root_dir) not in sys.path:
        sys.path.append(str(_root_dir))

    from common import fs_data
    import fs_flags_constants
    from generated_code.sexp_definitions import SEXP_DEFINITIONS, INT_MAX
    from generated_code.opf_definitions import *
    from generated_code.sexp_argument_logic import get_argument_type

# =============================================================================
# HELPER DATA (Derived from fs_data)
# =============================================================================

def is_fighter_bomber(ship_class: str) -> bool:
    """
    Determine if a ship class is a Fighter or Bomber.
    First checks weapons_compatibility_data (which is extracted exactly from ship flags).
    Falls back to a prefix heuristic.
    """
    if not ship_class:
        return False
        
    try:
        from weapons_compatibility_data import WEAPON_COMPATIBILITY
        if ship_class in WEAPON_COMPATIBILITY:
            return True
    except ImportError:
        pass
        
    sc = ship_class.upper()
    return any(sc.startswith(p) for p in ["GTF", "GTB", "PVF", "PVB", "SF", "SB", "GVF", "GVB"])

# OPF types that resolve to a Ship or Wing name, used for subsystem context
SHIP_TYPE_OPFS = {
    OPF_SHIP,
    OPF_WING,
    OPF_SHIP_WING,
    OPF_SHIP_WING_WHOLETEAM,
    OPF_SHIP_WING_SHIPONTEAM_POINT,
    OPF_SHIP_WING_POINT,
    OPF_SHIP_WING_POINT_OR_NONE,
    OPF_SHIP_OR_NONE,
    OPF_SHIP_WITH_BAY,
    OPF_SHIP_NOT_PLAYER
}

# AI Operators restricted to Fighters and Bombers
FIGHTER_BOMBER_ONLY_OPERATORS = {
    "ai-guard",
    "ai-guard-wing",
    "ai-destroy-subsystem",
    "ai-destroy-subsys",
    "ai-disable-ship",
    "ai-disarm-ship",
    "ai-disable-ship-tactical",
    "ai-disarm-ship-tactical",
    "ai-evade-ship",
    "ai-ignore",
    "ai-ignore-new",
    "ai-fly-to-ship",
    "ai-chase-any",
    "ai-chase-ship-class",
    "ai-chase-ship-type",
    "ai-chase-wing",
    "ai-form-on-wing"
}

# Logical AI categories for IFF checks
GUARD_OPERATORS = {
    "ai-guard",
    "ai-guard-wing"
}

ATTACK_OPERATORS = {
    "ai-chase",
    "ai-chase-wing",
    "ai-disable-ship",
    "ai-disarm-ship",
    "ai-destroy-subsystem",
    "ai-destroy-subsys",
    "ai-disable-ship-tactical",
    "ai-disarm-ship-tactical"
}

# Construct a set of all known subsystem names (from all ships) for validation
# This allows checking if a subsystem name is at least valid for *some* ship,
# even if we can't determine the specific ship context.
ALL_KNOWN_SUBSYSTEMS = set()
for s_set in fs_data.ALLOWED_SUBSYSTEMS.values():
    ALL_KNOWN_SUBSYSTEMS.update(s_set)
ALL_KNOWN_SUBSYSTEMS.add("pilot") # Virtual subsystem always available
ALL_KNOWN_SUBSYSTEMS.add("hull") # Special target
ALL_KNOWN_SUBSYSTEMS.add("shields") # Special target

# Construct a set of all known dockpoints
ALL_KNOWN_DOCKPOINTS = set()
for d_set in fs_data.ALLOWED_DOCKPOINTS.values():
    ALL_KNOWN_DOCKPOINTS.update(d_set)

# =============================================================================
# CONSTANTS & ENUMS
# =============================================================================

# Return Types (What an operator produces) - From sexp.h/sexp_opr_t
class SexpReturnType(IntEnum):
    NONE = 0
    NUMBER = 4
    BOOL = 3
    NULL = 2  # Returns nothing (Action)
    AI_GOAL = 11
    POSITIVE = 14
    STRING = 12
    AMBIGUOUS = 17
    FLEXIBLE_ARGUMENT = 18 # Goober5000



# =============================================================================
# DATA STRUCTURES
# =============================================================================

class SexpNode:
    """
    Represents a node in the Symbolic Expression (SEXP) tree.
    Mirrors the 'sexp_node' structure from FreeSpace Open's C++ engine.
    """
    def __init__(self, text: str = "", is_list: bool = False):
        """
        Initialize a SEXP node.
        :param text: The raw string content of the node (e.g., operator name or atom value).
        :param is_list: True if this node is a container for a list of children (an operator call).
        """
        self.text = text          # The raw string (e.g., "when", "Alpha 1", "100")
        self.is_list = is_list    # True if this node wraps a list of children
        self.children: List['SexpNode'] = [] # List of child nodes
        self.parent: Optional['SexpNode'] = None # Reference to parent for traversal

    def add_child(self, node: 'SexpNode'):
        """
        Adds a child node to this container node.
        :param node: The child SexpNode to add.
        """
        node.parent = self
        self.children.append(node)

    def __repr__(self) -> str:
        if self.is_list:
            children_str = " ".join([str(c) for c in self.children])
            return f"({self.text} {children_str})" if children_str else f"({self.text})"
        return self.text

class OperatorDef:
    """
    Metadata definition for a SEXP operator.
    Mirrors the 'sexp_oper' structure from FreeSpace Open's C++ engine.
    """
    def __init__(self, op_id: str, text: str, min_args: int, max_args: int, return_type: int):
        """
        Initialize an operator definition.
        :param op_id: The internal FSO operator ID constant (e.g., 'OP_WHEN').
        :param text: The string literal used in mission files (e.g., 'when').
        :param min_args: Minimum number of arguments required.
        :param max_args: Maximum number of arguments allowed.
        :param return_type: The return type of this operator (OPR_* constants).
        """
        self.id = op_id
        self.text = text
        self.min_args = min_args
        self.max_args = max_args
        self.return_type = return_type

class MissionContext:
    """
    Stores mission-specific entity names for reference validation.
    Enables checking if a ship, wing, event, or waypoint mentioned in a SEXP actually exists.
    """
    def __init__(self):
        """Initialize an empty mission context."""
        self.ships: Set[str] = set()
        self.wings: Set[str] = set()
        self.ship_to_class: Dict[str, str] = {} # ship name -> class name
        self.wing_to_template_class: Dict[str, str] = {} # wing name -> template class name
        self.ship_to_team: Dict[str, str] = {} # ship name -> team name
        self.wing_to_team: Dict[str, str] = {} # wing name -> team name
        self.variables: Dict[str, int] = {}
        self.events: Set[str] = set()
        self.goals: Set[str] = set()
        self.messages: Set[str] = set()
        self.waypoints: Dict[str, int] = {}
        self.jump_nodes: Set[str] = set()

    @classmethod
    def from_mission(cls, mission: Any) -> 'MissionContext':
        """
        Factory method to create a MissionContext from a converter's Mission object.
        :param mission: The hydrated data_models.Mission object.
        :return: A populated MissionContext instance.
        """
        ctx = cls()
        
        # 1. Ships (Standalone + Wing members)
        for s in mission.ships:
            ctx.ships.add(s.name)
            ctx.ship_to_class[s.name] = s.ship_class
            ctx.ship_to_team[s.name] = s.team
            
        # 2. Wings
        for w in mission.wings:
            ctx.wings.add(w.name)
            # Find class and team from template or ships
            if w.ships:
                ctx.wing_to_template_class[w.name] = w.ships[0].ship_class
                ctx.wing_to_team[w.name] = w.ships[0].team
            
        # 3. Events
        for e in mission.events:
            if e.name:
                ctx.events.add(e.name)
                
        # 4. Goals
        for g in mission.goals:
            ctx.goals.add(g.name)
            
        # 5. Messages
        for m in mission.messages:
            ctx.messages.add(m.name)
            
        # 6. Waypoints
        for wp_name, wp_list in mission.waypoints.items():
            ctx.waypoints[wp_name] = len(wp_list)

        # 7. Jump Nodes
        for jn in mission.jump_nodes:
            ctx.jump_nodes.add(jn.name)

        # 8. Variables (TODO: FSIF doesn't explicitly define variables yet)
        # ctx.variables["mission_time"] = SexpReturnType.NUMBER
        
        return ctx

# =============================================================================
# OPERATOR DATABASE
# =============================================================================

OPERATORS = {}

def register_op(op_id, text, min_args, max_args, return_type):
    OPERATORS[text] = OperatorDef(op_id, text, min_args, max_args, return_type)

# Load definitions from generated file
for text, data in SEXP_DEFINITIONS.items():
    register_op(data["id"], text, data["min_args"], data["max_args"], data["return_type"])

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def map_opf_to_opr(opf_type):
    """
    Maps an argument type (OPF_*) to a return type (OPR_*).
    This tells us what kind of operator can be plugged into an argument slot.
    """
    if opf_type == OPF_BOOL:
        return SexpReturnType.BOOL
    if opf_type == OPF_NUMBER:
        return SexpReturnType.NUMBER
    if opf_type == OPF_POSITIVE:
        return SexpReturnType.POSITIVE
    if opf_type == OPF_NULL:
        return SexpReturnType.NULL
    if opf_type == OPF_AI_GOAL:
        return SexpReturnType.AI_GOAL
    
    # Most things (Ships, Wings, Messages, etc.) are just strings in the SEXP tree
    return SexpReturnType.STRING

# =============================================================================
# PARSER (Mirrors missionparse.cpp / get_sexp_main)
# =============================================================================

class SexpParser:
    """
    Parser for Symbolic Expression (SEXP) strings.
    Implements a recursive descent parser to convert LISP-like strings into SexpNode trees.
    """
    def __init__(self):
        """Initialize the parser state."""
        self.tokens: List[str] = []
        self.cursor = 0

    def parse(self, text: str) -> List[SexpNode]:
        """
        Main entry point for parsing a SEXP string.
        :param text: The raw SEXP string (e.g., '(when (true) (do-nothing))').
        :return: A list of root SexpNodes representing the parsed structure.
        """
        self.tokens = self._tokenize(text)
        self.cursor = 0
        roots = []
        while self.cursor < len(self.tokens):
            node = self._parse_node()
            if node:
                roots.append(node)
        return roots

    def _tokenize(self, text):
        """
        Splits text into tokens, handling parens, quotes, and comments.
        Mirrors FSO tokenizer behavior.
        """
        tokens = []
        i = 0
        length = len(text)
        
        while i < length:
            char = text[i]

            # 1. Skip Whitespace
            if char.isspace():
                i += 1
                continue

            # 2. Comments (;)
            if char == ';':
                while i < length and text[i] != '\n':
                    i += 1
                continue

            # 3. Parentheses
            if char in '()':
                tokens.append(char)
                i += 1
                continue

            # 4. Quoted Strings
            if char == '"':
                start = i + 1
                i += 1
                while i < length and text[i] != '"':
                    i += 1
                tokens.append(text[start:i]) # Add content without quotes
                i += 1 # Skip closing quote
                continue

            # 5. Standard Atoms (Text, Numbers, Operators)
            start = i
            while i < length and not text[i].isspace() and text[i] not in '();':
                i += 1
            tokens.append(text[start:i])

        return tokens

    def _parse_node(self):
        """Recursive function to build the tree."""
        if self.cursor >= len(self.tokens):
            return None

        token = self.tokens[self.cursor]
        self.cursor += 1

        # Case A: Start of a List
        if token == '(':
            # Look ahead: The first token inside ( usually determines the operator
            if self.cursor < len(self.tokens):
                op_text = self.tokens[self.cursor]
                
                # Check if it's a nested list immediately like ((...))
                if op_text == '(':
                    node = SexpNode(text="<container>", is_list=True)
                elif op_text == ')':
                    # Empty list ()
                    self.cursor += 1
                    return SexpNode(text="", is_list=True)
                else:
                    # Normal case: (operator arg1 arg2)
                    self.cursor += 1 
                    node = SexpNode(text=op_text, is_list=True)

                # Recursively parse children until ')'
                while self.cursor < len(self.tokens) and self.tokens[self.cursor] != ')':
                    child = self._parse_node()
                    if child:
                        node.add_child(child)

                # Consume closing ')'
                if self.cursor < len(self.tokens) and self.tokens[self.cursor] == ')':
                    self.cursor += 1
                else:
                    raise SyntaxError("Missing closing parenthesis")
                
                return node
        
        # Case B: Stray closing parenthesis — always a structural error.
        # The loop in Case A already stops before consuming ')'.
        # If we reach here, a ')' appeared at the top level or in a position
        # where no matching '(' preceded it.
        elif token == ')':
            raise SyntaxError("Unexpected closing parenthesis")

        # Case C: Atom (Number, String, Variable)
        else:
            return SexpNode(text=token, is_list=False)

# =============================================================================
# VALIDATOR (Mirrors sexp.cpp logic)
# =============================================================================

class SexpValidator:
    """
    Validator for Symbolic Expression (SEXP) trees.
    Performs recursive semantic analysis, type checking, and reference validation
    using rules transpiled from FreeSpace Open's C++ source code.
    """
    def __init__(self, context: MissionContext):
        """
        Initialize the validator with a mission context.
        :param context: MissionContext containing valid entity names for this validation run.
        """
        self.context = context
        self.current_subject: Optional[str] = None # Name of ship/wing being validated
        
        # Dispatch table for atom validation
        self._atom_validators = {
            OPF_BOOL: self._validate_bool,
            OPF_SHIP: self._validate_ship,
            OPF_WING: self._validate_wing,
            OPF_SHIP_WING: self._validate_ship_wing,
            OPF_SHIP_WING_POINT: self._validate_ship_wing_point,
            OPF_SHIP_WING_SHIPONTEAM_POINT: self._validate_ship_wing_point, # Alias for now
            OPF_POINT: self._validate_point,
            OPF_SHIP_POINT: self._validate_ship_point,
            OPF_WHO_FROM: self._validate_who_from,
            OPF_PRIORITY: self._validate_priority,
            OPF_AI_CLASS: self._validate_ai_class,
            OPF_IFF: self._validate_iff,
            OPF_WEAPON_NAME: self._validate_weapon_name,
            OPF_SHIP_CLASS_NAME: self._validate_ship_class_name,
            OPF_SHIP_TYPE: self._validate_ship_class_name, # Handles both
            OPF_SUBSYSTEM: self._validate_subsystem,
            OPF_SUBSYS_OR_GENERIC: self._validate_subsystem,
            OPF_DOCKER_POINT: self._validate_dockpoint,
            OPF_DOCKEE_POINT: self._validate_dockpoint,
            OPF_WAYPOINT_PATH: self._validate_waypoint_path,
            OPF_JUMP_NODE_NAME: self._validate_jump_node_name,
            OPF_EVENT_NAME: self._validate_event_name,
            OPF_GOAL_NAME: self._validate_goal_name,
            OPF_MESSAGE: self._validate_message,
            OPF_POSITIVE: self._validate_positive,
            OPF_NUMBER: self._validate_number,
            OPF_SHIP_FLAG: self._validate_ship_flag,
            OPF_WING_FLAG: self._validate_wing_flag,
            OPF_BACKGROUND_BITMAP: self._validate_background_bitmap,
            OPF_SUN_BITMAP: self._validate_sun_bitmap,
            OPF_NEBULA_PATTERN: self._validate_nebula_pattern,
            OPF_NEBULA_POOF: self._validate_nebula_poof,
            OPF_SOUNDTRACK_NAME: self._validate_soundtrack_name,
            OPF_AI_ORDER: self._validate_ai_order,
        }

    def validate(self, node: SexpNode, expected_type: SexpReturnType = SexpReturnType.NULL, recursive: bool = True, context: str = "") -> List[str]:
        """
        Recursively validates the node.
        
        :param node: The current node to check.
        :param expected_type: The return type expected by the parent (OPR_*).
        :param recursive: Whether to validate children.
        :param context: Context string for error messages (e.g. "Argument 1 of 'when'")
        :return: A list of error messages found during validation.
        """
        return self._validate_recursive(node, expected_type, recursive, context)

    def _validate_recursive(self, node: SexpNode, expected_type: SexpReturnType, recursive: bool, context: str = "") -> List[str]:
        errors: List[str] = []
        
        # 1. Determine Actual Return Type
        op_def = None
        actual_type = SexpReturnType.AMBIGUOUS

        if node.is_list:
            if node.text in OPERATORS:
                op_def = OPERATORS[node.text]
                actual_type = op_def.return_type
            elif node.text == "<container>":
                # Special handling for containers?
                # FSO does not generally allow anonymous lists (containers) where an operator is expected.
                # If we encounter one, it's likely a syntax error (e.g. ((...))).
                errors.append(self._format_error(f"Unexpected nested list (container). Expected an operator.", context))
                actual_type = SexpReturnType.NONE  # Force type mismatch if expected type is strict
            else:
                errors.append(self._format_error(f"Unknown operator: '{node.text}'", context))
                # Treat as AMBIGUOUS if unknown, allowing it to pass type check
                # but we cannot validate its arguments
                return errors
        else:
            # Atom
            actual_type = self._get_atom_return_type(node)

        # 2. Check Type Match (Actual vs Expected)
        if not self._sexp_query_type_match(expected_type, actual_type):
             errors.append(self._format_error(
                f"Type Mismatch: Expected {self._opr_name(expected_type)}, "
                f"Got {self._opr_name(actual_type)} ('{node.text}')",
                context
            ))

        # 3. If it's a list (Operator), validate arguments structure and types
        if node.is_list and op_def:
            num_args = len(node.children)
            
            if num_args < op_def.min_args:
                errors.append(self._format_error(f"Operator '{node.text}' needs at least {op_def.min_args} arguments, found {num_args}.", context))
            
            if num_args > op_def.max_args:
                errors.append(self._format_error(f"Operator '{node.text}' accepts at most {op_def.max_args} arguments, found {num_args}.", context))

            # 3a. AI Goal Applicability Check
            if node.text in FIGHTER_BOMBER_ONLY_OPERATORS and self.current_subject:
                # Check if subject is a fighter/bomber
                s_class = self.context.ship_to_class.get(self.current_subject)
                if not s_class:
                    s_class = self.context.wing_to_template_class.get(self.current_subject)
                
                if s_class and not is_fighter_bomber(s_class):
                    errors.append(self._format_error(
                        f"Operator '{node.text}' is invalid for non-fighter/non-bomber ship '{self.current_subject}' (class {s_class}). Larger ships only support a restricted set of AI goals.",
                        context
                    ))

            # 3b. Logical AI Checks (IFF, Self-Target)
            if self.current_subject and node.text in (GUARD_OPERATORS | ATTACK_OPERATORS):
                errors.extend(self._validate_ai_logic(node, self.current_subject, context))

            if recursive:
                for i, child in enumerate(node.children):
                    # Determine what OPF type the operator expects for this argument
                    arg_opf_type = self._query_operator_argument_type(op_def, i)
                    
                    # Special Subject Tracking for 'add-goal'
                    # If this is the second argument of add-goal, set current_subject
                    # based on the first argument (if it's an atom)
                    old_subject = self.current_subject
                    if node.text == "add-goal" and i == 1 and len(node.children) > 0:
                        first_arg = node.children[0]
                        if not first_arg.is_list:
                            self.current_subject = first_arg.text
                    # Also handle nested Subject inheritance if already set
                    elif self.current_subject:
                        pass # Keep current_subject
                    
                    # Map OPF (Argument Type) -> OPR (Return Type) for the child
                    child_expected_opr = map_opf_to_opr(arg_opf_type)
                    
                    # Context for child
                    child_context = f"Argument {i+1} of '{node.text}'"
                    
                    # Recurse: Check if the child returns the correct OPR type
                    errors.extend(self._validate_recursive(child, child_expected_opr, recursive, child_context))
                    
                    # Restore subject
                    self.current_subject = old_subject

                    # If the child is an atom, we also perform specific content validation
                    # (e.g. is "Alpha 1" actually a valid Ship name in this context?)
                    if not child.is_list:
                        errors.extend(self._validate_atom_content(child, arg_opf_type, child_context))
        
        return errors

    def _format_error(self, msg: str, context: str = "") -> str:
        if context:
            return f"[{context}] {msg}"
        return msg

    def _validate_ai_logic(self, node: SexpNode, subject_name: str, context: str) -> List[str]:
        """
        Performs logical checks for AI goals (IFF consistency and self-targeting).
        """
        errors = []
        if not node.children:
            return errors
        
        # Target is always the first argument (index 0) for these operators
        target_node = node.children[0]
        if target_node.is_list:
            # Cannot easily validate logical targets that are SEXPs
            return errors
            
        target_name = target_node.text
        
        # 1. Self-Targeting Check
        if subject_name == target_name:
            errors.append(self._format_error(
                f"Self-targeting error: '{subject_name}' is ordered to '{node.text}' itself.",
                context
            ))

        # 2. IFF Consistency Check
        subject_team = self.context.ship_to_team.get(subject_name) or self.context.wing_to_team.get(subject_name)
        target_team = self.context.ship_to_team.get(target_name) or self.context.wing_to_team.get(target_name)
        
        # Only validate if we know teams for both
        if subject_team and target_team:
            if node.text in GUARD_OPERATORS:
                # Friendly cannot guard Hostile (and vice versa)
                if subject_team == "Friendly" and target_team == "Hostile":
                    errors.append(self._format_error(
                        f"IFF Logic error: Friendly ship '{subject_name}' cannot be ordered to guard Hostile ship '{target_name}'.",
                        context
                    ))
                elif subject_team == "Hostile" and target_team == "Friendly":
                    errors.append(self._format_error(
                        f"IFF Logic error: Hostile ship '{subject_name}' cannot be ordered to guard Friendly ship '{target_name}'.",
                        context
                    ))
            
            elif node.text in ATTACK_OPERATORS:
                # Friendly cannot attack Friendly
                if subject_team == "Friendly" and target_team == "Friendly":
                    errors.append(self._format_error(
                        f"IFF Logic error: Friendly ship '{subject_name}' cannot be ordered to attack Friendly ship '{target_name}'.",
                        context
                    ))
                    
        return errors

    def _query_operator_argument_type(self, op: OperatorDef, arg_index: int):
        return get_argument_type(op.id, arg_index)

    def _sexp_query_type_match(self, expected_opr: SexpReturnType, actual_opr: SexpReturnType) -> bool:
        """
        Returns True if 'actual_opr' return type satisfies 'expected_opr'.
        """
        if expected_opr == SexpReturnType.AMBIGUOUS or actual_opr == SexpReturnType.AMBIGUOUS:
            return True
            
        if expected_opr == SexpReturnType.NUMBER:
            return actual_opr in [SexpReturnType.NUMBER, SexpReturnType.POSITIVE]
            
        if expected_opr == SexpReturnType.POSITIVE:
            # FSO allows Number where Positive is expected (relaxed)
            return actual_opr in [SexpReturnType.POSITIVE, SexpReturnType.NUMBER]
            
        # Strict matches for others (Bool, Null, Goal, String)
        return expected_opr == actual_opr

    def _get_atom_return_type(self, node: SexpNode) -> SexpReturnType:
        if self._is_number(node.text):
            return SexpReturnType.NUMBER
        if node.text in ["true", "false"]:
            return SexpReturnType.BOOL
        if node.text in self.context.variables:
            # Assuming variables are stored with SexpReturnType values
            # but providing a fallback to AMBIGUOUS or cast if they are raw ints
            val = self.context.variables[node.text]
            return SexpReturnType(val)
        
        # Everything else is treated as a String
        return SexpReturnType.STRING

    def _validate_atom_content(self, node: SexpNode, expected_opf, context: str = "") -> List[str]:
        """Checks if the raw string content fits the expected specific OPF type."""
        validator = self._atom_validators.get(expected_opf)
        if validator:
            return validator(node.text, context, node)
        return []

    # --- Helpers ---

    def _is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _opr_name(self, t: Union[SexpReturnType, int]) -> str:
        try:
            enum_val = SexpReturnType(t)
        except ValueError:
            return f"Type({t})"

        names = {
            SexpReturnType.BOOL: "Boolean",
            SexpReturnType.NUMBER: "Number",
            SexpReturnType.POSITIVE: "Positive Number",
            SexpReturnType.STRING: "String",
            SexpReturnType.NULL: "Action/Void",
            SexpReturnType.AMBIGUOUS: "Any",
            SexpReturnType.AI_GOAL: "AI Goal",
            SexpReturnType.NONE: "None",
            SexpReturnType.FLEXIBLE_ARGUMENT: "Flexible Argument"
        }
        return names.get(enum_val, f"Type({enum_val.value})")

    def _is_valid_special_token(self, text: str) -> bool:
        """Checks if text is a valid special token (starts with # or <)."""
        if text == "<none>" or text == "<default>": return True
        return text in fs_data.ALLOWED_ANCHORS_TOKENS

    # --- Atom Validators ---

    def _validate_bool(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text in ["true", "false"]: return []
        if self._is_number(text): return []
        if not node.is_list:
            return [self._format_error(f"Invalid boolean value: '{text}'. Expected 'true', 'false', or a number.", context)]
        return []

    def _validate_ship(self, text: str, context: str, node: SexpNode) -> List[str]:
        if self._is_valid_special_token(text): return []
        if text in self.context.ships: return []
        if text in self.context.wings:
            return [self._format_error(f"Argument '{text}' is a Wing, but Operator expects a Ship.", context)]
        return [self._format_error(f"Invalid Ship name: '{text}'", context)]

    def _validate_wing(self, text: str, context: str, node: SexpNode) -> List[str]:
        if self._is_valid_special_token(text): return []
        if text in self.context.wings: return []
        if text in self.context.ships:
            return [self._format_error(f"Argument '{text}' is a Ship, but Operator expects a Wing.", context)]
        return [self._format_error(f"Invalid Wing name: '{text}'", context)]

    def _validate_ship_wing(self, text: str, context: str, node: SexpNode) -> List[str]:
        if self._is_valid_special_token(text): return []
        if text in self.context.ships: return []
        if text in self.context.wings: return []
        return [self._format_error(f"Invalid Ship/Wing name: '{text}'", context)]

    def _validate_specific_point(self, text: str, context: str) -> List[str]:
        """Helper to validate Path:N syntax and range."""
        parts = text.split(':')
        if len(parts) != 2:
            return [self._format_error(f"Invalid waypoint syntax: '{text}'. Expected format 'PathName:Index'.", context)]
        
        base_name, index_str = parts
        if base_name not in self.context.waypoints:
            return [self._format_error(f"Invalid waypoint path: '{base_name}' in '{text}'.", context)]
            
        try:
            index = int(index_str)
        except ValueError:
            return [self._format_error(f"Invalid waypoint point index '{index_str}' in '{text}'. Must be an integer.", context)]
            
        # Point indices are 1-based in FSO SEXPs
        count = self.context.waypoints[base_name]
        if index < 1 or index > count:
            return [self._format_error(f"Waypoint point index {index} out of bounds for path '{base_name}' (has {count} points).", context)]
            
        return []

    def _validate_ship_wing_point(self, text: str, context: str, node: SexpNode) -> List[str]:
        if self._is_valid_special_token(text): return []
        if text in self.context.ships: return []
        if text in self.context.wings: return []
        
        # Check waypoint path reference (PathName:Index)
        if ":" in text:
            return self._validate_specific_point(text, context)
            
        return [self._format_error(f"Invalid Ship/Wing/Point name: '{text}'", context)]

    def _validate_point(self, text: str, context: str, node: SexpNode) -> List[str]:
        if self._is_valid_special_token(text): return []
        
        # Whole waypoint path
        if text in self.context.waypoints: return []
        
        # Specific waypoint point Path:N
        if ":" in text:
            return self._validate_specific_point(text, context)

        return [self._format_error(f"Invalid Point/Waypoint name: '{text}'", context)]

    def _validate_ship_point(self, text: str, context: str, node: SexpNode) -> List[str]:
        if self._is_valid_special_token(text): return []
        if text in self.context.ships: return []
        
        # Point (Waypoint/Specific Point)
        if text in self.context.waypoints: return []
        if ":" in text:
            return self._validate_specific_point(text, context)
            
        return [self._format_error(f"Invalid Ship/Point name: '{text}'", context)]

    def _validate_who_from(self, text: str, context: str, node: SexpNode) -> List[str]:
        # 1. Check if it's a known Ship
        if text in self.context.ships: return []
        
        # 2. Check if it's a known Wing
        if text in self.context.wings: return []
        
        # 3. If it starts with special chars, it MUST be a valid special token
        if text.startswith("#") or text.startswith("<"):
            if self._is_valid_special_token(text): return []
            return [self._format_error(f"Invalid Special Message Sender: '{text}' (Unknown token)", context)]
            
        # 4. Otherwise invalid
        return [self._format_error(f"Invalid Message Sender (WHO_FROM): '{text}'", context)]

    def _validate_priority(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_data.ALLOWED_PRIORITIES:
            return [self._format_error(f"Invalid Priority: '{text}'. Expected one of {fs_data.ALLOWED_PRIORITIES}.", context)]
        return []

    def _validate_ai_class(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_data.ALLOWED_AI_CLASSES:
            return [self._format_error(f"Invalid AI Class: '{text}'", context)]
        return []

    def _validate_iff(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_data.ALLOWED_TEAMS:
            return [self._format_error(f"Invalid Team (IFF): '{text}'. Expected one of {fs_data.ALLOWED_TEAMS}.", context)]
        return []

    def _validate_weapon_name(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_data.ALLOWED_WEAPONS:
            return [self._format_error(f"Invalid Weapon: '{text}'", context)]
        return []

    def _validate_ship_class_name(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_data.ALLOWED_SHIP_CLASSES and text != "fighter/bomber":
            return [self._format_error(f"Invalid Ship Class: '{text}'", context)]
        return []

    def _get_associated_ship_node(self, node: SexpNode) -> Optional[SexpNode]:
        """
        Attempts to find a sibling node that represents the ship/wing associated with this subsystem node.
        Uses a heuristic: 
        1. Check the immediate predecessor (Index - 1).
        2. Fallback to the first argument (Index 0).
        """
        if not node.parent or not node.parent.is_list:
            return None
        
        # Determine current node's index
        try:
            current_index = node.parent.children.index(node)
        except ValueError:
            return None
            
        op_name = node.parent.text
        if op_name not in OPERATORS:
            return None
            
        op_def = OPERATORS[op_name]
        
        # 1. Check predecessor
        if current_index > 0:
            pred_type = self._query_operator_argument_type(op_def, current_index - 1)
            if pred_type in SHIP_TYPE_OPFS:
                return node.parent.children[current_index - 1]
                
        # 2. Check first argument
        if current_index != 0:
            first_type = self._query_operator_argument_type(op_def, 0)
            if first_type in SHIP_TYPE_OPFS:
                return node.parent.children[0]
                
        return None

    def _validate_subsystem(self, text: str, context: str, node: SexpNode) -> List[str]:
        # 1. Basic check against global list
        if text not in ALL_KNOWN_SUBSYSTEMS:
            return [self._format_error(f"Invalid Subsystem: '{text}'. (Not found in any known ship class)", context)]
            
        # 2. Context-aware check against specific ship/wing class
        ship_node = self._get_associated_ship_node(node)
        if ship_node and not ship_node.is_list:
            ship_name = ship_node.text
            
            # Resolve ship class
            s_class = self.context.ship_to_class.get(ship_name)
            if not s_class:
                s_class = self.context.wing_to_template_class.get(ship_name)
                
            if s_class:
                if s_class in fs_data.ALLOWED_SUBSYSTEMS:
                    allowed = fs_data.ALLOWED_SUBSYSTEMS[s_class]
                    # Virtual/Special subsystems are always allowed
                    if text.lower() not in ["pilot", "hull", "shields"] and text not in allowed:
                        return [self._format_error(
                            f"Ship '{ship_name}' (class {s_class}) does not have a subsystem named '{text}'.",
                            context
                        )]
                elif s_class != "Unknown":
                    # We have a class but no subsystem data for it?
                    # This might happen for special objects like NavBuoys.
                    # If the global list had it, we allow it.
                    pass
                    
        return []

    def _validate_dockpoint(self, text: str, context: str, node: SexpNode) -> List[str]:
        # 1. Basic check against global list
        if text not in ALL_KNOWN_DOCKPOINTS:
            return [self._format_error(f"Invalid Dockpoint: '{text}'. (Not found in any known ship class)", context)]
            
        # 2. Context-aware check
        if not node.parent or not node.parent.is_list:
            return []
            
        try:
            current_index = node.parent.children.index(node)
        except ValueError:
            return []
            
        op_name = node.parent.text
        if op_name not in OPERATORS:
            return []
            
        # Logic for ai-dock: ( ai-dock Dockee DockerPoint DockeePoint Priority )
        # Note: In initial ai_goals, "docker" is current_subject.
        # Dockee (Arg 1 in SEXP, Index 0 in children)
        # DockerPoint (Arg 2, Index 1) -> Context is docker (current_subject)
        # DockeePoint (Arg 3, Index 2) -> Context is Dockee (Arg 1 / Index 0)
        ship_name = None
        if op_name == "ai-dock":
            if current_index == 1: # DockerPoint
                ship_name = self.current_subject
            elif current_index == 2: # DockeePoint
                if len(node.parent.children) > 0:
                    ship_node = node.parent.children[0]
                    if not ship_node.is_list:
                        ship_name = ship_node.text
        
        # DEBUG
        # print(f"DEBUG: op={op_name}, idx={current_index}, node={text}, ship_name={ship_name}")
        
        if not ship_name:
            # Fallback to _get_associated_ship_node heuristic for other operators
            ship_node = self._get_associated_ship_node(node)
            if ship_node and not ship_node.is_list:
                ship_name = ship_node.text
                
        if ship_name:
            s_class = self.context.ship_to_class.get(ship_name)
            if not s_class:
                s_class = self.context.wing_to_template_class.get(ship_name)
                
            if s_class and s_class in fs_data.ALLOWED_DOCKPOINTS:
                allowed = fs_data.ALLOWED_DOCKPOINTS[s_class]
                if text not in allowed:
                    return [self._format_error(
                        f"Ship '{ship_name}' (class {s_class}) does not have a dockpoint named '{text}'.",
                        context
                    )]
                    
        return []

    def _validate_waypoint_path(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text in self.context.waypoints: return []
        return [self._format_error(f"Invalid Waypoint Path: '{text}'", context)]

    def _validate_jump_node_name(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text in self.context.jump_nodes: return []
        return [self._format_error(f"Invalid Jump Node: '{text}'", context)]

    def _validate_event_name(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text in self.context.events: return []
        return [self._format_error(f"Invalid Event name: '{text}'", context)]

    def _validate_goal_name(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text in self.context.goals: return []
        return [self._format_error(f"Invalid Goal name: '{text}'", context)]

    def _validate_message(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text in self.context.messages: return []
        return [self._format_error(f"Invalid Message name: '{text}'", context)]

    def _validate_positive(self, text: str, context: str, node: SexpNode) -> List[str]:
        if self._is_number(text):
            if float(text) < 0:
                return [self._format_error(f"Value '{text}' must be positive.", context)]
            return []
        elif text in self.context.variables:
            return []
        else:
            return [self._format_error(f"Value '{text}' is not a valid number.", context)]

    def _validate_number(self, text: str, context: str, node: SexpNode) -> List[str]:
        if not self._is_number(text):
            if text not in self.context.variables:
                return [self._format_error(f"Value '{text}' is not a valid number.", context)]
        return []

    def _validate_ship_flag(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_flags_constants.SHIP_FLAGS_BUCKET:
            return [self._format_error(f"Invalid Ship Flag: '{text}'", context)]
        return []

    def _validate_wing_flag(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_flags_constants.WING_FLAGS_BUCKET:
            return [self._format_error(f"Invalid Wing Flag: '{text}'", context)]
        return []

    def _validate_background_bitmap(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_data.ALLOWED_BACKGROUNDS:
            return [self._format_error(f"Invalid Background Bitmap: '{text}'", context)]
        return []

    def _validate_sun_bitmap(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_data.ALLOWED_SUNS:
            return [self._format_error(f"Invalid Sun Bitmap: '{text}'", context)]
        return []

    def _validate_nebula_pattern(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_data.ALLOWED_NEBULA_PATTERNS:
            return [self._format_error(f"Invalid Nebula Pattern: '{text}'", context)]
        return []

    def _validate_nebula_poof(self, text: str, context: str, node: SexpNode) -> List[str]:
        if text not in fs_data.ALLOWED_NEBULA_POOFS:
            return [self._format_error(f"Invalid Nebula Poof: '{text}'", context)]
        return []

    def _validate_soundtrack_name(self, text: str, context: str, node: SexpNode) -> List[str]:
        valid_music = fs_data.ALLOWED_MUSIC_MISSION | fs_data.ALLOWED_MUSIC_BRIEFING
        if text not in valid_music:
            return [self._format_error(f"Invalid Soundtrack Name: '{text}'", context)]
        return []

    def _validate_ai_order(self, text: str, context: str, node: SexpNode) -> List[str]:
        valid_orders = {
            "Attack Target", "Disable Target", "Disarm Target", "Destroy Subsystem",
            "Protect Target", "Ignore Target", "Form on my wing", "Cover me",
            "Engage Enemy", "Capture Target", "Rearm me", "Abort rearm", "Depart",
            "Stay Near Target", "Keep Safe Distance", "Evade Target"
        }
        if text not in valid_orders:
            return [self._format_error(f"Invalid Player AI Order: '{text}'. Expected one of {sorted(valid_orders)}.", context)]
        return []

# =============================================================================
# INTEGRATION ENTRY POINT
# =============================================================================

import logging
logger = logging.getLogger(__name__)

def validate_mission(mission) -> bool:
    """
    Main entry point for FSIF converter integration.
    :param mission: The hydrated Mission object (data_models.Mission)
    :return: True if passed, False if errors found
    """
    logger.info("[INFO] [Advanced SEXP Validator] Starting strict validation...")

    # 1. Build Context
    ctx = MissionContext.from_mission(mission)
    
    parser = SexpParser()
    validator = SexpValidator(ctx)
    
    total_errors = 0
    
    # Task List: (Context Description, SEXP String, Expected Return Type)
    tasks = []
    
    # Events
    for e in mission.events:
        if e.formula:
            tasks.append((f"Event '{e.name or '<unnamed>'}'", e.formula, SexpReturnType.NULL))
            
    # Goals
    for g in mission.goals:
        if g.formula:
            tasks.append((f"Goal '{g.name}'", g.formula, SexpReturnType.BOOL))
            
    # Ships
    for s in mission.ships:
        if s.arrival_condition:
            tasks.append((f"Ship '{s.name}' Arrival Cue", s.arrival_condition, SexpReturnType.BOOL))
        if s.departure_condition:
            tasks.append((f"Ship '{s.name}' Departure Cue", s.departure_condition, SexpReturnType.BOOL))
        if s.initial_orders:
            # initial_orders field usually contains "( goals ... )"
            # 'goals' operator returns SexpReturnType.NULL (Action), but contains AI Goals.
            tasks.append((f"Ship '{s.name}' AI Goals", s.initial_orders, SexpReturnType.NULL))
            
    # Wings
    for w in mission.wings:
        if w.arrival_condition:
            tasks.append((f"Wing '{w.name}' Arrival Cue", w.arrival_condition, SexpReturnType.BOOL))
        if w.departure_condition:
            tasks.append((f"Wing '{w.name}' Departure Cue", w.departure_condition, SexpReturnType.BOOL))
        if w.initial_orders:
            tasks.append((f"Wing '{w.name}' AI Goals", w.initial_orders, SexpReturnType.NULL))
            
    # Debriefing
    for i, stage in enumerate(mission.debriefing.stages):
        if stage.display_condition:
            tasks.append((f"Debriefing Stage {i+1}", stage.display_condition, SexpReturnType.BOOL))

    # Briefing (if any conditions exist - usually not in standard briefing, but check spec)
    # Standard briefing uses $Formula but usually ( true ). 
    # FSIF doesn't seem to expose Briefing formula in stages? 
    # Checking data_models.BriefingStage... no formula field.
    # checking fs2_writer: writes ( true ).
    # So we skip briefing.

    # Execution
    for desc, sexp, expected_type in tasks:
        # logger.info(f"Validating {desc}...")
        
        # Extract subject from description if it's an AI Goals task
        # Format: "Ship 'Name' AI Goals" or "Wing 'Name' AI Goals"
        validator.current_subject = None
        if "AI Goals" in desc:
            match = re.search(r"(?:Ship|Wing) '(.+?)'", desc)
            if match:
                validator.current_subject = match.group(1)

        try:
            roots = parser.parse(sexp)
            for root in roots:
                errors = validator.validate(root, expected_type=expected_type)
                if errors:
                    logger.error(f"[ERROR] [FAIL] {desc}:")
                    for e in errors:
                        logger.error(f"  - {e}")
                    total_errors += len(errors)
        except Exception as e:
            logger.error(f"[ERROR] [CRASH] {desc}: Parser exception: {e}")
            total_errors += 1

    if total_errors > 0:
        logger.error(f"[FAILED] [Advanced SEXP Validator] Validation FAILED with {total_errors} errors.")
        return False
    else:
        logger.info("[SUCCESS] [Advanced SEXP Validator] Validation PASSED.")
        return True
