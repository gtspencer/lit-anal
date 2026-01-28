"""SceneSegmenter node: splits chapter text into scenes."""

from schemas.state import BookState
from utils.text import segment_scenes
from utils.logging_config import get_logger

logger = get_logger()


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
    chapter_id = state['current_chapter_id']
    
    logger.info(f"Segmenting chapter {chapter_id} into scenes")
    scenes = segment_scenes(chapter_text)
    
    logger.info(f"Segmented into {len(scenes)} scenes")
    logger.debug(f"Scene IDs: {[s['scene_id'] for s in scenes]}")
    
    updated_state: BookState = {
        **state,
        'current_scenes': scenes,
    }
    
    return updated_state

