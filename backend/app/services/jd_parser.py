"""Deterministic job-description parser (no LLM dependency).

Extracts a structured job profile from raw JD text:
    - required vs preferred skills (context-aware)
    - technologies (all recognised skills)
    - responsibilities (bullet/sentence extraction)
    - minimum experience (years)
    - seniority level
    - education requirement

Like the resume parser, this is pure standard library + the shared skill
taxonomy, so it is fully testable without external dependencies.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from app.ml.taxonomy import extract_skills

# Cues that mark a line/section as describing *preferred* (not required) skills.
_PREFERRED_CUES = [
    "preferred",
    "nice to have",
    "nice-to-have",
    "bonus",
    "plus",
    "good to have",
    "desirable",
    "a plus",
    "advantage",
]

# Cues that strongly mark required skills/sections.
_REQUIRED_CUES = [
    "required",
    "requirement",
    "must have",
    "must-have",
    "minimum qualifications",
    "qualifications",
    "you have",
    "we expect",
]

_RESPONSIBILITY_CUES = [
    "responsibilities",
    "what you'll do",
    "what you will do",
    "the role",
    "your role",
    "duties",
    "you will",
    "day to day",
    "day-to-day",
]

# Generic section-heading cue words used to detect block boundaries.
_HEADING_CUES = [
    "responsibilities", "what you'll do", "what you will do", "duties",
    "your role", "the role", "you will", "day to day", "day-to-day",
    "required", "requirement", "qualifications", "must have", "must-have",
    "preferred", "nice to have", "nice-to-have", "bonus", "skills",
    "about", "who you are", "what we offer", "benefits", "perks",
    "compensation", "education", "experience", "we expect", "you have",
]

_SENIORITY_MAP = [
    ("intern", "Intern"),
    ("principal", "Principal"),
    ("staff", "Staff"),
    ("lead", "Lead"),
    ("senior", "Senior"),
    ("sr.", "Senior"),
    ("junior", "Junior"),
    ("jr.", "Junior"),
    ("entry level", "Entry"),
    ("entry-level", "Entry"),
    ("mid level", "Mid"),
    ("mid-level", "Mid"),
]

_EXPERIENCE_RE = re.compile(
    r"(\d{1,2})\s*(?:\+|to|-|–)?\s*(?:(\d{1,2})\s*)?(?:\+)?\s*years?",
    re.IGNORECASE,
)
_DEGREE_RE = re.compile(
    r"\b(bachelor(?:'s)?|master(?:'s)?|b\.?tech|b\.?e\.?|b\.?sc|m\.?tech|"
    r"m\.?sc|m\.?s\.?|mba|ph\.?d|doctorate|degree)\b",
    re.IGNORECASE,
)


def parse_job_text(text: str, *, title: Optional[str] = None) -> dict:
    """Parse raw job-description text into a structured profile dict."""
    normalized = _normalize(text)
    lines = [ln.strip("- ").strip() for ln in normalized.split("\n") if ln.strip()]

    all_skills = set(extract_skills(normalized))
    preferred = _extract_preferred_skills(lines)
    # Required = everything recognised that isn't explicitly preferred.
    required = sorted(all_skills - set(preferred))
    preferred = sorted(set(preferred) - set(required))

    return {
        "title": (title or _guess_title(lines)) or None,
        "required_skills": required,
        "preferred_skills": preferred,
        "technologies": sorted(all_skills),
        "responsibilities": _extract_responsibilities(normalized, lines),
        "min_experience_years": _extract_min_experience(normalized),
        "education_required": _extract_education(normalized),
        "seniority": _extract_seniority(normalized, title),
    }


# ── Normalisation ────────────────────────────────────────────────────────
def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[•▪◦‣·]", "-", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _line_is_preferred(line: str) -> bool:
    lowered = line.lower()
    return any(cue in lowered for cue in _PREFERRED_CUES)


def _extract_preferred_skills(lines: List[str]) -> List[str]:
    """Collect skills that appear in a 'preferred / nice to have' context.

    A preferred-cue line marks itself and (until the next blank/heading) the
    lines beneath it as preferred context.
    """
    preferred: List[str] = []
    in_preferred_block = False
    for line in lines:
        lowered = line.lower()
        if _line_is_preferred(line):
            in_preferred_block = True
        elif any(cue in lowered for cue in _REQUIRED_CUES) or any(
            cue in lowered for cue in _RESPONSIBILITY_CUES
        ):
            in_preferred_block = False

        if in_preferred_block or _line_is_preferred(line):
            preferred.extend(extract_skills(line))
    return preferred


def _is_heading(line: str) -> bool:
    """True if a line looks like a section heading (short + cue/colon)."""
    stripped = line.strip("- ").strip()
    if not stripped or len(stripped) > 45:
        return False
    lowered = stripped.lower().rstrip(":")
    if stripped.endswith(":"):
        return True
    return any(lowered == cue or lowered.startswith(cue) for cue in _HEADING_CUES)


def _starts_responsibility_section(line: str) -> bool:
    lowered = line.strip("- ").strip().lower().rstrip(":")
    return any(lowered.startswith(cue) for cue in _RESPONSIBILITY_CUES)


def _extract_responsibilities(text: str, lines: List[str]) -> List[str]:
    """Extract responsibility statements from the responsibilities section.

    The block begins at a responsibility heading and ends at the next heading
    (qualifications, preferred, benefits, etc.), so content doesn't bleed
    across sections.
    """
    responsibilities: List[str] = []
    in_block = False
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if _is_heading(line):
            in_block = _starts_responsibility_section(line)
            continue
        if in_block:
            item = line.strip("- ").strip()
            if 4 < len(item) < 240:
                responsibilities.append(item)
    return responsibilities[:12]


def _extract_min_experience(text: str) -> Optional[int]:
    """Find the minimum required years of experience, if stated."""
    years: List[int] = []
    for match in _EXPERIENCE_RE.finditer(text):
        low = int(match.group(1))
        years.append(low)
    if not years:
        return None
    return min(years)


def _extract_education(text: str) -> Optional[str]:
    match = _DEGREE_RE.search(text)
    if not match:
        return None
    word = match.group(0).lower()
    if word.startswith("ph") or "doctor" in word:
        return "PhD"
    if word.startswith("m") or "master" in word:
        return "Master's degree"
    if word.startswith("b") or "bachelor" in word:
        return "Bachelor's degree"
    return "Degree"


def _extract_seniority(text: str, title: Optional[str]) -> Optional[str]:
    haystack = f"{title or ''} {text}".lower()
    for needle, label in _SENIORITY_MAP:
        if needle in haystack:
            return label
    return None


def _guess_title(lines: List[str]) -> Optional[str]:
    """Heuristic: first non-empty line that looks like a role title."""
    role_words = re.compile(
        r"engineer|developer|scientist|analyst|manager|designer|architect|"
        r"intern|consultant|lead|specialist",
        re.IGNORECASE,
    )
    for line in lines[:6]:
        if role_words.search(line) and len(line) < 80:
            return line
    return lines[0][:80] if lines else None
