"""
LangGraph definition of the core PulseCast dialogue loop.

This module implements the podcast generation graph with nodes for:
- Researcher: Extracts knowledge points from source content
- Leo: Drafts engaging script sections as the visionary host
- Sarah: Responds with realistic grounding and caveats
- Director: Reviews, cleans, and decides APPROVE vs CONTINUE
"""

from __future__ import annotations

import re
from typing import Any, Dict, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from ..llm import get_llm
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
    knowledge_points_list: list[str]
    covered_points: list[str]
    script: str
    script_version: int
    status: str
    current_step: str
    progress_pct: int
    turn_count: int
    min_words: int
    critique_count: int
    critique_limit: int
    director_decision: str
    error_message: str
    audio_segments: list[dict]
    final_podcast_url: str
    duration_seconds: float


def _get_llm():
    """Get the LLM client from the factory."""
    return get_llm()


def _state_to_graph(state: PodcastState) -> GraphState:
    """Convert PodcastState to GraphState."""
    return GraphState(
        job_id=state.id,
        source_url=state.source_url,
        source_title=state.source_title or "",
        source_markdown=state.source_markdown or "",
        knowledge_points=state.knowledge_points or "",
        knowledge_points_list=[],
        covered_points=[],
        script=state.script or "",
        script_version=state.script_version,
        status=state.status.value,
        current_step=state.current_step.value,
        progress_pct=state.progress_pct,
        turn_count=0,
        min_words=1000,
        critique_count=state.critique_count,
        critique_limit=state.critique_limit,
        director_decision=state.director_decision.value
        if state.director_decision
        else "",
        error_message=state.error_message or "",
        audio_segments=[],
        final_podcast_url=state.final_podcast_url or "",
        duration_seconds=state.duration_seconds or 0.0,
    )


def _graph_to_state(graph_state: GraphState, base_state: PodcastState) -> PodcastState:
    """Convert GraphState back to PodcastState."""
    from ..models.state import AudioSegment as AudioSegmentModel

    audio_segments = None
    if graph_state.get("audio_segments"):
        audio_segments = [
            AudioSegmentModel(**seg) for seg in graph_state["audio_segments"]
        ]

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
        director_decision=DirectorDecision(graph_state["director_decision"])
        if graph_state["director_decision"]
        else None,
        error_message=graph_state["error_message"] or None,
        audio_segments=audio_segments,
        final_podcast_url=graph_state.get("final_podcast_url") or None,
        duration_seconds=graph_state.get("duration_seconds") or None,
    )


RESEARCHER_SYSTEM = """You are a research assistant. Extract the key knowledge points from the provided content.

Create a detailed beat-sheet with:
- 6-8 key points that capture the main ideas and insights
- Each point should be 1-2 sentences with enough detail to discuss
- Focus on facts, insights, notable examples, and actionable takeaways
- Include specific names, numbers, or details where relevant
- Stay strictly grounded in the source content - do not add external knowledge

Output format: List each point on a separate line prefixed with "- " (dash and space).
Example:
- First knowledge point with specific details and names
- Second knowledge point with specific details and names

Important: Each point should contain enough substance for a meaningful discussion."""


LEO_SYSTEM = """You are Leo, an enthusiastic podcast co-host who loves exploring ideas. You have genuine curiosity and bring energy to conversations.

YOUR VOICE:
- Speak naturally, like you're having a real conversation with a friend
- Use varied sentence structures - mix short punchy statements with longer flowing thoughts
- Let your enthusiasm show, but don't be over-the-top
- When excited, your sentences might run together a bit - that's natural
- React genuinely to what Sarah says - build on it, challenge it, or take it somewhere new

CRITICAL RULES:
1. STAY ON TOPIC - Only discuss the provided knowledge points. Do NOT introduce random topics like neural oscillations, cortisol, or unrelated concepts.
2. NO STAGE DIRECTIONS - Never write things like (smiling), (nodding), (laughing), [pause], etc.
3. NO REPETITION - Never repeat phrases like "That's a great point" or "Absolutely" or "Exactly" multiple times.
4. ONE SIGN-OFF ONLY - Only say goodbye ONCE at the very end of the entire podcast, not after each segment.
5. NO FALSE ENDINGS - Don't write "In conclusion" or "To wrap up" until the actual final segment.

KNOWLEDGE POINTS TO DISCUSS (these are your ONLY source of content):
{knowledge_points}

POINTS ALREADY COVERED (don't repeat these):
{covered_points}

CURRENT SCRIPT SO FAR:
{script}

Write a substantial, meaningful contribution. Focus on depth and natural conversation flow. Start with "LEO:" - remember you're having a natural conversation."""


