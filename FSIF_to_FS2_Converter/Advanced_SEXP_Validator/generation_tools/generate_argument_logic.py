import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
VALIDATOR_DIR = BASE_DIR.parent
SOURCE_FILE = VALIDATOR_DIR / "FSO code excerpts" / "sexpdotcpp_excerpts.txt"
OUTPUT_FILE = VALIDATOR_DIR / "generated_code" / "sexp_argument_logic.py"

class CaseBlock:
    def __init__(self, labels):
        self.labels = labels        # List[str], e.g. ["OP_A", "OP_B"]
        self.lines = []             # List[str], raw C++ lines
        self.fallthrough = True     # Default is True (C++ behavior)
        self.effective_labels = []  # List[str], resolved labels including predecessors

    def __repr__(self):
        return f"Block(labels={self.labels}, lines={len(self.lines)}, fallthrough={self.fallthrough})"

def transpile_cpp_to_python(cpp_code):
    lines = cpp_code.splitlines()
    py_lines = []
    
    # 1. Parsing Phase: Build CaseBlocks
    blocks = []
    current_labels = []
    current_body = []
    
    in_switch = False
    switch_brace_level = 0
    current_brace_level = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Clean line for brace counting
        clean_line = line.split("//")[0]
        open_braces = clean_line.count('{')
        close_braces = clean_line.count('}')
        
        if "switch" in stripped and not in_switch:
            in_switch = True
            switch_brace_level = current_brace_level
            current_brace_level += open_braces - close_braces
            continue
            
        if not in_switch:
            current_brace_level += open_braces - close_braces
            continue
            
        # Inside switch
        new_level = current_brace_level + open_braces - close_braces
        
        if new_level == switch_brace_level:
            # End of switch
            if current_labels or current_body:
                # Flush final block
                block = create_block(current_labels, current_body)
                blocks.append(block)
            break
            
        is_case_line = False
        is_default_line = False
        
        # Check for case/default at the correct nesting level (immediately inside switch)
        if current_brace_level == switch_brace_level + 1:
            case_match = re.match(r"case\s+(OP_[A-Z0-9_]+):", stripped)
            default_match = stripped.startswith("default:")
            
            if case_match or default_match:
                is_case_line = True
                if default_match: is_default_line = True
                
                # If we have a pending body, flush it to a block
                if current_body:
                    block = create_block(current_labels, current_body)
                    blocks.append(block)
                    current_labels = []
                    current_body = []
                
                if case_match:
                    current_labels.append(case_match.group(1))
                else:
                    current_labels.append("DEFAULT")
        
        current_brace_level = new_level
        
        if is_case_line:
            continue
            
        # Accumulate body lines if we are inside a case
        if current_labels:
            current_body.append(line)

    # 2. Resolution Phase: Handle Fallthroughs
    for i, block in enumerate(blocks):
        if "DEFAULT" in block.labels:
            continue
            
        # Initialize effective labels with own labels
        if not block.effective_labels:
            block.effective_labels = list(block.labels)
            
        # If this block falls through, propagate its effective labels to the next block
        if block.fallthrough and i + 1 < len(blocks):
            next_block = blocks[i+1]
            if "DEFAULT" not in next_block.labels:
                seen = set(next_block.effective_labels) if next_block.effective_labels else set(next_block.labels)
                if not next_block.effective_labels:
                     next_block.effective_labels = list(next_block.labels)
                
                for op in block.effective_labels:
                    if op not in seen:
                        next_block.effective_labels.append(op)
                        seen.add(op)

    # 3. Generation Phase: Produce Python Code
    py_lines.append("from opf_definitions import *")
    py_lines.append("from sexp_definitions import INT_MAX")
    py_lines.append("\n")
    py_lines.append("def get_argument_type(op, arg_index):")
    
    # Generate static blocks
    for block in blocks:
        if "DEFAULT" in block.labels:
            continue # Handle default at the end
            
        if not block.effective_labels:
            continue
            
        generate_block_code(py_lines, block.effective_labels, block.lines)

    # Default block handling
    py_lines.append("    # Default/Fallback")
    py_lines.append("    return OPF_NONE")
    
    return "\n".join(py_lines)

