"""Deterministic resume parser (no LLM dependency).

Pipeline:
    PDF bytes --(pdfplumber)--> raw text --(section split)--> sections
            --(per-section extractors)--> structured profile dict

The PDF library is imported lazily so the parsing logic (the interesting,
testable part) can run with only the standard library. All extractors operate
on plain text and return JSON-serialisable dicts that map directly onto the
Pydantic models in ``app.models.resume``.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional

from app.ml.taxonomy import extract_skills

# ── Section headers ──────────────────────────────────────────────────────
# Maps a canonical section name to the header keywords that introduce it.
SECTION_KEYWORDS: Dict[str, List[str]] = {
    "summary": ["summary", "objective", "about", "profile"],
    "skills": ["skills", "technical skills", "technologies", "tech stack"],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "work history",
    ],
    "projects": ["projects", "personal projects", "academic projects"],
    "education": ["education", "academic background", "academics"],
    "certifications": ["certifications", "certificates", "licenses"],
    "achievements": ["achievements", "awards", "honors"],
}

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}")
_URL_RE = re.compile(r"(https?://[^\s)]+|(?:www\.|linkedin\.com|github\.com)[^\s)]+)", re.IGNORECASE)
_DEGREE_RE = re.compile(
    r"\b(b\.?tech|b\.?e\.?|b\.?sc|bachelor(?:'s)?|m\.?tech|m\.?sc|m\.?s\.?|"
    r"master(?:'s)?|mba|ph\.?d|doctorate|b\.?c\.?a|m\.?c\.?a|diploma)\b",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_GPA_RE = re.compile(r"\b(?:gpa|cgpa)\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,2})?)\s*(?:/\s*(\d{1,2}(?:\.\d{1,2})?))?", re.IGNORECASE)


# ── Public API ───────────────────────────────────────────────────────────
def extract_text_from_pdf(data: bytes) -> str:
    """Extract text from a PDF byte string using pdfplumber (lazy import)."""
    import io

    import pdfplumber  # imported lazily; heavy/optional dependency

    parts: List[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            parts.append(text)
    return "\n".join(parts)


def parse_resume_text(text: str) -> dict:
    """Parse raw resume text into a structured profile dict."""
    normalized = _normalize(text)
    sections = _split_sections(normalized)

    skills = _extract_skills(sections, normalized)
    experience = _parse_experience(sections.get("experience", ""))
    education = _parse_education(sections.get("education", ""))
    projects = _parse_projects(sections.get("projects", ""))
    certifications = _parse_certifications(sections.get("certifications", ""))
    total_months = sum(e["months"] for e in experience if e.get("months"))

    return {
        "contact": _parse_contact(normalized),
        "summary": sections.get("summary", "").strip() or None,
        "skills": skills,
        "experience": experience,
        "education": education,
        "projects": projects,
        "certifications": certifications,
        "total_experience_months": total_months,
    }


# ── Normalisation & sectioning ───────────────────────────────────────────
def _normalize(text: str) -> str:
    """Standardise whitespace and bullet characters."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[•▪◦‣·]", "-", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _header_lookup() -> List[tuple[str, str]]:
    pairs: List[tuple[str, str]] = []
    for canonical, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            pairs.append((kw, canonical))
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


_HEADER_LOOKUP = _header_lookup()


def _match_header(line: str) -> Optional[str]:
    """Return the canonical section if a line looks like a section header."""
    stripped = line.strip().strip(":").strip()
    if not stripped or len(stripped) > 40:
        return None
    lowered = stripped.lower()
    for kw, canonical in _HEADER_LOOKUP:
        # Header lines are short and consist (mostly) of the keyword.
        if lowered == kw or lowered.startswith(kw + " ") or lowered.endswith(" " + kw):
            return canonical
    return None


def _split_sections(text: str) -> Dict[str, str]:
    """Split text into sections keyed by canonical section name."""
    sections: Dict[str, List[str]] = {}
    current = "header"
    for line in text.split("\n"):
        canonical = _match_header(line)
        if canonical is not None:
            current = canonical
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


# ── Field extractors ─────────────────────────────────────────────────────
def _parse_contact(text: str) -> dict:
    head = text[:600]  # contact info is near the top
    email_match = _EMAIL_RE.search(head) or _EMAIL_RE.search(text)
    phone_match = _PHONE_RE.search(head) or _PHONE_RE.search(text)
    links = []
    for m in _URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;")
        if url not in links:
            links.append(url)
    name = _guess_name(text)
    return {
        "name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "links": links[:6],
    }


def _guess_name(text: str) -> Optional[str]:
    """Heuristic: the first short, mostly-alphabetic non-contact line."""
    for line in text.split("\n")[:8]:
        candidate = line.strip()
        if not candidate or _EMAIL_RE.search(candidate) or _URL_RE.search(candidate):
            continue
        if _PHONE_RE.search(candidate):
            continue
        words = candidate.split()
        if 1 < len(words) <= 4 and all(re.match(r"^[A-Za-z.'-]+$", w) for w in words):
            return candidate
    return None


