"""
LangGraph definition of the core PulseCast dialogue loop.

This module implements the podcast generation graph with nodes for:
- Researcher: Extracts knowledge points from source content
- Leo: Drafts engaging script sections as the visionary host
- Sarah: Responds with realistic grounding and caveats
- Director: Reviews, cleans, and decides APPROVE vs REWRITE
"""

from __future__ import annotations

import os
from typing import Any, Dict, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from ..models.state import (
    CurrentStep,
    DirectorDecision,
    JobStatus,
    PodcastState,
)
from .checkpointer import get_checkpointer, make_thread_config


class GraphState(TypedDict):
    """State that flows through the LangGraph nodes."""

    job_id: str
    source_url: str
    source_title: str
    source_markdown: str
    knowledge_points: str
    script: str
    script_version: int
    status: str
    current_step: str
    progress_pct: int
    critique_count: int
    critique_limit: int
    director_decision: str
    error_message: str


def _get_llm() -> ChatOpenAI:
    """Get the LLM client."""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.7,
    )


def _state_to_graph(state: PodcastState) -> GraphState:
    """Convert PodcastState to GraphState."""
    return GraphState(
        job_id=state.id,
        source_url=state.source_url,
        source_title=state.source_title or "",
        source_markdown=state.source_markdown or "",
        knowledge_points=state.knowledge_points or "",
        script=state.script or "",
        script_version=state.script_version,
        status=state.status.value,
        current_step=state.current_step.value,
        progress_pct=state.progress_pct,
        critique_count=state.critique_count,
        critique_limit=state.critique_limit,
        director_decision=state.director_decision.value if state.director_decision else "",
        error_message=state.error_message or "",
    )


def _graph_to_state(graph_state: GraphState, base_state: PodcastState) -> PodcastState:
    """Convert GraphState back to PodcastState."""
    return PodcastState(
        id=base_state.id,
        source_url=base_state.source_url,
        source_title=graph_state["source_title"] or base_state.source_title,
        created_at=base_state.created_at,
        updated_at=base_state.updated_at,
        source_markdown=graph_state["source_markdown"] or base_state.source_markdown,
        knowledge_points=graph_state["knowledge_points"],
        script=graph_state["script"],
        script_version=graph_state["script_version"],
        status=JobStatus(graph_state["status"]),
        current_step=CurrentStep(graph_state["current_step"]),
        progress_pct=graph_state["progress_pct"],
        critique_count=graph_state["critique_count"],
        critique_limit=graph_state["critique_limit"],
        director_decision=DirectorDecision(graph_state["director_decision"]) if graph_state["director_decision"] else None,
        error_message=graph_state["error_message"] or None,
    )


RESEARCHER_SYSTEM = """You are a research assistant. Extract the key knowledge points from the provided content.

Create a concise beat-sheet with:
- 5-8 key points that capture the main ideas
- Each point should be a single sentence
- Focus on facts, insights, and notable details
- Be neutral and objective

Output format: Just list the points, one per line, no bullets or numbering."""


LEO_SYSTEM = """You are Leo, the enthusiastic and visionary podcast co-host. You see exciting possibilities and love to explore big ideas.

Guidelines:
- Start your lines with "LEO:"
- Be engaging, optimistic, and curious
- Use conversational language
- Reference knowledge points naturally
- Ask questions that spark discussion
- Keep each line to 1-3 sentences

Previous script (if any): {script}

Knowledge points to discuss:
{knowledge_points}"""


SARAH_SYSTEM = """You are Sarah, the grounded and realistic podcast co-host. You provide balance, caveats, and practical perspectives.

Guidelines:
- Start your lines with "SARAH:"
- Respond to Leo's points with nuance
- Add context, limitations, or alternative views
- Be conversational but thoughtful
- Keep each line to 1-3 sentences

Current script so far:
{script}"""


DIRECTOR_SYSTEM = """You are the podcast director. Review the script and decide if it's ready or needs revision.

Review criteria:
1. Has a clear intro that hooks the listener
2. Covers key knowledge points naturally
3. Both hosts contribute meaningfully
4. Has a conclusion that wraps up
5. No excessive repetition
6. Appropriate length (not too short, not too long)

Output ONLY one of:
- "APPROVE" if the script is ready
- "REWRITE: [brief reason]" if it needs revision

Script to review:
{script}"""


async def researcher_node(state: GraphState) -> Dict[str, Any]:
    """
    Extract knowledge points from the source content.

    Reads source_markdown and produces a beat-sheet of key points.
    """
    llm = _get_llm()

    messages = [
        SystemMessage(content=RESEARCHER_SYSTEM),
        HumanMessage(content=state["source_markdown"][:8000]),
    ]

    response = await llm.ainvoke(messages)
    knowledge_points = response.content.strip()

    return {
        "knowledge_points": knowledge_points,
        "current_step": CurrentStep.RESEARCHING.value,
        "progress_pct": 25,
    }