SARAH_SYSTEM = """You are Sarah, a thoughtful podcast co-host who brings depth and nuance to conversations. You're not cynical, but you like to dig deeper.

YOUR VOICE:
- Speak naturally and conversationally
- Build on what Leo says - expand, question, or provide a different angle
- Use specific examples and concrete details
- Vary your sentence structure - don't fall into patterns
- React authentically - if Leo says something interesting, engage with it genuinely

CRITICAL RULES:
1. STAY ON TOPIC - Only discuss the provided knowledge points. Do NOT introduce random topics like neural oscillations, cortisol, or unrelated concepts.
2. NO STAGE DIRECTIONS - Never write things like (smiling), (nodding), (laughing), [pause], etc.
3. NO REPETITION - Never repeat phrases like "That's a great point" or "Absolutely" or "Exactly" multiple times.
4. ONE SIGN-OFF ONLY - Only say goodbye ONCE at the very end of the entire podcast, not after each segment.
5. NO FALSE ENDINGS - Don't write "In conclusion" or "To wrap up" until the actual final segment.

KNOWLEDGE POINTS TO DISCUSS (these are your ONLY source of content):
{knowledge_points}

POINTS ALREADY COVERED (don't repeat these):
{covered_points}

CURRENT SCRIPT SO FAR:
{script}

Write a substantial, meaningful contribution. Focus on depth and natural conversation flow. Start with "SARAH:" - remember you're having a natural conversation."""


DIRECTOR_SYSTEM = """You are a podcast director reviewing the script.

APPROVAL CRITERIA (in order of priority):
1. COVERAGE: Have most knowledge points (75%+) been discussed with substance?
2. QUALITY: No repetition, no topic drift, no stage directions, no false endings
3. MINIMUM LENGTH: Script should be at least 1000 words (no upper limit - let coverage determine length)

CRITICAL QUALITY CHECKS:
- TOPIC DRIFT: Are the hosts discussing ONLY the provided knowledge points? Reject if they've drifted to unrelated topics.
- REPETITION: Are there repeated phrases like "That's a great point", "Absolutely" appearing 3+ times? Reject.
- FALSE ENDINGS: Are there multiple "In conclusion" or "To wrap up" sections? There should only be ONE ending.
- STAGE DIRECTIONS: Are there parentheticals like (smiling), (nodding)? These should not exist.

KNOWLEDGE POINTS (hosts should ONLY discuss these):
{knowledge_points}

POINTS ALREADY DISCUSSED:
{covered_points}

WORD COUNT: {word_count} (minimum: 1000)

If quality issues exist (drift, repetition, false endings, stage directions), output:
"ISSUES: [list problems]"

If coverage is incomplete OR word count is below 1000, output:
"CONTINUE: [which knowledge points need discussion]"

If coverage is good (75%+), word count >= 1000, and no quality issues, output:
"APPROVE"

Script to review:
{script}"""


def _parse_knowledge_points(knowledge_points_text: str) -> list[str]:
    """Parse knowledge points text into a list of individual points."""
    points = []
    for line in knowledge_points_text.strip().split("\n"):
        line = line.strip()
        if line.startswith("- "):
            points.append(line[2:])
        elif line.startswith("• "):
            points.append(line[2:])
        elif line and not line.startswith("#"):
            points.append(line)
    return points


