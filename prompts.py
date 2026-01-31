"""Prompt templates for LLM-based nodes.

This module contains all prompt templates used by nodes that invoke LLMs:
- EntityRosterUpdate (character detection and alias resolution)
- InfluenceExtractor (influence evidence extraction)
- BookSynthesis (dossier creation)
- Ranker (influence ranking)
"""

# Prompt version tracking
PROMPT_VERSION = "1.0.0"


def get_entity_roster_prompt(existing_characters: dict, scene_chunk: list) -> str:
    """Generate prompt for entity roster update (character detection).
    
    Args:
        existing_characters: Existing character profiles
        scene_chunk: List of scenes in the current chunk being processed
    
    Returns:
        Prompt string
    """
    existing_chars_str = ""
    if existing_characters:
        existing_chars_str = "Existing characters:\n"
        for char_id, char in existing_characters.items():
            existing_chars_str += f"- {char['canonical_name']} (ID: {char_id})\n"
            if char.get('aliases'):
                existing_chars_str += f"  Aliases: {', '.join(char['aliases'])}\n"
    
    # Build scenes text (all scenes, no truncation)
    scenes_str = "\n\n".join([
        f"Scene {i+1} ({scene['scene_id']}):\n{scene['text']}"
        for i, scene in enumerate(scene_chunk)
    ])
    
    return f"""You are analyzing scenes from a book chapter to identify and track characters.

{existing_chars_str}

Scenes from this chapter:
{scenes_str}

Tasks:
1. Identify any NEW characters introduced in these scenes
2. Identify any NEW aliases/nicknames for existing characters
3. Resolve ambiguous references where possible using context

For each character, provide:
- canonical_name: The primary name used for this character
- aliases: List of nicknames, titles, or alternative names
- notes: Brief notes about traits, relationships, or context

Output JSON in this format:
{{
  "new_characters": [
    {{
      "canonical_name": "Character Name",
      "aliases": ["Alias1", "Alias2"],
      "notes": ["Note1", "Note2"]
    }}
  ],
  "alias_updates": [
    {{
      "character_id": "existing_char_id",
      "new_aliases": ["NewAlias1", "NewAlias2"]
    }}
  ],
  "ambiguous_references": [
    {{
      "alias": "ambiguous_name",
      "candidates": ["char_id1", "char_id2"],
      "context": "snippet of text",
      "reason": "why ambiguous"
    }}
  ]
}}
"""


def get_influence_extraction_prompt(scene_chunk: list, characters: dict) -> str:
    """Generate prompt for influence evidence extraction.
    
    Args:
        scene_chunk: List of scenes in the current chunk (all scenes, no truncation)
        characters: Character profiles
    
    Returns:
        Prompt string
    """
    chars_str = "\n".join([
        f"- {char['canonical_name']} (ID: {char_id})"
        for char_id, char in characters.items()
    ])
    
    # Build scenes text (all scenes in chunk, no truncation)
    scenes_str = "\n\n".join([
        f"Scene {i+1} ({scene['scene_id']}):\n{scene['text']}"
        for i, scene in enumerate(scene_chunk)
    ])
    
    return f"""Analyze the following scenes from a book chapter and extract influence evidence for each character.

Characters in this chapter:
{chars_str}

Scenes:
{scenes_str}

For each character that appears, extract structured influence evidence:

1. **Causal**: Events they trigger or decisions they make (e.g., "X triggers Y", "X decides Z")
2. **Social**: How they affect other characters (e.g., "X persuades A", "X intimidates B")
3. **World**: Changes to setting, rules, or stakes (e.g., "X changes rules/stakes/setting")
4. **Pacing**: How they affect story pacing (e.g., "X introduces conflict", "X resolves obstacle")
5. **Narrative Gravity**: How scenes/plot revolve around them (e.g., "scene centers on X", "plot follows X")

Output JSON in this format:
{{
  "chapter_id": "chapter_001",
  "character_evidence": {{
    "char_id_1": {{
      "signals": {{
        "causal": ["evidence1", "evidence2"],
        "social": ["evidence1"],
        "world": [],
        "pacing": ["evidence1"],
        "narrative_gravity": ["evidence1"]
      }},
      "salience_score": 0.8
    }}
  }}
}}

Only include characters that actually appear in these scenes. Be specific and concise in evidence descriptions.
"""