def create_block(labels, lines):
    block = CaseBlock(list(labels))
    block.lines = list(lines)
    
    # Analyze for fallthrough
    for i in range(len(lines) - 1, -1, -1):
        s = lines[i].strip()
        s = s.split("//")[0].strip()
        if not s: continue
        
        if s.startswith("return") or s == "break;" or s.startswith("Error("):
            block.fallthrough = False
            break
            
        if "FALLTHROUGH" in s:
            block.fallthrough = True
            break
        
    return block

def generate_block_code(py_lines, labels, body_lines):
    # Condition
    if len(labels) == 1:
        cond = f'    if op == "{labels[0]}":'
    else:
        ops_list = ", ".join([f'"{op}"' for op in labels])
        cond = f'    if op in [{ops_list}]:'
    py_lines.append(cond)
    
    # Body Generation with Indentation Tracking
    indent_level = 2 # Starts at 2 tabs (function + if)
    
    # Track body content to ensure we don't output empty blocks
    body_start_idx = len(py_lines)
    
    # Join multiline statements but preserve brace structure lines
    joined_lines = join_multiline_statements(body_lines)
    
    for line in joined_lines:
        s_raw = line.strip()
        if not s_raw: continue
        
        # Analyze braces for indentation adjustment BEFORE processing
        open_braces = s_raw.count('{')
        close_braces = s_raw.count('}')
        
        # If line starts with closing brace, dedent immediately
        if s_raw.startswith("}"):
            indent_level = max(2, indent_level - 1)
            
        # Process the line content -> returns LIST of lines
        py_code_lines = process_cpp_line(s_raw)
        
        for py_code in py_code_lines:
            if not py_code: continue
            
            # Special handling for else/elif dedenting
            current_indent = indent_level
            if py_code.startswith("else") or py_code.startswith("elif"):
                current_indent = max(2, indent_level - 1)
                # Permanently adjust if we are dedenting an if block
                indent_level = current_indent
            
            py_indent = "    " * current_indent
            py_lines.append(f"{py_indent}{py_code}")
            
            # If line starts a block, indent next
            if py_code.endswith(":"):
                indent_level += 1
            
            # CRITICAL FIX: If line is a return statement, and we are inside an implicit block (indent > 2),
            # we should dedent because the block is finished.
            # This handles: if A: return X \n if B: return Y (nested without this logic)
            if py_code.startswith("return ") and indent_level > 2:
                 indent_level -= 1

        # Fallback to C++ brace logic if not converted to Python block
        # Only if we didn't already indent via python logic
        if open_braces > 0:
             pass
            
        # If line did not start with } but contained }, we dedent after
        if not s_raw.startswith("}") and close_braces > 0:
             indent_level = max(2, indent_level - close_braces)

    # Check if we generated any code for this block (avoid IndentationError)
    added_lines = py_lines[body_start_idx:]
    has_code = False
    for l in added_lines:
        if l.strip() and not l.strip().startswith("#"):
            has_code = True
            break
            
    if not has_code:
        py_lines.append("        pass")

def join_multiline_statements(lines):
    joined = []
    pending = ""
    
    for line in lines:
        s = line.strip().split("//")[0].strip()
        if not s: continue
        
        # If it's a brace-only line, don't join it to previous
        if s in ["{", "}", "};"] or s.startswith("}") or s.endswith("{"):
            if pending:
                joined.append(pending)
                pending = ""
            joined.append(s)
            continue
            
        if pending:
            pending += " " + s
        else:
            pending = s
            
        # Check balance (if not a brace line)
        if pending.count('(') == pending.count(')'):
            # Check if it ends with partial operator
            if not (pending.endswith("||") or pending.endswith("&&") or pending.endswith("?") or pending.endswith(":")):
                joined.append(pending)
                pending = ""
            
    if pending:
        joined.append(pending)
    return joined