def _extract_skills(sections: Dict[str, str], full_text: str) -> List[str]:
    """Prefer the skills section but fall back to the full document."""
    skill_text = sections.get("skills", "")
    skills = set(extract_skills(skill_text))
    # Always augment from the full text — skills appear in projects/experience.
    skills.update(extract_skills(full_text))
    return sorted(skills)


def _parse_experience(text: str) -> List[dict]:
    if not text:
        return []
    entries: List[dict] = []
    for block in _split_entries(text):
        date_range = _find_date_range(block)
        lines = [ln.strip("- ").strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        title_line = lines[0]
        title, company = _split_title_company(title_line)
        # Exclude the standalone date-range line and the title line from bullets.
        bullets = [
            ln for ln in lines[1:]
            if len(ln) > 3 and not _is_date_line(ln)
        ][:8]
        months = _months_between(date_range) if date_range else 0
        entries.append({
            "title": title,
            "company": company,
            "start": date_range[0] if date_range else None,
            "end": date_range[1] if date_range else None,
            "months": months,
            "bullets": bullets,
        })
    return entries


def _parse_projects(text: str) -> List[dict]:
    if not text:
        return []
    projects: List[dict] = []
    for block in _split_entries(text):
        lines = [ln.strip("- ").strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        name = re.split(r"[-–|:]", lines[0])[0].strip()
        description = " ".join(lines[1:])[:500]
        tech = extract_skills(block)
        projects.append({
            "name": name[:120],
            "description": description or None,
            "tech": tech,
            "bullets": [ln for ln in lines[1:] if len(ln) > 3][:6],
        })
    return projects


def _parse_education(text: str) -> List[dict]:
    if not text:
        return []
    education: List[dict] = []
    for block in _split_entries(text):
        if not _DEGREE_RE.search(block) and not _YEAR_RE.search(block):
            continue
        degree_match = _DEGREE_RE.search(block)
        year_matches = _YEAR_RE.findall(block)
        years = re.findall(r"\b(?:19|20)\d{2}\b", block)
        gpa_match = _GPA_RE.search(block)
        lines = [ln.strip("- ").strip() for ln in block.split("\n") if ln.strip()]
        institution = _guess_institution(lines)
        education.append({
            "degree": degree_match.group(0).title() if degree_match else None,
            "institution": institution,
            "year": int(years[-1]) if years else None,
            "gpa": gpa_match.group(1) if gpa_match else None,
        })
    return education


def _parse_certifications(text: str) -> List[str]:
    if not text:
        return []
    certs: List[str] = []
    for line in text.split("\n"):
        item = line.strip("- ").strip()
        if 3 < len(item) < 120:
            certs.append(item)
    return certs[:15]


# ── Helpers ──────────────────────────────────────────────────────────────
def _split_entries(text: str) -> List[str]:
    """Split a section into entries on blank lines (falls back to lines)."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    return blocks if blocks else [ln for ln in text.split("\n") if ln.strip()]


def _split_title_company(line: str) -> tuple[str, Optional[str]]:
    parts = re.split(r"(?:\s+(?:at|@)\s+|\s*[-–|,]\s+)", line, maxsplit=1)
    title = parts[0].strip()[:120]
    company = parts[1].strip()[:120] if len(parts) > 1 else None
    return title, company


def _is_date_line(line: str) -> bool:
    """True if the line is essentially just a date / date-range."""
    stripped = line.strip()
    if len(stripped) > 30:
        return False
    return _find_date_range(stripped) is not None or bool(
        re.fullmatch(r"(?:[A-Za-z]{3,9}\.?\s*)?(?:19|20)\d{2}", stripped)
    )


def _guess_institution(lines: List[str]) -> Optional[str]:
    for line in lines:
        if re.search(r"\b(university|college|institute|school|iit|nit|academy)\b", line, re.IGNORECASE):
            return line[:160]
    return lines[0][:160] if lines else None


def _find_date_range(text: str) -> Optional[tuple[str, str]]:
    """Find a 'start - end' date range like 'Jan 2020 - Mar 2022' or '2019 - Present'."""
    pattern = re.compile(
        r"((?:[A-Za-z]{3,9}\.?\s*)?(?:19|20)\d{2})\s*[-–to]+\s*"
        r"((?:[A-Za-z]{3,9}\.?\s*)?(?:19|20)\d{2}|present|current|now)",
        re.IGNORECASE,
    )
    m = pattern.search(text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None


def _months_between(date_range: tuple[str, str]) -> int:
    start = _parse_month_year(date_range[0])
    end_raw = date_range[1].lower()
    if end_raw in {"present", "current", "now"}:
        now = datetime.now()
        end = (now.year, now.month)
    else:
        end = _parse_month_year(date_range[1])
    if not start or not end:
        return 0
    months = (end[0] - start[0]) * 12 + (end[1] - start[1])
    return max(months, 0)


def _parse_month_year(value: str) -> Optional[tuple[int, int]]:
    year_match = _YEAR_RE.search(value)
    if not year_match:
        return None
    year = int(year_match.group(0))
    month = 1
    month_match = re.search(r"[A-Za-z]{3,9}", value)
    if month_match:
        month = _MONTHS.get(month_match.group(0)[:3].lower(), 1)
    return year, month
