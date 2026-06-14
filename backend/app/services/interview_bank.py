"""Interview question bank and selection logic (pure standard library).

Provides a curated, categorised question bank plus deterministic question
selection and follow-up generation. ``interview_service`` layers persistence
and optional LLM-generated follow-ups on top of this.

Modes:      software_engineer | full_stack | ai_engineer | data_scientist
Categories: DSA, OOP, DBMS, OS, CN, ML, Projects, Behavioral
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

# Default category mix per interview mode.
MODE_CATEGORIES: Dict[str, List[str]] = {
    "software_engineer": ["DSA", "OOP", "OS", "DBMS", "CN", "Projects", "Behavioral"],
    "full_stack": ["DSA", "OOP", "DBMS", "CN", "Projects", "Behavioral"],
    "ai_engineer": ["ML", "DSA", "OOP", "Projects", "Behavioral"],
    "data_scientist": ["ML", "DBMS", "DSA", "Projects", "Behavioral"],
}

MODE_LABELS: Dict[str, str] = {
    "software_engineer": "Software Engineer",
    "full_stack": "Full Stack Developer",
    "ai_engineer": "AI Engineer",
    "data_scientist": "Data Scientist",
}

# category -> list of {text, difficulty}
QUESTION_BANK: Dict[str, List[Dict[str, str]]] = {
    "DSA": [
        {"text": "Explain the difference between an array and a linked list, and when you'd choose each.", "difficulty": "easy"},
        {"text": "How would you detect a cycle in a linked list? Describe the approach and its complexity.", "difficulty": "medium"},
        {"text": "Describe how a hash map works and how collisions are handled.", "difficulty": "medium"},
        {"text": "Given a large dataset, how would you find the top-K most frequent elements efficiently?", "difficulty": "hard"},
        {"text": "Compare BFS and DFS — when would you use one over the other?", "difficulty": "medium"},
    ],
    "OOP": [
        {"text": "Explain the four pillars of object-oriented programming with examples.", "difficulty": "easy"},
        {"text": "What is the difference between composition and inheritance? Which do you prefer and why?", "difficulty": "medium"},
        {"text": "Describe the SOLID principles and give an example of one you've applied.", "difficulty": "hard"},
        {"text": "What is polymorphism and how does it improve code design?", "difficulty": "easy"},
    ],
    "DBMS": [
        {"text": "Explain database normalization and why it matters.", "difficulty": "medium"},
        {"text": "What is the difference between SQL and NoSQL databases? When would you choose each?", "difficulty": "medium"},
        {"text": "Explain ACID properties in the context of transactions.", "difficulty": "medium"},
        {"text": "How would you optimize a slow query on a large table?", "difficulty": "hard"},
        {"text": "What are database indexes and what are their trade-offs?", "difficulty": "medium"},
    ],
    "OS": [
        {"text": "Explain the difference between a process and a thread.", "difficulty": "easy"},
        {"text": "What is a deadlock and what conditions cause it?", "difficulty": "medium"},
        {"text": "Describe how virtual memory and paging work.", "difficulty": "hard"},
        {"text": "What is the difference between concurrency and parallelism?", "difficulty": "medium"},
    ],
    "CN": [
        {"text": "Walk me through what happens when you type a URL and press enter.", "difficulty": "medium"},
        {"text": "Explain the difference between TCP and UDP.", "difficulty": "easy"},
        {"text": "What is the purpose of the TCP three-way handshake?", "difficulty": "medium"},
        {"text": "How does HTTPS secure communication between client and server?", "difficulty": "hard"},
    ],
    "ML": [
        {"text": "Explain the bias-variance tradeoff.", "difficulty": "medium"},
        {"text": "How do you handle overfitting in a machine learning model?", "difficulty": "medium"},
        {"text": "Explain the difference between precision and recall, and when each matters.", "difficulty": "medium"},
        {"text": "Describe how a random forest works and why it reduces variance.", "difficulty": "hard"},
        {"text": "What is the difference between supervised and unsupervised learning?", "difficulty": "easy"},
        {"text": "How would you evaluate a classification model on imbalanced data?", "difficulty": "hard"},
    ],
    "Projects": [
        {"text": "Walk me through the most technically challenging project you've worked on.", "difficulty": "medium"},
        {"text": "Describe a technical decision you made on a project and the trade-offs involved.", "difficulty": "medium"},
        {"text": "How did you ensure quality and correctness in your last project?", "difficulty": "medium"},
    ],
    "Behavioral": [
        {"text": "Tell me about a time you had a conflict with a teammate and how you resolved it.", "difficulty": "easy"},
        {"text": "Describe a situation where you had to learn a new technology quickly.", "difficulty": "easy"},
        {"text": "Tell me about a time you failed and what you learned from it.", "difficulty": "medium"},
    ],
}

# Follow-up probes per category (deterministic, used when no LLM is configured).
_FOLLOWUP_TEMPLATES: Dict[str, List[str]] = {
    "DSA": [
        "What's the time and space complexity of that approach?",
        "Can you think of a way to optimize it further?",
        "How would your solution change if the input didn't fit in memory?",
    ],
    "OOP": [
        "Can you give a concrete code example of that?",
        "What are the trade-offs of that design choice?",
    ],
    "DBMS": [
        "How would that behave under high write throughput?",
        "What indexing strategy would you use here?",
    ],
    "OS": ["Can you give a real-world example where that matters?"],
    "CN": ["What could go wrong at that step, and how would you debug it?"],
    "ML": [
        "How would you validate that in practice?",
        "What metric would you optimize for, and why?",
    ],
    "Projects": [
        "What would you do differently if you rebuilt it today?",
        "How did you measure the impact of that work?",
    ],
    "Behavioral": ["What was the outcome, and what did you learn?"],
}

_GENERIC_FOLLOWUPS = [
    "Can you elaborate on that with a specific example?",
    "What trade-offs did you consider?",
]


def resolve_categories(mode: str, categories: Optional[List[str]]) -> List[str]:
    """Return the categories to use, defaulting to the mode's mix.

    Always returns a fresh list so callers can safely shuffle/mutate it without
    corrupting the module-level defaults.
    """
    if categories:
        valid = [c for c in categories if c in QUESTION_BANK]
        if valid:
            return list(valid)
    return list(MODE_CATEGORIES.get(mode, list(QUESTION_BANK.keys())))


def select_questions(
    mode: str,
    categories: Optional[List[str]] = None,
    count: int = 6,
    *,
    seed: Optional[int] = None,
    project_names: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """Select a balanced set of base questions across the chosen categories."""
    rng = random.Random(seed)
    cats = resolve_categories(mode, categories)
    rng.shuffle(cats)

    selected: List[Dict[str, str]] = []
    pools = {c: rng.sample(QUESTION_BANK[c], len(QUESTION_BANK[c])) for c in cats}

    # Round-robin across categories until we reach the desired count.
    i = 0
    while len(selected) < count:
        progressed = False
        for c in cats:
            if pools[c]:
                q = pools[c].pop()
                selected.append({"category": c, "difficulty": q["difficulty"], "text": q["text"]})
                progressed = True
                if len(selected) >= count:
                    break
        i += 1
        if not progressed or i > 50:
            break

    # Personalise a Projects question using the candidate's actual projects.
    if project_names:
        for q in selected:
            if q["category"] == "Projects":
                name = project_names[0]
                q["text"] = (
                    f"Tell me about your project '{name}'. What problem did it solve "
                    "and what was your specific contribution?"
                )
                break
    return selected


def deterministic_followup(category: str, answer: str, *, seed: Optional[int] = None) -> Optional[str]:
    """Produce a deterministic follow-up probe based on the answer.

    Returns None when the answer is too short to warrant a follow-up.
    """
    if len(answer.strip()) < 25:
        return None
    rng = random.Random(seed if seed is not None else len(answer))
    templates = _FOLLOWUP_TEMPLATES.get(category, []) + _GENERIC_FOLLOWUPS
    return rng.choice(templates)
