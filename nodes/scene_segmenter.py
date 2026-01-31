"""SceneSegmenter node: splits chapter text into scenes.
SceneChunker node: selects a batch of full scenes that fit within character limit."""

import os
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


def scene_chunker_node(state: BookState) -> BookState:
    """Select a batch of full scenes that fit within the character limit.
    
    This node selects as many complete scenes as possible without exceeding
    the character limit. Scenes are never truncated - only complete scenes
    are included in the chunk.
    
    Reads:
    - `current_scenes`: all scenes in current chapter
    - `processed_scene_ids`: set of scene IDs already processed
    
    Writes:
    - `current_scene_chunk`: list of scenes selected for this batch
    - `processed_scene_ids`: updated with newly selected scene IDs
    
    Args:
        state: Current state
    
    Returns:
        Updated state with scene chunk selected
    """
    chapter_id = state['current_chapter_id']
    all_scenes = state.get('current_scenes', [])
    processed_ids = state.get('processed_scene_ids', set())
    
    # Get character limit from environment
    max_chars = int(os.getenv("SCENE_CHUNK_MAX_CHARS", "5000"))
    
    logger.info(f"Selecting scene chunk for chapter {chapter_id} (max {max_chars} chars)")
    
    # Filter out already processed scenes
    remaining_scenes = [s for s in all_scenes if s['scene_id'] not in processed_ids]
    
    if not remaining_scenes:
        logger.info("No remaining scenes to process in this chapter")
        updated_state: BookState = {
            **state,
            'current_scene_chunk': [],
        }
        return updated_state
    
    # Select scenes sequentially until adding next would exceed limit
    selected_scenes = []
    total_chars = 0
    
    for scene in remaining_scenes:
        scene_chars = len(scene['text'])
        
        # If this is the first scene and it exceeds limit, include it anyway
        # (we never truncate scenes)
        if not selected_scenes and scene_chars > max_chars:
            logger.warning(
                f"Scene {scene['scene_id']} ({scene_chars} chars) exceeds limit ({max_chars}), "
                f"but including it anyway (no truncation)"
            )
            selected_scenes.append(scene)
            total_chars += scene_chars
            break
        
        # If adding this scene would exceed limit, stop
        if total_chars + scene_chars > max_chars:
            break
        
        # Add scene to chunk
        selected_scenes.append(scene)
        total_chars += scene_chars
    
    # Update processed scene IDs
    new_processed_ids = processed_ids | {s['scene_id'] for s in selected_scenes}
    
    logger.info(
        f"Selected {len(selected_scenes)} scenes ({total_chars} chars). "
        f"{len(new_processed_ids)}/{len(all_scenes)} scenes processed in chapter"
    )
    
    updated_state: BookState = {
        **state,
        'current_scene_chunk': selected_scenes,
        'processed_scene_ids': new_processed_ids,
    }
    
    return updated_state

