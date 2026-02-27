import yaml
from pathlib import Path
from typing import List, Tuple, Any

def validate_sexp_styles(fsif_path: Path) -> List[str]:
    """
    Validate that all SEXP fields in the FSIF file use the block scalar style ('|').
    
    Args:
        fsif_path: Path to the FSIF file.
        
    Returns:
        List of error messages describing any violations found.
    """
    errors: List[str] = []
    
    try:
        with open(fsif_path, 'r', encoding='utf-8') as f:
            # use safe_load to verify it's valid YAML first, though compose also parses
            # but compose preserves node structure which is what we need
            root_node = yaml.compose(f)
    except Exception as e:
        return [f"Error parsing YAML for style validation: {e}"]

    if not isinstance(root_node, yaml.MappingNode):
        return [] # Not a valid FSIF structure if root is not a mapping

    # Helper to traverse and check specific keys
    def check_node(node: yaml.Node, path: str = ""):
        if isinstance(node, yaml.MappingNode):
            for key_node, value_node in node.value:
                if not isinstance(key_node, yaml.ScalarNode):
                    continue
                
                key = key_node.value
                current_path = f"{path}.{key}" if path else key
                
                # Check for SEXP fields
                if key in ['arrival_cue', 'departure_cue', 'ai_goals', 'formula', 'condition']:
                    # These fields must be block scalars if they are strings
                    if isinstance(value_node, yaml.ScalarNode):
                        # style '|' is block literal
                        if value_node.style != '|':
                            line = value_node.start_mark.line + 1
                            errors.append(
                                f"SEXP field '{key}' at line {line} must use literal block scalar style ('|'). Flow style ('\"') or folded block style ('>') is not allowed."
                            )
                
                # Recurse into children
                check_node(value_node, current_path)
                
        elif isinstance(node, yaml.SequenceNode):
            for i, item_node in enumerate(node.value):
                check_node(item_node, f"{path}[{i}]")

    check_node(root_node)
    return errors
