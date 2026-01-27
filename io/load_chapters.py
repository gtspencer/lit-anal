"""Load chapters from various input formats."""

import json
from typing import List, Dict
from pathlib import Path
from schemas.state import ChapterInput


def load_chapters_from_json(file_path: str) -> List[ChapterInput]:
    """Load chapters from a JSON file.
    
    Expected JSON format:
    [
      {
        "chapter_id": "chapter_001",
        "text": "Chapter text here..."
      },
      ...
    ]
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        List of chapter inputs
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of chapters")
    
    chapters = []
    for i, chapter in enumerate(data):
        if 'chapter_id' not in chapter:
            chapter['chapter_id'] = f"chapter_{i+1:03d}"
        if 'text' not in chapter:
            raise ValueError(f"Chapter {i} missing 'text' field")
        
        chapters.append({
            'chapter_id': chapter['chapter_id'],
            'text': chapter['text'],
        })
    
    return chapters


def load_chapters_from_directory(directory: str, pattern: str = "*.txt") -> List[ChapterInput]:
    """Load chapters from text files in a directory.
    
    Files are sorted by name and assigned sequential chapter IDs.
    
    Args:
        directory: Directory containing chapter text files
        pattern: Glob pattern for chapter files (default: "*.txt")
    
    Returns:
        List of chapter inputs
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise ValueError(f"Directory does not exist: {directory}")
    
    chapter_files = sorted(dir_path.glob(pattern))
    
    chapters = []
    for i, file_path in enumerate(chapter_files):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        chapter_id = f"chapter_{i+1:03d}"
        chapters.append({
            'chapter_id': chapter_id,
            'text': text,
        })
    
    return chapters


def load_chapters_from_single_file(file_path: str, separator: str = "\n\n---\n\n") -> List[ChapterInput]:
    """Load chapters from a single file with a separator.
    
    Args:
        file_path: Path to text file
        separator: String that separates chapters
    
    Returns:
        List of chapter inputs
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chapter_texts = content.split(separator)
    
    chapters = []
    for i, text in enumerate(chapter_texts):
        text = text.strip()
        if not text:
            continue
        
        chapter_id = f"chapter_{i+1:03d}"
        chapters.append({
            'chapter_id': chapter_id,
            'text': text,
        })
    
    return chapters