def _extract_key_phrases(text: str) -> list[str]:
    """Extract meaningful key phrases from text for matching."""
    text_lower = text.lower()

    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "they",
        "them",
        "their",
        "we",
        "us",
        "our",
        "you",
        "your",
        "he",
        "him",
        "his",
        "she",
        "her",
        "i",
        "me",
        "my",
        "what",
        "which",
        "who",
        "whom",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "not",
        "only",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "also",
        "now",
        "here",
        "there",
        "then",
        "once",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "again",
        "further",
        "any",
        "if",
        "as",
    }

    words = re.findall(r"\b[a-z]{3,}\b", text_lower)
    key_words = [w for w in words if w not in stop_words]

    phrases = re.findall(r"\b[a-z]+(?:\s+[a-z]+)*\b", text_lower)
    meaningful_phrases = []
    for phrase in phrases:
        words_in_phrase = phrase.split()
        if len(words_in_phrase) >= 2:
            meaningful_count = sum(1 for w in words_in_phrase if w not in stop_words)
            if meaningful_count >= 2:
                meaningful_phrases.append(phrase)

    return key_words + meaningful_phrases


def _detect_covered_points(script: str, knowledge_points_list: list[str]) -> list[str]:
    """Detect which knowledge points have been meaningfully discussed in the script."""
    covered = []
    script_lower = script.lower()

    script_key_phrases = set(_extract_key_phrases(script))

    for point in knowledge_points_list:
        point_lower = point.lower()
        point_phrases = _extract_key_phrases(point)

        if not point_phrases:
            continue

        phrase_matches = sum(1 for phrase in point_phrases if phrase in script_lower)

        exact_phrase_matches = 0
        for phrase in point_phrases:
            if " " in phrase and phrase in script_lower:
                exact_phrase_matches += 1

        coverage_score = (phrase_matches / len(point_phrases)) + (
            exact_phrase_matches * 0.5
        )

        if coverage_score >= 0.6:
            covered.append(point)

    return covered


def _detect_repetition(script: str) -> list[str]:
    """Detect repeated phrases that indicate robotic dialogue."""
    issues = []

    repetitive_patterns = [
        r"\b(that\'s a great point|absolutely|exactly|great point|good point)\b",
        r"\b(well,? i think|i think that|i\'d like to add)\b",
        r"\b(as we wrap up|in conclusion|to conclude|to wrap up)\b",
        r"\b(thank you for|it\'s been (a|an) (absolute|great) pleasure)\b",
        r"\b(let\'s (dive|explore|continue|talk))\b",
    ]

    script_lower = script.lower()

    for pattern in repetitive_patterns:
        matches = re.findall(pattern, script_lower)
        if len(matches) >= 3:
            issues.append(
                f"Repetitive phrase '{matches[0]}' appears {len(matches)} times"
            )

    return issues


def _detect_quality_issues(script: str) -> list[str]:
    """Detect various quality issues in the script."""
    issues = []

    stage_directions = re.findall(r"\([^)]+\)", script)
    if stage_directions:
        issues.append(
            f"Found {len(stage_directions)} stage directions like '(smiling)', '(nodding)' - these should be removed"
        )

    false_endings = len(
        re.findall(
            r"\b(in conclusion|to wrap up|as we conclude|concluding|to conclude)\b",
            script.lower(),
        )
    )
    if false_endings >= 2:
        issues.append(
            f"Found {false_endings} false ending phrases - should only have ONE conclusion"
        )

    goodbye_count = len(
        re.findall(
            r"\b(thank you for (joining|listening|being)|thanks for (joining|listening|being))\b",
            script.lower(),
        )
    )
    if goodbye_count >= 2:
        issues.append(
            f"Found {goodbye_count} goodbye/sign-off sections - should only have ONE at the very end"
        )

    drift_keywords = [
        "neural oscillation",
        "cortisol",
        "mirror neuron",
        "dopamine",
        "brainwave entrainment",
        "embodied cognition",
        "mental time travel",
        "neural synchrony",
    ]
    for keyword in drift_keywords:
        if keyword in script.lower():
            issues.append(
                f"Possible topic drift: '{keyword}' detected - ensure this relates to the source content"
            )

    return issues


