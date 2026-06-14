"""Pure mentor logic (no Pydantic / DB dependencies).

Houses the deterministic resume analysis and roadmap construction so it can be
unit-tested and run in any environment. ``mentor_service`` wraps these in
Pydantic models and handles persistence / LLM enhancement.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

# Curated learning resources for common skills (official docs / canonical).
RESOURCES: Dict[str, Tuple[str, str]] = {
    "Python": ("Official Python Tutorial", "https://docs.python.org/3/tutorial/"),
    "FastAPI": ("FastAPI Documentation", "https://fastapi.tiangolo.com/"),
    "Django": ("Django Docs", "https://docs.djangoproject.com/"),
    "React": ("React Learn", "https://react.dev/learn"),
    "Next.js": ("Next.js Learn", "https://nextjs.org/learn"),
    "TypeScript": ("TypeScript Handbook", "https://www.typescriptlang.org/docs/"),
    "PyTorch": ("PyTorch Tutorials", "https://pytorch.org/tutorials/"),
    "TensorFlow": ("TensorFlow Tutorials", "https://www.tensorflow.org/tutorials"),
    "scikit-learn": ("scikit-learn User Guide", "https://scikit-learn.org/stable/user_guide.html"),
    "Machine Learning": ("Google ML Crash Course", "https://developers.google.com/machine-learning/crash-course"),
    "Deep Learning": ("DeepLearning.AI", "https://www.deeplearning.ai/"),
    "NLP": ("Hugging Face NLP Course", "https://huggingface.co/learn/nlp-course"),
    "Docker": ("Docker Get Started", "https://docs.docker.com/get-started/"),
    "Kubernetes": ("Kubernetes Basics", "https://kubernetes.io/docs/tutorials/kubernetes-basics/"),
    "AWS": ("AWS Skill Builder", "https://skillbuilder.aws/"),
    "PostgreSQL": ("PostgreSQL Tutorial", "https://www.postgresql.org/docs/current/tutorial.html"),
    "MongoDB": ("MongoDB University", "https://learn.mongodb.com/"),
    "SQL": ("SQLBolt Interactive Lessons", "https://sqlbolt.com/"),
    "Data Structures": ("NeetCode DSA", "https://neetcode.io/"),
    "Algorithms": ("NeetCode Algorithms", "https://neetcode.io/"),
    "System Design": ("System Design Primer", "https://github.com/donnemartin/system-design-primer"),
    "GraphQL": ("GraphQL Learn", "https://graphql.org/learn/"),
    "Kafka": ("Apache Kafka Docs", "https://kafka.apache.org/documentation/"),
    "Redis": ("Redis University", "https://redis.io/learn"),
}


def resource_for(skill: str) -> Tuple[str, str]:
    if skill in RESOURCES:
        return RESOURCES[skill]
    query = skill.replace(" ", "+")
    return (f"Top resources for {skill}", f"https://www.google.com/search?q=learn+{query}+tutorial")


def has_quantified_bullets(experience: List[Dict]) -> bool:
    for exp in experience:
        for bullet in exp.get("bullets", []):
            if re.search(r"\d", bullet):
                return True
    return False


def analyze_resume(profile: Dict) -> Tuple[List[str], List[str], List[str]]:
    """Return (strengths, missing_sections, suggestions)."""
    strengths: List[str] = []
    missing: List[str] = []
    suggestions: List[str] = []

    skills = profile.get("skills", [])
    experience = profile.get("experience", [])
    projects = profile.get("projects", [])
    education = profile.get("education", [])
    certifications = profile.get("certifications", [])
    months = profile.get("total_experience_months", 0) or 0
    contact = profile.get("contact", {}) or {}

    if len(skills) >= 8:
        strengths.append(f"Broad skill set ({len(skills)} skills detected)")
    if months >= 24:
        strengths.append(f"{round(months / 12, 1)} years of experience")
    if len(projects) >= 2:
        strengths.append(f"{len(projects)} projects demonstrate hands-on work")
    if certifications:
        strengths.append(f"{len(certifications)} certification(s) listed")
    if education:
        strengths.append("Education section present")

    if not profile.get("summary"):
        missing.append("Professional summary")
    if not projects:
        missing.append("Projects")
    if not certifications:
        missing.append("Certifications")
    if not contact.get("links"):
        missing.append("Portfolio / GitHub / LinkedIn links")
    if not education:
        missing.append("Education")

    if not profile.get("summary"):
        suggestions.append("Add a 2–3 line summary highlighting your strongest skills and goals.")
    if any(len(e.get("bullets", [])) == 0 for e in experience):
        suggestions.append("Add bullet points describing impact for each role.")
    if not has_quantified_bullets(experience):
        suggestions.append("Quantify achievements with numbers (e.g., 'reduced latency 30%').")
    if len(skills) < 6:
        suggestions.append("List more relevant technical skills to improve keyword matching.")
    if not contact.get("links"):
        suggestions.append("Include links to your GitHub, LinkedIn, or portfolio.")
    if not suggestions:
        suggestions.append("Strong resume — tailor the summary and skills to each job you apply to.")

    return strengths, missing, suggestions


def distribute_into_weeks(skills: List[str], weeks: int) -> List[List[str]]:
    """Spread skills across weeks in balanced, ordered buckets."""
    buckets: List[List[str]] = [[] for _ in range(weeks)]
    if not skills:
        return buckets
    per_week = max(1, (len(skills) + weeks - 1) // weeks)
    idx = 0
    for week in range(weeks):
        chunk = skills[idx : idx + per_week]
        buckets[week].extend(chunk)
        idx += per_week
        if idx >= len(skills):
            break
    return buckets


def week_focus(skills: List[str]) -> str:
    if len(skills) == 1:
        return f"Master {skills[0]}"
    return f"Learn {', '.join(skills[:-1])} and {skills[-1]}"
