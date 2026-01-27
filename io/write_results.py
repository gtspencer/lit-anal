"""Write final results to JSON output."""

import json
from pathlib import Path
from typing import Dict, Any
from schemas.state import BookState, FinalCharacterResult


def write_results_json(
    state: BookState,
    output_path: str,
    include_metadata: bool = False,
) -> None:
    """Write final ranked characters to JSON file.
    
    Args:
        state: Final state after graph execution
        output_path: Path to output JSON file
        include_metadata: Whether to include ranking_run_metadata in output
    """
    ranked_characters = state.get('final_ranked_characters', [])
    
    output_data = ranked_characters
    
    if include_metadata:
        output_data = {
            'ranked_characters': ranked_characters,
            'metadata': state.get('ranking_run_metadata', {}),
        }
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Results written to {output_path}")


def write_full_state_json(state: BookState, output_path: str) -> None:
    """Write full state to JSON file (for debugging).
    
    Args:
        state: Full state after graph execution
        output_path: Path to output JSON file
    """
    # Convert sets to lists for JSON serialization
    serializable_state = {}
    for key, value in state.items():
        if isinstance(value, dict):
            serializable_value = {}
            for k, v in value.items():
                if isinstance(v, set):
                    serializable_value[k] = list(v)
                else:
                    serializable_value[k] = v
            serializable_state[key] = serializable_value
        elif isinstance(value, set):
            serializable_state[key] = list(value)
        else:
            serializable_state[key] = value
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_state, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"Full state written to {output_path}")