def _count_words(script: str) -> int:
    """Count words in the script (excluding speaker prefixes and stage directions)."""
    clean_script = re.sub(r"\([^)]+\)", "", script)
    clean_script = re.sub(r"\[.*?\]", "", clean_script)
    clean_script = re.sub(r"(LEO:|SARAH:)", "", clean_script)
    words = clean_script.split()
    return len(words)


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
    knowledge_points_text = str(response.content).strip()
    knowledge_points_list = _parse_knowledge_points(knowledge_points_text)

    return {
        "knowledge_points": knowledge_points_text,
        "knowledge_points_list": knowledge_points_list,
        "covered_points": [],
        "current_step": CurrentStep.RESEARCHING.value,
        "progress_pct": 15,
        "turn_count": 0,
    }


async def leo_node(state: GraphState) -> Dict[str, Any]:
    """
    Draft engaging script content as Leo (visionary host).
    """
    llm = _get_llm()

    existing_script = state.get("script", "")
    knowledge_points_list = state.get("knowledge_points_list", [])
    covered_points = state.get("covered_points", [])
    turn_count = state.get("turn_count", 0)

    uncovered_points = [p for p in knowledge_points_list if p not in covered_points]
    covered_points_str = (
        "\n".join(f"- {p}" for p in covered_points) if covered_points else "None yet"
    )
    uncovered_points_str = (
        "\n".join(f"- {p}" for p in uncovered_points)
        if uncovered_points
        else "All major points covered - provide a brief conclusion"
    )

    if not existing_script:
        intro_prompt = """Start the podcast with a natural, engaging intro.
Introduce yourselves briefly as Leo and Sarah, hook the listener with why this topic matters, 
then dive into discussing ONE specific knowledge point in depth.
Start your lines with "LEO:" and write like you're actually talking to someone."""
    else:
        quality_issues = _detect_quality_issues(existing_script)
        repetition_issues = _detect_repetition(existing_script)
        all_issues = quality_issues + repetition_issues

        issues_warning = ""
        if all_issues:
            issues_warning = f"""

IMPORTANT - Fix these issues in your response:
{chr(10).join(f"- {issue}" for issue in all_issues[:3])}"""

        if uncovered_points:
            intro_prompt = f"""Continue the conversation naturally.
Pick ONE uncovered knowledge point and discuss it in depth. Quote specific details from it.
Do NOT introduce new topics outside the knowledge points.{issues_warning}

UNCOVERED POINTS TO DISCUSS:
{uncovered_points_str}"""
        else:
            intro_prompt = f"""Provide a natural conclusion.
Summarize the key insights discussed. Say goodbye naturally ONCE - don't repeat sign-offs.
This is the FINAL segment of the podcast.{issues_warning}"""

    messages = [
        SystemMessage(
            content=LEO_SYSTEM.format(
                script=existing_script if existing_script else "(starting fresh)",
                knowledge_points=uncovered_points_str,
                covered_points=covered_points_str,
            )
        ),
        HumanMessage(content=intro_prompt),
    ]

    response = await llm.ainvoke(messages)
    new_lines = str(response.content).strip()

    if existing_script:
        script = existing_script + "\n\n" + new_lines
    else:
        script = new_lines

    updated_covered = _detect_covered_points(script, knowledge_points_list)

    return {
        "script": script,
        "covered_points": updated_covered,
        "turn_count": turn_count + 1,
        "current_step": CurrentStep.SCRIPTING.value,
        "progress_pct": min(80, 25 + turn_count * 8),
    }


