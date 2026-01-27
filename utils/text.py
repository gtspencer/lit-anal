"""Text processing utilities for scene segmentation and text manipulation."""

import re
from typing import List


def segment_scenes(text: str, max_scene_length: int = 5000) -> List[dict]:
    """Segment chapter text into scenes.
    
    Scene boundaries are detected by:
    - Double newlines (paragraph breaks)
    - Explicit markers (***, ---, etc.)
    - Chapter subheadings (lines starting with # or numbers)
    
    Args:
        text: The chapter text to segment
        max_scene_length: Maximum characters per scene (will split if exceeded)
    
    Returns:
        List of scene dicts with 'scene_id' and 'text' keys
    """
    scenes = []
    
    # First, split on explicit scene markers
    scene_markers = [
        r'\n\s*\*\*\*\s*\n',  # ***
        r'\n\s*---\s*\n',     # ---
        r'\n\s*###\s+',       # ### heading
    ]
    
    parts = [text]
    for marker in scene_markers:
        new_parts = []
        for part in parts:
            new_parts.extend(re.split(marker, part))
        parts = new_parts
    
    # Then split on double newlines
    all_parts = []
    for part in parts:
        all_parts.extend(re.split(r'\n\s*\n+', part))
    
    # Clean and create scenes
    scene_idx = 0
    for part in all_parts:
        part = part.strip()
        if not part:
            continue
        
        # If scene is too long, split further by paragraphs
        if len(part) > max_scene_length:
            paragraphs = re.split(r'\n+', part)
            current_scene = []
            current_length = 0
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                if current_length + len(para) > max_scene_length and current_scene:
                    # Save current scene
                    scenes.append({
                        'scene_id': f'scene_{scene_idx:03d}',
                        'text': '\n'.join(current_scene)
                    })
                    scene_idx += 1
                    current_scene = [para]
                    current_length = len(para)
                else:
                    current_scene.append(para)
                    current_length += len(para) + 1
            
            if current_scene:
                scenes.append({
                    'scene_id': f'scene_{scene_idx:03d}',
                    'text': '\n'.join(current_scene)
                })
                scene_idx += 1
        else:
            scenes.append({
                'scene_id': f'scene_{scene_idx:03d}',
                'text': part
            })
            scene_idx += 1
    
    # If no scenes were created, create one scene from entire text
    if not scenes:
        scenes.append({
            'scene_id': 'scene_000',
            'text': text.strip()
        })
    
    return scenes


def normalize_text(text: str) -> str:
    """Normalize text for matching (lowercase, strip whitespace)."""
    return text.lower().strip()


def extract_context(text: str, position: int, context_length: int = 100) -> str:
    """Extract context around a position in text.
    
    Args:
        text: The full text
        position: Character position
        context_length: Number of characters before/after to include
    
    Returns:
        Context snippet with ellipsis if truncated
    """
    start = max(0, position - context_length)
    end = min(len(text), position + context_length)
    
    snippet = text[start:end]
    if start > 0:
        snippet = '...' + snippet
    if end < len(text):
        snippet = snippet + '...'
    
    return snippet

