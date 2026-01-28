"""LangSmith integration for end-to-end tracing and debugging.

This module provides a thin wrapper around LangGraph invocation to enable
tracing, tagging, and metadata collection for all runs.
"""

import os
from typing import Any, Optional, Dict

# Try to import CompiledGraph, but use Any as fallback for compatibility
try:
    from langgraph.graph import CompiledGraph
except ImportError:
    # CompiledGraph may not exist in all LangGraph versions
    # Use Any as type hint fallback
    CompiledGraph = Any


def invoke_with_tracing(
    app: CompiledGraph,
    inputs: Dict[str, Any],
    run_meta: Optional[Dict[str, Any]] = None,
    project_name: Optional[str] = None,
    tags: Optional[list[str]] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Invoke LangGraph app with LangSmith tracing enabled.
    
    Args:
        app: Compiled LangGraph application
        inputs: Input state for the graph
        run_meta: Run metadata (book_id, run_id, env, git_sha, etc.)
        project_name: LangSmith project name (defaults to env var or "book-influence-dev")
        tags: Additional tags to attach (e.g., ["book:book_001", "run:run_001"])
        extra_metadata: Additional metadata to attach
        thread_id: Thread ID for grouping related runs in LangSmith (defaults to run_id from run_meta)
    
    Returns:
        Graph execution result
    """
    # Calculate recursion limit based on number of chapters
    # Each chapter requires one loop iteration, plus buffer for init/finalization
    num_chapters = len(inputs.get('chapters', []))
    if num_chapters > 0:
        # Set limit to 2x number of chapters to be safe
        # (accounts for init, finalization, and some buffer)
        recursion_limit = num_chapters * 2
    else:
        # Default fallback if chapters not in inputs
        recursion_limit = int(os.getenv("LANGSMITH_RECURSION_LIMIT", "100"))
    
    # Check if tracing is enabled
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    
    # Build config with recursion limit (always set, even if tracing disabled)
    config = {
        "recursion_limit": recursion_limit
    }
    
    if not tracing_enabled:
        # If tracing disabled, just invoke with recursion limit
        return app.invoke(inputs, config=config)
    
    # Set project name
    if project_name:
        config["langsmith_project"] = project_name
    elif os.getenv("LANGSMITH_PROJECT"):
        config["langsmith_project"] = os.getenv("LANGSMITH_PROJECT")
    else:
        config["langsmith_project"] = "book-influence-dev"
    
    # Add thread_id for grouping runs in LangSmith
    if thread_id:
        config["thread_id"] = thread_id
    elif run_meta and run_meta.get("run_id"):
        # Auto-generate thread_id from run_id if not explicitly provided
        config["thread_id"] = run_meta["run_id"]
    
    # Add tags
    if tags:
        config["tags"] = tags
    else:
        config["tags"] = []
    
    # Add metadata
    metadata = {}
    if run_meta:
        metadata.update(run_meta)
    if extra_metadata:
        metadata.update(extra_metadata)
    
    if metadata:
        config["metadata"] = metadata
    
    # Recursion limit already set above, so invoke with full config
    return app.invoke(inputs, config=config)


def build_run_metadata(
    book_id: Optional[str] = None,
    run_id: Optional[str] = None,
    env: Optional[str] = None,
    git_sha: Optional[str] = None,
) -> Dict[str, Any]:
    """Build standard run metadata dictionary.
    
    Args:
        book_id: Identifier for the book being processed
        run_id: Unique identifier for this run
        env: Environment (dev/prod)
        git_sha: Git commit SHA
    
    Returns:
        Metadata dictionary
    """
    metadata = {}
    
    if book_id:
        metadata["book_id"] = book_id
    if run_id:
        metadata["run_id"] = run_id
    if env:
        metadata["env"] = env
    else:
        metadata["env"] = os.getenv("ENV", "dev")
    
    if git_sha:
        metadata["git_sha"] = git_sha
    
    return metadata


def build_tags(
    book_id: Optional[str] = None,
    run_id: Optional[str] = None,
    stage: Optional[str] = None,
) -> list[str]:
    """Build standard tags list.
    
    Args:
        book_id: Identifier for the book
        run_id: Unique identifier for this run
        stage: Stage (dev/prod)
    
    Returns:
        List of tags
    """
    tags = []
    
    if book_id:
        tags.append(f"book:{book_id}")
    if run_id:
        tags.append(f"run:{run_id}")
    if stage:
        tags.append(f"stage:{stage}")
    else:
        env = os.getenv("ENV", "dev")
        tags.append(f"stage:{env}")
    
    return tags

