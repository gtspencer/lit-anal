"""LangGraph assembly: wires nodes together with edges and conditional routing.

Graph flow:
Init -> LoadChapter -> SceneSegmenter -> EntityRosterUpdate -> MentionCounter ->
AppearanceCounter -> InfluenceExtractor -> BookAggregator -> NextChapter ->
(if next_chapter: loop to LoadChapter, else: BookSynthesis -> Ranker -> Done)
"""

from langgraph.graph import StateGraph, END
from schemas.state import BookState
from nodes.init import init_node
from nodes.load_chapter import load_chapter_node
from nodes.scene_segmenter import scene_segmenter_node
from nodes.entity_roster_update import entity_roster_update_node
from nodes.mention_counter import mention_counter_node
from nodes.appearance_counter import appearance_counter_node
from nodes.influence_extractor import influence_extractor_node
from nodes.book_aggregator import book_aggregator_node
from nodes.next_chapter import next_chapter_node
from nodes.book_synthesis import book_synthesis_node
from nodes.ranker import ranker_node


def create_graph() -> StateGraph:
    """Create and configure the LangGraph state machine.
    
    Returns:
        Configured StateGraph ready for execution
    """
    # Create graph
    workflow = StateGraph(BookState)
    
    # Add nodes
    workflow.add_node("init", init_node)
    workflow.add_node("load_chapter", load_chapter_node)
    workflow.add_node("scene_segmenter", scene_segmenter_node)
    workflow.add_node("entity_roster_update", entity_roster_update_node)
    workflow.add_node("mention_counter", mention_counter_node)
    workflow.add_node("appearance_counter", appearance_counter_node)
    workflow.add_node("influence_extractor", influence_extractor_node)
    workflow.add_node("book_aggregator", book_aggregator_node)
    workflow.add_node("next_chapter", next_chapter_node)
    workflow.add_node("book_synthesis", book_synthesis_node)
    workflow.add_node("ranker", ranker_node)
    
    # Set entry point
    workflow.set_entry_point("init")
    
    # Add edges
    workflow.add_edge("init", "load_chapter")
    workflow.add_edge("load_chapter", "scene_segmenter")
    workflow.add_edge("scene_segmenter", "entity_roster_update")
    workflow.add_edge("entity_roster_update", "mention_counter")
    workflow.add_edge("mention_counter", "appearance_counter")
    workflow.add_edge("appearance_counter", "influence_extractor")
    workflow.add_edge("influence_extractor", "book_aggregator")
    workflow.add_edge("book_aggregator", "next_chapter")
    
    # Conditional routing from next_chapter
    workflow.add_conditional_edges(
        "next_chapter",
        next_chapter_node,
        {
            "next_chapter": "load_chapter",
            "finalize": "book_synthesis",
        }
    )
    
    # Finalization path
    workflow.add_edge("book_synthesis", "ranker")
    workflow.add_edge("ranker", END)
    
    return workflow.compile()


def get_app():
    """Get the compiled graph application.
    
    Returns:
        Compiled LangGraph application
    """
    return create_graph()