def process_cpp_line(s):
    # Returns a LIST of strings
    
    # 1. Clean artifacts
    if s.startswith("/*") or s.startswith("//"): return []
    if "FALLTHROUGH" in s: return ["# FALLTHROUGH"]
    if s == "break;": return [] 
    if s in ["{", "}", "};"]: return [] 
    if s.startswith("Assertion"): return []
    if s.startswith("UNREACHABLE"): return ["# UNREACHABLE"]
    if s.startswith("Error"): return ["# Error"]
    
    # 2. Syntax replacements
    # Preserve strings by using a placeholder? Too complex.
    # Simple replacement but avoid replacing inside quotes if possible.
    # For this file, most '!' are logical nots. String literals are rare (except op names which we processed).
    
    s = s.replace("argnum", "arg_index")
    s = s.replace("&&", "and")
    s = s.replace("||", "or")
    
    if "!" in s and "=\"" not in s: # Rough check to avoid replacing inside strings?
        s = s.replace("!", "not ")
    
    s = re.sub(r'->', '.', s)
    s = re.sub(r'::', '.', s)
    
    if "++" in s: s = s.replace("++", " += 1")
    if "--" in s: s = s.replace("--", " -= 1")
    
    # Remove types
    s = re.sub(r'^(int|bool|auto|size_t|sexp_container|SCP_string)\s*[\*\&]?\s+', '', s)
    if s.startswith("const "): s = s[6:].strip()
    
    # Handle control flow
    if s.startswith("return"): 
        s = s.replace(";", "")
    elif s.endswith(";"):
        s = s[:-1]

    # Ternary
    ternary_match = re.match(r"return\s+(.+?)\s*\?\s*(.+?)\s*:\s*(.+)", s)
    if ternary_match:
        cond = ternary_match.group(1)
        true_val = ternary_match.group(2)
        false_val = ternary_match.group(3)
        s = f"return {true_val} if {cond} else {false_val}"

    # Convert inner switch to if/elif chain logic
    if s.startswith("switch"):
        return ["# switch detected"]
    
    if s.startswith("case "):
        # Check for inline return: case X: return Y;
        # Split by :
        parts = s.split(":", 1)
        case_part = parts[0]
        rest = parts[1].strip()
        
        match = re.match(r"case\s+(.+)", case_part)
        if match:
            val = match.group(1)
            lines = [f"if arg_index == {val}:"]
            if rest:
                processed_rest = process_cpp_line(rest)
                lines.extend(processed_rest)
            return lines
    
    if s.startswith("default:"):
        rest = s[len("default:"):].strip()
        lines = ["else:"]
        if rest:
             lines.extend(process_cpp_line(rest))
        return lines

    # Handle C++ if/else with braces
    if s.endswith("{"): s = s[:-1].strip()
    if s.startswith("}"): s = s[1:].strip()
    
    if s.startswith("if"):
        if not s.endswith(":"): s += ":"
        
    if s.startswith("else if"):
        s = s.replace("else if", "elif")
        if not s.endswith(":"): s += ":"
        
    if s == "else":
        s = "else:"

    if s.startswith("else") and not s.startswith("elif") and s != "else" and s != "else:":
        rest = s[4:].strip()
        lines = ["else:"]
        if rest:
             lines.extend(process_cpp_line(rest))
        return lines

    # Quote OP_ constants
    s = re.sub(r'(?<!["\w])(OP_[A-Z0-9_]+)(?!["\w])', r'"\1"', s)
    
    # Cleanup parens around conditions "if (x):" -> "if x:"
    if s.startswith("if (") and s.endswith("):"):
        inner = s[4:-2]
        if inner.count('(') == inner.count(')'): 
            s = f"if {inner}:"
            
    if s.startswith("elif (") and s.endswith("):"):
        inner = s[6:-2]
        if inner.count('(') == inner.count(')'):
            s = f"elif {inner}:"

    return [s]

def generate():
    print(f"Reading from {SOURCE_FILE}...")
    try:
        content = SOURCE_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Source file not found at {SOURCE_FILE}")
        return

    start_marker = "int query_operator_argument_type(int op, int argnum)"
    start_idx = content.find(start_marker)
    
    if start_idx == -1:
        print("Error: Could not find query_operator_argument_type function.")
        return
        
    open_brace = content.find("{", start_idx)
    
    lines = content[start_idx:].splitlines()
    captured_lines = []
    balance = 0
    started = False
    
    for line_num, line in enumerate(lines, start=start_idx):
        captured_lines.append(line)
        
        clean_line = line.split("//")[0]
        balance += clean_line.count('{')
        balance -= clean_line.count('}')
        
        if '{' in clean_line:
            started = True
            
        if started and balance == 0:
            print(f"DEBUG: Block ended at line {line_num}: {line.strip()}")
            break
            
    func_body = "\n".join(captured_lines)
    
    print("Transpiling logic...")
    py_code = transpile_cpp_to_python(func_body)
    
    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# sexp_argument_logic.py\n")
        f.write("# Auto-generated from FSO sexp.cpp. Do not edit manually.\n\n")
        f.write(py_code)
        
    print("Done.")

if __name__ == "__main__":
    generate()
