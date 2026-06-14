"""Curated technical-skill taxonomy and extraction utilities.

This module is the single source of truth for skill recognition across the
product: resume parsing, job-description parsing, candidate matching, and ML
feature engineering all rely on it. Keeping it dependency-free (stdlib only)
makes it fast, testable, and reusable everywhere.

Each canonical skill maps to a set of aliases/surface forms. Extraction is
alias-aware and uses word-boundary matching so we don't match "java" inside
"javascript" or "r" inside ordinary prose.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set

# ── Canonical skill → aliases ────────────────────────────────────────────
# Grouped by category for readability; categories also drive UI grouping.
SKILL_CATEGORIES: Dict[str, Dict[str, List[str]]] = {
    "languages": {
        "Python": ["python"],
        "JavaScript": ["javascript", "js"],
        "TypeScript": ["typescript", "ts"],
        "Java": ["java"],
        "C++": ["c++", "cpp"],
        "C": ["c language", "c programming"],
        "C#": ["c#", "csharp"],
        "Go": ["golang", "go lang"],
        "Rust": ["rust"],
        "Ruby": ["ruby"],
        "PHP": ["php"],
        "Swift": ["swift"],
        "Kotlin": ["kotlin"],
        "Scala": ["scala"],
        "R": ["r programming", "r language"],
        "MATLAB": ["matlab"],
        "SQL": ["sql"],
        "Bash": ["bash", "shell scripting"],
    },
    "frontend": {
        "React": ["react", "react.js", "reactjs"],
        "Next.js": ["next.js", "nextjs", "next js"],
        "Vue.js": ["vue", "vue.js", "vuejs"],
        "Angular": ["angular", "angularjs"],
        "Svelte": ["svelte"],
        "Redux": ["redux"],
        "Tailwind CSS": ["tailwind", "tailwindcss"],
        "HTML": ["html", "html5"],
        "CSS": ["css", "css3"],
        "Sass": ["sass", "scss"],
    },
    "backend": {
        "Node.js": ["node.js", "nodejs", "node js"],
        "Express": ["express", "express.js", "expressjs"],
        "FastAPI": ["fastapi"],
        "Django": ["django"],
        "Flask": ["flask"],
        "Spring Boot": ["spring boot", "springboot", "spring"],
        "Ruby on Rails": ["rails", "ruby on rails"],
        "GraphQL": ["graphql"],
        "REST API": ["rest api", "restful", "rest"],
        "gRPC": ["grpc"],
        "WebSockets": ["websocket", "websockets"],
    },
    "databases": {
        "PostgreSQL": ["postgresql", "postgres"],
        "MySQL": ["mysql"],
        "MongoDB": ["mongodb", "mongo"],
        "Redis": ["redis"],
        "SQLite": ["sqlite"],
        "Elasticsearch": ["elasticsearch", "elastic search"],
        "Cassandra": ["cassandra"],
        "DynamoDB": ["dynamodb"],
        "Oracle": ["oracle db", "oracle database"],
    },
    "cloud_devops": {
        "AWS": ["aws", "amazon web services"],
        "Azure": ["azure", "microsoft azure"],
        "GCP": ["gcp", "google cloud"],
        "Docker": ["docker"],
        "Kubernetes": ["kubernetes", "k8s"],
        "Terraform": ["terraform"],
        "Jenkins": ["jenkins"],
        "GitHub Actions": ["github actions"],
        "CI/CD": ["ci/cd", "cicd", "continuous integration"],
        "Linux": ["linux", "unix"],
        "Nginx": ["nginx"],
        "Kafka": ["kafka", "apache kafka"],
        "RabbitMQ": ["rabbitmq"],
    },
    "data_ml": {
        "Machine Learning": ["machine learning", "ml"],
        "Deep Learning": ["deep learning"],
        "NLP": ["nlp", "natural language processing"],
        "Computer Vision": ["computer vision", "cv"],
        "TensorFlow": ["tensorflow"],
        "PyTorch": ["pytorch"],
        "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
        "Keras": ["keras"],
        "XGBoost": ["xgboost"],
        "Pandas": ["pandas"],
        "NumPy": ["numpy"],
        "Spark": ["spark", "apache spark", "pyspark"],
        "Hadoop": ["hadoop"],
        "Tableau": ["tableau"],
        "Power BI": ["power bi", "powerbi"],
        "OpenCV": ["opencv"],
        "Hugging Face": ["hugging face", "huggingface", "transformers"],
        "LLMs": ["llm", "llms", "large language models"],
        "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
    },
    "cs_fundamentals": {
        "Data Structures": ["data structures", "dsa"],
        "Algorithms": ["algorithms", "algorithm design"],
        "Operating Systems": ["operating systems", "os"],
        "DBMS": ["dbms", "database management"],
        "Computer Networks": ["computer networks", "networking"],
        "OOP": ["oop", "object oriented programming", "object-oriented"],
        "System Design": ["system design", "distributed systems"],
    },
    "tools": {
        "Git": ["git"],
        "Jira": ["jira"],
        "Postman": ["postman"],
        "Figma": ["figma"],
        "Agile": ["agile", "scrum"],
    },
}


def _build_alias_index() -> List[tuple[str, str]]:
    """Return (alias, canonical) pairs sorted by descending alias length.

    Longer aliases are matched first so "react.js" wins over "react", and
    multi-word skills are detected before their substrings.
    """
    pairs: List[tuple[str, str]] = []
    for group in SKILL_CATEGORIES.values():
        for canonical, aliases in group.items():
            for alias in aliases:
                pairs.append((alias.lower(), canonical))
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


_ALIAS_INDEX = _build_alias_index()

# Canonical → category, for grouping in the UI / features.
CANONICAL_TO_CATEGORY: Dict[str, str] = {
    canonical: category
    for category, group in SKILL_CATEGORIES.items()
    for canonical in group
}

ALL_CANONICAL_SKILLS: List[str] = sorted(CANONICAL_TO_CATEGORY.keys())


def _alias_pattern(alias: str) -> re.Pattern[str]:
    """Compile a word-boundary regex for an alias.

    We escape regex metacharacters (``c++``, ``c#``, ``ci/cd`` contain them)
    and use lookarounds rather than ``\\b`` because ``\\b`` behaves poorly
    around symbols like ``+`` and ``#``.
    """
    escaped = re.escape(alias)
    return re.compile(rf"(?<![A-Za-z0-9+#]){escaped}(?![A-Za-z0-9+#])", re.IGNORECASE)


# Pre-compile alias patterns once.
_ALIAS_PATTERNS: List[tuple[re.Pattern[str], str]] = [
    (_alias_pattern(alias), canonical) for alias, canonical in _ALIAS_INDEX
]


def extract_skills(text: str) -> List[str]:
    """Extract canonical skills present in ``text`` (deduplicated, ordered).

    Returns canonical skill names in a stable, deterministic order
    (alphabetical) so downstream features and UI are reproducible.
    """
    if not text:
        return []
    found: Set[str] = set()
    for pattern, canonical in _ALIAS_PATTERNS:
        if pattern.search(text):
            found.add(canonical)
    return sorted(found)


def categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    """Group canonical skills by their taxonomy category."""
    grouped: Dict[str, List[str]] = {}
    for skill in skills:
        category = CANONICAL_TO_CATEGORY.get(skill, "other")
        grouped.setdefault(category, []).append(skill)
    for values in grouped.values():
        values.sort()
    return grouped
