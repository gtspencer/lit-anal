"""LangSmith integration for end-to-end tracing and debugging.

This module provides a thin wrapper around LangGraph invocation to enable
tracing, tagging, and metadata collection for all runs.
"""

import os
from typing import Any, Optional, Dict
from langgraph.graph import CompiledGraph


def invoke_with_tracing(
    app: CompiledGraph,
    inputs: Dict[str, Any],
    run_meta: Optional[Dict[str, Any]] = None,
    project_name: Optional[str] = None,
    tags: Optional[list[str]] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Invoke LangGraph app with LangSmith tracing enabled.
    
    Args:
        app: Compiled LangGraph application
        inputs: Input state for the graph
        run_meta: Run metadata (book_id, run_id, env, git_sha, etc.)
        project_name: LangSmith project name (defaults to env var or "book-influence-dev")
        tags: Additional tags to attach (e.g., ["book:book_001", "run:run_001"])
        extra_metadata: Additional metadata to attach
    
    Returns:
        Graph execution result
    """
    # Check if tracing is enabled
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    
    if not tracing_enabled:
        # If tracing disabled, just invoke normally
        return app.invoke(inputs)
    
    # Build config with tags and metadata
    config = {}
    
    # Set project name
    if project_name:
        config["langsmith_project"] = project_name
    elif os.getenv("LANGSMITH_PROJECT"):
        config["langsmith_project"] = os.getenv("LANGSMITH_PROJECT")
    else:
        config["langsmith_project"] = "book-influence-dev"
    
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
    
    # Invoke with config
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

