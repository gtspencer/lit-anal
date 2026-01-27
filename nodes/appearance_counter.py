"""AppearanceCounter node: counts scenes in which each character appears."""

from collections import defaultdict
from schemas.state import BookState
from utils.aliases import find_all_alias_matches


def appearance_counter_node(state: BookState) -> BookState:
    """Count scenes in which each character appears (binary per scene).
    
    Reads:
    - `current_scenes`: list of scenes
    - `alias_index`: alias to char_id mapping
    
    Writes:
    - `chapter_appearances_by_char`: dict mapping char_id -> scene count
    
    Args:
        state: Current state
    
    Returns:
        Updated state with appearance counts
    """
    scenes = state['current_scenes']
    alias_index = state.get('alias_index', {})
    
    # For each scene, determine which characters appear
    characters_in_scenes = defaultdict(set)
    
    for scene in scenes:
        scene_text = scene['text']
        matches_by_char = find_all_alias_matches(scene_text, alias_index, case_sensitive=False)
        
        # Any character with a match in this scene is considered present
        for char_id in matches_by_char.keys():
            characters_in_scenes[char_id].add(scene['scene_id'])
    
    # Count unique scenes per character
    chapter_appearances = {
        char_id: len(scene_ids)
        for char_id, scene_ids in characters_in_scenes.items()
    }
    
    updated_state: BookState = {
        **state,
        'chapter_appearances_by_char': chapter_appearances,
    }
    
    return updated_state

