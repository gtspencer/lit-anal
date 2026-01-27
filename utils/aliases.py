"""Alias matching and character resolution utilities."""

import re
from typing import Set, List, Optional, Tuple
from collections import defaultdict


def find_alias_matches(text: str, alias: str, case_sensitive: bool = False) -> List[Tuple[int, int]]:
    """Find all occurrences of an alias in text.
    
    Args:
        text: Text to search
        alias: Alias to find (can be multi-word)
        case_sensitive: Whether matching should be case-sensitive
    
    Returns:
        List of (start, end) tuples for each match
    """
    pattern = re.escape(alias)
    
    if case_sensitive:
        matches = list(re.finditer(pattern, text))
    else:
        flags = re.IGNORECASE
        matches = list(re.finditer(pattern, text, flags))
    
    return [(m.start(), m.end()) for m in matches]


def find_all_alias_matches(
    text: str,
    alias_index: dict[str, Set[str]],
    case_sensitive: bool = False
) -> dict[str, List[Tuple[int, int]]]:
    """Find all alias matches in text, grouped by character ID.
    
    Args:
        text: Text to search
        alias_index: Maps alias -> set of char_ids
        case_sensitive: Whether matching should be case-sensitive
    
    Returns:
        Dict mapping char_id -> list of (start, end) match positions
    """
    results = defaultdict(list)
    
    for alias, char_ids in alias_index.items():
        matches = find_alias_matches(text, alias, case_sensitive)
        for char_id in char_ids:
            results[char_id].extend(matches)
    
    return dict(results)


def resolve_ambiguous_alias(
    alias: str,
    candidates: Set[str],
    context: str,
    characters_by_id: dict
) -> Optional[str]:
    """Attempt to resolve an ambiguous alias using context.
    
    This is a simple heuristic-based resolver. For more sophisticated
    resolution, use an LLM-based disambiguation step.
    
    Args:
        alias: The ambiguous alias
        candidates: Set of candidate character IDs
        context: Context text around the alias
        characters_by_id: Character profiles for reference
    
    Returns:
        Resolved char_id if unambiguous, None if still ambiguous
    """
    if len(candidates) == 0:
        return None
    if len(candidates) == 1:
        return next(iter(candidates))
    
    # Simple heuristic: check if any candidate's canonical name or
    # other aliases appear in the context
    context_lower = context.lower()
    
    for char_id in candidates:
        char = characters_by_id.get(char_id)
        if not char:
            continue
        
        # Check canonical name
        if char['canonical_name'].lower() in context_lower:
            return char_id
        
        # Check other aliases
        for other_alias in char.get('aliases', []):
            if other_alias.lower() in context_lower and other_alias.lower() != alias.lower():
                return char_id
    
    # If still ambiguous, return None
    return None


def build_alias_index(characters_by_id: dict) -> dict[str, Set[str]]:
    """Build an alias index from character profiles.
    
    Args:
        characters_by_id: Dict mapping char_id -> CharacterProfile
    
    Returns:
        Dict mapping alias -> set of char_ids (can be ambiguous)
    """
    alias_index = defaultdict(set)
    
    for char_id, char in characters_by_id.items():
        # Add canonical name
        alias_index[char['canonical_name'].lower()].add(char_id)
        
        # Add all aliases
        for alias in char.get('aliases', []):
            alias_index[alias.lower()].add(char_id)
    
    return dict(alias_index)