async def leo_node(state: GraphState) -> Dict[str, Any]:
    """
    Draft engaging script content as Leo (visionary host).

    Uses knowledge points to create conversational LEO: lines.
    """
    llm = _get_llm()

    existing_script = state.get("script", "")

    if not existing_script:
        intro_prompt = """Start the podcast with an engaging intro. Introduce yourselves as Leo and Sarah, 
mention the topic briefly, and kick off the discussion. Remember to start your lines with "LEO:"""

        messages = [
            SystemMessage(content=LEO_SYSTEM.format(
                script="(starting fresh)",
                knowledge_points=state["knowledge_points"]
            )),
            HumanMessage(content=intro_prompt),
        ]
    else:
        messages = [
            SystemMessage(content=LEO_SYSTEM.format(
                script=existing_script,
                knowledge_points=state["knowledge_points"]
            )),
            HumanMessage(content="Continue the podcast discussion. Add 1-2 LEO: lines that advance the conversation."),
        ]

    response = await llm.ainvoke(messages)
    new_lines = response.content.strip()

    if existing_script:
        script = existing_script + "\n\n" + new_lines
    else:
        script = new_lines

    return {
        "script": script,
        "current_step": CurrentStep.SCRIPTING.value,
        "progress_pct": 45,
    }


async def sarah_node(state: GraphState) -> Dict[str, Any]:
    """
    Add Sarah's responses to the script.

    Provides grounded, realistic counterpoints to Leo's enthusiasm.
    """
    llm = _get_llm()

    messages = [
        SystemMessage(content=SARAH_SYSTEM.format(script=state["script"])),
        HumanMessage(content="Add 1-2 SARAH: lines that respond to Leo and add depth to the discussion."),
    ]

    response = await llm.ainvoke(messages)
    new_lines = response.content.strip()

    script = state["script"] + "\n\n" + new_lines

    return {
        "script": script,
        "progress_pct": 60,
    }


async def director_node(state: GraphState) -> Dict[str, Any]:
    """
    Review the script and decide APPROVE or REWRITE.

    Adds pauses, checks for issues, and increments critique_count if needed.
    """
    llm = _get_llm()

    script = state["script"]

    pause_script = _add_pauses(script)

    messages = [
        SystemMessage(content=DIRECTOR_SYSTEM.format(script=pause_script)),
        HumanMessage(content="Review this script and decide: APPROVE or REWRITE with reason."),
    ]

    response = await llm.ainvoke(messages)
    decision_text = response.content.strip()

    if decision_text.upper().startswith("APPROVE"):
        return {
            "script": pause_script,
            "director_decision": DirectorDecision.APPROVE.value,
            "script_version": state["script_version"] + 1,
            "current_step": CurrentStep.DIRECTOR.value,
            "progress_pct": 85,
        }
    else:
        new_critique_count = state["critique_count"] + 1
        error_msg = decision_text.replace("REWRITE:", "").strip() if "REWRITE:" in decision_text else "Needs revision"

        if new_critique_count >= state["critique_limit"]:
            return {
                "script": pause_script,
                "director_decision": DirectorDecision.APPROVE.value,
                "script_version": state["script_version"] + 1,
                "critique_count": new_critique_count,
                "current_step": CurrentStep.DIRECTOR.value,
                "progress_pct": 85,
                "error_message": f"Reached critique limit. Auto-approved. Last feedback: {error_msg}",
            }

        return {
            "script": pause_script,
            "director_decision": DirectorDecision.REWRITE.value,
            "critique_count": new_critique_count,
            "current_step": CurrentStep.DIRECTOR.value,
            "error_message": error_msg,
        }


def _add_pauses(script: str) -> str:
    """Add natural pauses to the script."""
    lines = script.split("\n")
    result = []

    for i, line in enumerate(lines):
        result.append(line)
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if next_line and (next_line.startswith("LEO:") or next_line.startswith("SARAH:")):
                current_speaker = line.strip()[:3] if line.strip() else ""
                next_speaker = next_line[:3]
                if current_speaker != next_speaker and current_speaker in ("LEO", "SAR"):
                    result.append("")
                    result.append("[pause: 500ms]")
                    result.append("")

    return "\n".join(result)


def _should_continue(state: GraphState) -> Literal["leo", "end"]:
    """Determine if we should loop back to leo or end."""
    if state.get("director_decision") == DirectorDecision.APPROVE.value:
        return "end"
    return "leo"


def create_podcast_graph() -> StateGraph:
    """Create the LangGraph for podcast generation."""
    graph = StateGraph(GraphState)

    graph.add_node("researcher", researcher_node)
    graph.add_node("leo", leo_node)
    graph.add_node("sarah", sarah_node)
    graph.add_node("director", director_node)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "leo")
    graph.add_edge("leo", "sarah")
    graph.add_edge("sarah", "director")

    graph.add_conditional_edges(
        "director",
        _should_continue,
        {
            "leo": "leo",
            "end": END,
        },
    )

    return graph


class PodcastGraphRunner:
    """Runner for the podcast generation graph."""

    def __init__(self) -> None:
        self._graph = create_podcast_graph().compile(checkpointer=get_checkpointer())

    async def run(self, state: PodcastState) -> PodcastState:
        """Run the podcast generation graph."""
        graph_state = _state_to_graph(state)
        config = make_thread_config(state.id)

        final_state = await self._graph.ainvoke(graph_state, config)

        return _graph_to_state(final_state, state)

    async def get_current_state(self, job_id: str) -> dict | None:
        """Get the current graph state for a job from the checkpointer."""
        config = make_thread_config(job_id)
        snapshot = await self._graph.aget_state(config)
        if snapshot and snapshot.values:
            return snapshot.values
        return None


_graph_runner: PodcastGraphRunner | None = None


def get_graph_runner() -> PodcastGraphRunner:
    """Get the singleton graph runner."""
    global _graph_runner
    if _graph_runner is None:
        _graph_runner = PodcastGraphRunner()
    return _graph_runner