def get_book_synthesis_prompt(
    book_influence: dict,
    book_mentions: dict,
    characters_by_id: dict,
    chapter_summaries: dict
) -> str:
    """Generate prompt for book-wide synthesis into dossiers.
    
    Args:
        book_influence: Accumulated influence evidence per character
        book_mentions: Total mentions per character
        characters_by_id: All character profiles
        chapter_summaries: Chapter summaries for narrative context
    
    Returns:
        Prompt string
    """
    # Build summary of evidence for each character
    char_summaries = []
    for char_id, accumulator in book_influence.items():
        char = characters_by_id.get(char_id, {})
        char_name = char.get('canonical_name', 'Unknown')
        
        evidence_count = len(accumulator.get('evidence', []))
        mentions = book_mentions.get(char_id, 0)
        
        # Summarize evidence types
        evidence_summary = []
        for ev in accumulator.get('evidence', [])[:5]:  # First 5 chapters
            signals = ev.get('signals', {})
            signal_counts = {k: len(v) for k, v in signals.items()}
            evidence_summary.append(f"Chapter {ev.get('chapter_id', '?')}: {signal_counts}")
        
        char_summaries.append(f"""
Character: {char_name} (ID: {char_id})
- Mentions: {mentions}
- Evidence chapters: {evidence_count}
- Sample evidence: {evidence_summary[:2]}
""")
    
    # Build chapter summaries section
    chapter_summaries_str = ""
    if chapter_summaries:
        chapter_summaries_str = "\n\nChapter Summaries (for narrative context):\n"
        for chapter_id, summary in sorted(chapter_summaries.items()):
            chapter_summaries_str += f"\n{chapter_id}:\n{summary}\n"
    
    return f"""Synthesize book-wide character influence evidence into compact dossiers.

Character summaries:
{''.join(char_summaries)}
{chapter_summaries_str}

For each character, create a dossier with:
1. **arc_summary**: How they change/develop across the book
2. **relationships**: Key relationships, conflicts, or ties to other characters
3. **impact_summary**: How they move the plot, affect the world, or influence others
4. **key_evidence**: 5-10 most important evidence points distilled from all chapters
5. **uncertainties**: Any ambiguity notes from alias resolution

Also provide a **book_plot_summary**: A 2-3 paragraph summary of the overall plot and major themes.

Use the chapter summaries to understand narrative flow and context when creating dossiers.

Output JSON:
{{
  "book_plot_summary": "...",
  "character_dossiers": {{
    "char_id_1": {{
      "canonical_name": "...",
      "aliases": [...],
      "arc_summary": "...",
      "relationships": [...],
      "impact_summary": "...",
      "key_evidence": [...],
      "uncertainties": [...]
    }}
  }}
}}

Keep dossiers concise but comprehensive. Focus on influence and impact, not just frequency.
"""


def get_chapter_summary_prompt(previous_summary: str, scene_chunk: list) -> str:
    """Generate prompt for chapter summarization.
    
    Args:
        previous_summary: Previous summary of the chapter (empty string if first chunk)
        scene_chunk: List of scenes in the current chunk being processed
    
    Returns:
        Prompt string
    """
    # Build scenes text (all scenes, no truncation)
    scenes_str = "\n\n".join([
        f"Scene {i+1} ({scene['scene_id']}):\n{scene['text']}"
        for i, scene in enumerate(scene_chunk)
    ])
    
    previous_summary_section = ""
    if previous_summary:
        previous_summary_section = f"""
Previous summary of this chapter:
{previous_summary}

"""
    
    return f"""You are summarizing a book chapter incrementally as scenes are processed.

{previous_summary_section}New scenes to incorporate:
{scenes_str}

Your task:
- If this is the first chunk (no previous summary), create an initial summary
- If there's a previous summary, extend/update it to include these new scenes
- Keep the summary concise (2-4 sentences) but comprehensive
- Focus on key events, character actions, and narrative developments
- Maintain continuity with the previous summary if it exists

Output JSON in this format:
{{
  "chapter_summary": "Your updated summary of the chapter up to this point..."
}}
"""


def get_ranker_prompt(
    book_plot_summary: str,
    character_dossiers: dict,
    book_mentions: dict
) -> str:
    """Generate prompt for subjective influence ranking.
    
    Args:
        book_plot_summary: Overall plot summary
        character_dossiers: Character dossiers
        book_mentions: Mention counts (reference only)
    
    Returns:
        Prompt string
    """
    dossiers_str = "\n\n".join([
        f"""Character: {dossier.get('canonical_name', 'Unknown')} (ID: {char_id})
Aliases: {', '.join(dossier.get('aliases', []))}
Mentions: {book_mentions.get(char_id, 0)}
Arc: {dossier.get('arc_summary', 'N/A')}
Relationships: {', '.join(dossier.get('relationships', []))}
Impact: {dossier.get('impact_summary', 'N/A')}
Key Evidence: {chr(10).join('- ' + e for e in dossier.get('key_evidence', [])[:5])}
"""
        for char_id, dossier in character_dossiers.items()
    ])
    
    return f"""Rank characters by their overall influence throughout the book.

Book Plot Summary:
{book_plot_summary}

Character Dossiers:
{dossiers_str}

**Important**: Influence is NOT the same as frequency. Consider:
- How they affect other characters (social impact)
- How they affect the world/stakes/rules
- How they affect pacing (initiate/accelerate/resolve conflicts)
- Narrative gravity (scenes revolve around them)
- Causal responsibility for major events

Mention counts are provided for reference only. Do not rank solely by frequency.

Rank all characters from most influential (rank 1) to least influential.

Output JSON array:
[
  {{
    "rank": 1,
    "character_id": "char_id",
    "name": "Canonical Name",
    "aliases": ["alias1", "alias2"],
    "mentioned_count": 310,
    "influence_summary": "Brief summary of their influence across the book",
    "ranking_rationale": "Why this character ranks at this position"
  }}
]

Ensure ranks are unique and sequential (1, 2, 3, ...).
"""

