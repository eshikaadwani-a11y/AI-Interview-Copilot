"""Deterministic interview-answer evaluation (pure standard library).

Scores an answer along four dimensions — technical accuracy, communication,
completeness, and confidence — using transparent heuristics:

    technical      : coverage of category concept keywords
    communication  : structure (sentence count, length, connectors)
    completeness    : answer depth vs concept coverage
    confidence     : assertiveness (penalises hedging language)

These run with no dependencies so evaluation works offline; a configured LLM
can augment the qualitative feedback in the service layer.
"""

from __future__ import annotations

import re
from typing import Dict, List

# Concept keywords expected in a strong answer per category.
CONCEPT_KEYWORDS: Dict[str, List[str]] = {
    "DSA": ["complexity", "time", "space", "algorithm", "data structure", "hash",
            "tree", "graph", "array", "sort", "search", "stack", "queue", "pointer"],
    "OOP": ["class", "object", "inheritance", "polymorphism", "encapsulation",
            "abstraction", "interface", "composition", "method"],
    "DBMS": ["table", "index", "query", "normalization", "transaction", "acid",
             "join", "schema", "sql", "key", "relation"],
    "OS": ["process", "thread", "memory", "scheduling", "deadlock", "paging",
           "concurrency", "kernel", "synchronization"],
    "CN": ["tcp", "udp", "packet", "protocol", "dns", "http", "handshake",
           "ip", "routing", "latency"],
    "ML": ["model", "training", "feature", "overfitting", "accuracy", "precision",
           "recall", "gradient", "loss", "validation", "regularization", "bias", "variance"],
    "Projects": ["built", "designed", "implemented", "challenge", "team", "impact",
                 "decision", "trade-off", "scaled", "deployed"],
    "Behavioral": ["team", "conflict", "learned", "outcome", "resolved", "communicate"],
}

_HEDGES = ["maybe", "i think", "not sure", "i guess", "probably", "kind of",
           "sort of", "i'm not", "im not", "perhaps", "possibly", "might be"]
_ASSERTIVE = ["because", "specifically", "the reason", "in practice", "for example",
              "first", "second", "therefore", "as a result"]
_CONNECTORS = ["because", "therefore", "however", "so that", "in order to",
               "for example", "such as", "which means", "as a result"]

_SENTENCE_RE = re.compile(r"[.!?]+")
_WORD_RE = re.compile(r"[a-zA-Z0-9+#]+")


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def evaluate_answer(category: str, question: str, answer: str) -> Dict[str, object]:
    """Return a per-answer evaluation dict with sub-scores and feedback."""
    text = (answer or "").strip()
    lower = text.lower()
    words = _WORD_RE.findall(lower)
    word_count = len(words)
    sentences = [s for s in _SENTENCE_RE.split(text) if s.strip()]

    # ── Technical accuracy: concept-keyword coverage ──
    expected = CONCEPT_KEYWORDS.get(category, [])
    matched = sorted({kw for kw in expected if kw in lower})
    target = max(1, min(len(expected), 4))
    technical = _clamp(len(matched) / target * 100)

    # ── Communication: structure & readability ──
    comm = 0.0
    if word_count > 0:
        length_component = _clamp(word_count / 120 * 70, 0, 70)
        structure_component = _clamp(len(sentences) * 12, 0, 20)
        connector_bonus = 10 if any(c in lower for c in _CONNECTORS) else 0
        comm = _clamp(length_component + structure_component + connector_bonus)

    # ── Completeness: depth + concept coverage ──
    depth = _clamp(word_count / 150, 0, 1)
    concept_ratio = len(matched) / target
    completeness = _clamp((depth * 0.5 + min(concept_ratio, 1.0) * 0.5) * 100)

    # ── Confidence: assertiveness vs hedging ──
    confidence = 75.0
    confidence -= 9 * sum(lower.count(h) for h in _HEDGES)
    confidence += 5 * sum(1 for a in _ASSERTIVE if a in lower)
    if word_count < 15:
        confidence -= 25
    confidence = _clamp(confidence)

    overall = _clamp(
        0.40 * technical + 0.20 * comm + 0.25 * completeness + 0.15 * confidence
    )

    strengths, weaknesses, suggestions = _qualitative(
        category, technical, comm, completeness, confidence, matched, expected, word_count
    )

    return {
        "technical": round(technical, 1),
        "communication": round(comm, 1),
        "completeness": round(completeness, 1),
        "confidence": round(confidence, 1),
        "score": round(overall, 1),
        "matched_concepts": matched,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
    }


def _qualitative(category, technical, comm, completeness, confidence, matched, expected, word_count):
    strengths: List[str] = []
    weaknesses: List[str] = []
    suggestions: List[str] = []

    if technical >= 70:
        strengths.append("Strong grasp of the core technical concepts")
    elif technical < 50:
        weaknesses.append("Missed several expected technical concepts")
        missing = [kw for kw in expected if kw not in matched][:4]
        if missing:
            suggestions.append("Mention concepts like: " + ", ".join(missing) + ".")

    if comm >= 70:
        strengths.append("Clear, well-structured explanation")
    elif comm < 50:
        weaknesses.append("Answer could be clearer and better structured")
        suggestions.append("Structure your answer (definition → example → trade-offs).")

    if completeness < 50:
        weaknesses.append("Answer was a bit shallow")
        if word_count < 40:
            suggestions.append("Elaborate with more detail and a concrete example.")

    if confidence < 55:
        weaknesses.append("Hedging language reduced perceived confidence")
        suggestions.append("State your reasoning assertively; avoid 'maybe/I think'.")
    elif confidence >= 75:
        strengths.append("Confident, assertive delivery")

    if not strengths:
        strengths.append("Attempted the question and engaged with the topic")
    if not suggestions:
        suggestions.append("Solid answer — add a concrete example to make it stand out.")

    return strengths, weaknesses, suggestions