async def sarah_node(state: GraphState) -> Dict[str, Any]:
    """
    Add Sarah's responses to the script.
    """
    llm = _get_llm()

    existing_script = state.get("script", "")
    knowledge_points_list = state.get("knowledge_points_list", [])
    covered_points = state.get("covered_points", [])
    turn_count = state.get("turn_count", 0)

    uncovered_points = [p for p in knowledge_points_list if p not in covered_points]
    covered_points_str = (
        "\n".join(f"- {p}" for p in covered_points) if covered_points else "None yet"
    )
    uncovered_points_str = (
        "\n".join(f"- {p}" for p in uncovered_points)
        if uncovered_points
        else "All major points covered - help conclude naturally"
    )

    quality_issues = _detect_quality_issues(existing_script)
    repetition_issues = _detect_repetition(existing_script)
    all_issues = quality_issues + repetition_issues

    issues_warning = ""
    if all_issues:
        issues_warning = f"""

IMPORTANT - Avoid these issues seen in the script:
{chr(10).join(f"- {issue}" for issue in all_issues[:3])}"""

    if uncovered_points:
        continue_prompt = f"""Respond naturally to what Leo said.
Pick ONE uncovered knowledge point and add depth or a different perspective. Quote specific details.
Do NOT introduce topics outside the knowledge points.{issues_warning}

UNCOVERED POINTS TO DISCUSS:
{uncovered_points_str}"""
    else:
        continue_prompt = f"""Help provide a natural conclusion.
Build on Leo's conclusion naturally. Don't repeat sign-offs.
This is the FINAL segment.{issues_warning}"""

    messages = [
        SystemMessage(
            content=SARAH_SYSTEM.format(
                script=existing_script,
                knowledge_points=uncovered_points_str,
                covered_points=covered_points_str,
            )
        ),
        HumanMessage(content=continue_prompt),
    ]

    response = await llm.ainvoke(messages)
    new_lines = str(response.content).strip()

    script = existing_script + "\n\n" + new_lines

    updated_covered = _detect_covered_points(script, knowledge_points_list)

    return {
        "script": script,
        "covered_points": updated_covered,
        "turn_count": turn_count + 1,
        "progress_pct": min(85, 30 + turn_count * 8),
    }


async def director_node(state: GraphState) -> Dict[str, Any]:
    """
    Review the script and decide APPROVE or CONTINUE.
    Coverage-first approach with 1000-word minimum floor.
    """
    llm = _get_llm()

    script = state["script"]
    knowledge_points_list = state.get("knowledge_points_list", [])
    min_words = state.get("min_words", 1000)
    turn_count = state.get("turn_count", 0)

    word_count = _count_words(script)
    updated_covered = _detect_covered_points(script, knowledge_points_list)
    uncovered_points = [p for p in knowledge_points_list if p not in updated_covered]

    quality_issues = _detect_quality_issues(script)
    repetition_issues = _detect_repetition(script)
    all_quality_issues = quality_issues + repetition_issues

    knowledge_points_str = (
        "\n".join(f"- {p}" for p in knowledge_points_list)
        if knowledge_points_list
        else "None"
    )
    covered_points_str = (
        "\n".join(f"- {p}" for p in updated_covered) if updated_covered else "None yet"
    )

    coverage_ratio = (
        len(updated_covered) / len(knowledge_points_list)
        if knowledge_points_list
        else 1.0
    )

    pause_script = _add_pauses(script)

    max_turns = 16
    if turn_count >= max_turns:
        return {
            "script": pause_script,
            "director_decision": DirectorDecision.APPROVE.value,
            "script_version": state["script_version"] + 1,
            "covered_points": updated_covered,
            "current_step": CurrentStep.DIRECTOR.value,
            "progress_pct": 85,
            "error_message": f"Reached max turns ({max_turns}). Auto-approved with {coverage_ratio:.0%} coverage, {word_count} words.",
        }

    if len(all_quality_issues) >= 3:
        guidance = "Quality issues detected: " + "; ".join(all_quality_issues[:3])
        if uncovered_points:
            guidance += f"\n\nStill need to cover: {', '.join(uncovered_points[:2])}"

        return {
            "script": pause_script,
            "director_decision": DirectorDecision.CONTINUE.value,
            "covered_points": updated_covered,
            "current_step": CurrentStep.DIRECTOR.value,
            "error_message": guidance,
        }

    has_good_coverage = coverage_ratio >= 0.75
    meets_min_words = word_count >= min_words

    if has_good_coverage and meets_min_words:
        messages = [
            SystemMessage(
                content=DIRECTOR_SYSTEM.format(
                    script=pause_script,
                    knowledge_points=knowledge_points_str,
                    covered_points=covered_points_str,
                    word_count=word_count,
                    min_words=min_words,
                )
            ),
            HumanMessage(
                content="Review this script for final approval. If quality is good, output APPROVE."
            ),
        ]

        response = await llm.ainvoke(messages)
        decision_text = str(response.content).strip()

        if "ISSUES:" in decision_text.upper():
            guidance = decision_text.replace("ISSUES:", "").strip()
            return {
                "script": pause_script,
                "director_decision": DirectorDecision.CONTINUE.value,
                "covered_points": updated_covered,
                "current_step": CurrentStep.DIRECTOR.value,
                "error_message": guidance,
            }

        return {
            "script": pause_script,
            "director_decision": DirectorDecision.APPROVE.value,
            "script_version": state["script_version"] + 1,
            "covered_points": updated_covered,
            "current_step": CurrentStep.DIRECTOR.value,
            "progress_pct": 85,
        }

    guidance_parts = []
    if not has_good_coverage:
        guidance_parts.append(f"Coverage at {coverage_ratio:.0%}, need 75%+")
        if uncovered_points:
            guidance_parts.append(f"Uncovered: {', '.join(uncovered_points[:3])}")
    if not meets_min_words:
        guidance_parts.append(f"Word count at {word_count}, need {min_words}+")

    guidance = "\n".join(guidance_parts)

    return {
        "script": pause_script,
        "director_decision": DirectorDecision.CONTINUE.value,
        "covered_points": updated_covered,
        "current_step": CurrentStep.DIRECTOR.value,
        "error_message": guidance,
    }


