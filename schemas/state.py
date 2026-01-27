"""State schema definitions for the book character influence analyzer.

This module defines all TypedDict and Pydantic models used throughout the graph.
State is designed with three layers:
1) Book-level aggregates (persist across chapters)
2) Per-chapter scratch (reset per loop)
3) Indexing/alias/disambiguation structures
"""

from typing import TypedDict, Optional
from dataclasses import dataclass, field
from typing_extensions import NotRequired


class CharacterProfile(TypedDict):
    """Canonical character profile maintained across the book."""
    id: str
    canonical_name: str
    aliases: list[str]  # nicknames, titles, surname-only, etc.
    notes: list[str]  # disambiguation hints, traits, relationships


class UnresolvedAliasOccurrence(TypedDict):
    """Record of an ambiguous alias reference that couldn't be resolved."""
    chapter_id: str
    scene_id: Optional[str]
    alias: str
    span: NotRequired[Optional[tuple[int, int]]]  # optional if using offsets
    context: str  # short snippet
    candidates: list[str]  # candidate char_ids
    reason: str  # why ambiguous


class InfluenceSignals(TypedDict):
    """Structured influence evidence signals."""
    causal: list[str]  # "X triggers Y", "X decides Z"
    social: list[str]  # "X persuades A", "X intimidates B"
    world: list[str]  # "X changes rules/stakes/setting"
    pacing: list[str]  # "X introduces conflict", "X resolves obstacle"
    narrative_gravity: list[str]  # "scene centers on X", "plot follows X"


class InfluenceEvidence(TypedDict):
    """Influence evidence for a character in a single chapter."""
    chapter_id: str
    signals: InfluenceSignals
    salience_score: NotRequired[float]  # local estimate (chapter); optional


class InfluenceFeatureTotals(TypedDict):
    """Optional feature totals for debugging/analysis."""
    causal_events: int
    social_turns: int
    world_shifts: int
    pacing_beats: int
    centered_scenes: int


class InfluenceAccumulator(TypedDict):
    """Accumulated influence evidence for a character across the book."""
    evidence: list[InfluenceEvidence]
    feature_totals: NotRequired[InfluenceFeatureTotals]


class CharacterDossier(TypedDict):
    """Synthesized dossier for a character after processing all chapters."""
    canonical_name: str
    aliases: list[str]
    arc_summary: str  # how they change across book
    relationships: list[str]  # key ties/conflicts
    impact_summary: str  # how they move plot/world/others
    key_evidence: list[str]  # bullet evidence distilled from chapters
    uncertainties: list[str]  # ambiguity notes from alias resolution


class FinalCharacterResult(TypedDict):
    """Final ranked character result."""
    rank: int
    character_id: str
    name: str
    aliases: list[str]
    appeared_scenes: int
    mentioned_count: int
    influence_summary: str  # book-level
    ranking_rationale: NotRequired[Optional[str]]  # optional


class ChapterInput(TypedDict):
    """Input format for a single chapter."""
    chapter_id: str
    text: str


class Scene(TypedDict):
    """A scene within a chapter."""
    scene_id: str
    text: str


class BookState(TypedDict, total=False):
    """Main state object passed through the LangGraph.
    
    Fields marked as NotRequired are optional and may be added during processing.
    """
    # Book input and iteration
    chapters: list[ChapterInput]
    chapter_idx: int
    
    # Character canon
    characters_by_id: dict[str, CharacterProfile]
    alias_index: dict[str, set[str]]  # maps alias -> candidate char_ids
    unresolved_aliases: dict[str, list[UnresolvedAliasOccurrence]]
    
    # Book-level aggregates
    book_mentions: dict[str, int]  # char_id -> total mention hits
    book_appearances: dict[str, int]  # char_id -> total scenes appeared
    book_influence: dict[str, InfluenceAccumulator]
    chapter_summaries: NotRequired[list[dict]]  # optional debug trace
    
    # Per-chapter scratch (reset each chapter)
    current_chapter_id: str
    current_chapter_text: str
    current_scenes: list[Scene]
    chapter_mentions_by_char: dict[str, int]
    chapter_appearances_by_char: dict[str, int]
    chapter_influence_evidence: dict[str, InfluenceEvidence]
    
    # Synthesis + final outputs
    book_plot_summary: NotRequired[str]
    character_dossiers: NotRequired[dict[str, CharacterDossier]]
    final_ranked_characters: NotRequired[list[FinalCharacterResult]]
    ranking_run_metadata: NotRequired[dict]

