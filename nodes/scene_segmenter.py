"""SceneSegmenter node: splits chapter text into scenes."""

from schemas.state import BookState
from utils.text import segment_scenes


def scene_segmenter_node(state: BookState) -> BookState:
    """Segment chapter text into scenes.
    
    Reads:
    - `current_chapter_text`: text of current chapter
    
    Writes:
    - `current_scenes`: list of scene dicts with 'scene_id' and 'text'
    
    Args:
        state: Current state
    
    Returns:
        Updated state with scenes segmented
    """
    chapter_text = state['current_chapter_text']
    
    scenes = segment_scenes(chapter_text)
    
    updated_state: BookState = {
        **state,
        'current_scenes': scenes,
    }
    
    return updated_state