def _add_pauses(script: str) -> str:
    """Add natural pauses to the script."""
    lines = script.split("\n")
    result = []

    for i, line in enumerate(lines):
        result.append(line)
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if next_line and (
                next_line.startswith("LEO:") or next_line.startswith("SARAH:")
            ):
                current_speaker = line.strip()[:3] if line.strip() else ""
                next_speaker = next_line[:3]
                if current_speaker != next_speaker and current_speaker in (
                    "LEO",
                    "SAR",
                ):
                    result.append("")
                    result.append("[pause: 500ms]")
                    result.append("")

    return "\n".join(result)


async def audio_node(state: GraphState) -> Dict[str, Any]:
    """
    Generate audio from the approved script.

    This node runs after the director approves the script.
    It synthesizes TTS audio for each segment and combines
    them into a final podcast file.
    """
    import logging

    from ..services.audio import synthesize_podcast_audio

    logger = logging.getLogger(__name__)

    job_id = state["job_id"]
    script = state["script"]

    logger.info(f"Starting audio synthesis for job {job_id}")

    try:
        result = await synthesize_podcast_audio(script, job_id)

        audio_segments = [
            {
                "speaker": seg.speaker,
                "text": seg.text,
                "audio_url": seg.audio_url,
            }
            for seg in result.segments
        ]

        logger.info(f"Audio synthesis complete: {result.final_url}")

        return {
            "audio_segments": audio_segments,
            "final_podcast_url": result.final_url or "",
            "duration_seconds": result.duration_seconds,
            "current_step": CurrentStep.COMPLETED.value,
            "progress_pct": 100,
            "status": JobStatus.COMPLETED.value,
        }
    except Exception as e:
        logger.error(f"Audio synthesis failed: {e}")
        return {
            "error_message": f"Audio synthesis failed: {str(e)}",
            "current_step": CurrentStep.AUDIO.value,
            "status": JobStatus.FAILED.value,
        }


def _should_continue(state: GraphState) -> Literal["leo", "audio", "end"]:
    """Determine if we should loop back to leo, go to audio, or end."""
    decision = state.get("director_decision")

    if decision == DirectorDecision.APPROVE.value:
        return "audio"

    if decision == DirectorDecision.CONTINUE.value:
        return "leo"

    return "leo"


def create_podcast_graph() -> StateGraph:
    """Create the LangGraph for podcast generation."""
    graph = StateGraph(GraphState)

    graph.add_node("researcher", researcher_node)
    graph.add_node("leo", leo_node)
    graph.add_node("sarah", sarah_node)
    graph.add_node("director", director_node)
    graph.add_node("audio", audio_node)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "leo")
    graph.add_edge("leo", "sarah")
    graph.add_edge("sarah", "director")

    graph.add_conditional_edges(
        "director",
        _should_continue,
        {
            "leo": "leo",
            "audio": "audio",
        },
    )

    graph.add_edge("audio", END)

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
