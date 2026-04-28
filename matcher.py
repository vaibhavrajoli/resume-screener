import os
import re
import nltk
import PyPDF2
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── NLTK setup (works locally + Streamlit Cloud) ──────────────────────────────
_nltk_path = os.path.join(os.path.expanduser("~"), "nltk_data")
os.makedirs(_nltk_path, exist_ok=True)
nltk.data.path.append(_nltk_path)
for pkg in ["stopwords", "punkt"]:
    nltk.download(pkg, download_dir=_nltk_path, quiet=True)

from nltk.corpus import stopwords
STOP = set(stopwords.words("english"))

# ── Section heading patterns (universal — works for any role) ─────────────────
SECTION_PATTERNS = {
    "Summary":        r"\b(summary|objective|profile|about|career goal)\b",
    "Skills":         r"\b(skill|technolog|tool|competenc|proficien|expertise|stack)\b",
    "Experience":     r"\b(experience|work history|employment|intern|position|role|job)\b",
    "Education":      r"\b(education|academic|qualif|degree|university|college|school)\b",
    "Certifications": r"\b(certif|licen|course|training|credential|badge|award)\b",
    "Projects":       r"\b(project|portfolio|work sample|case study|built|developed)\b",
    "Achievements":   r"\b(achiev|accomplish|award|honor|recogni|publication)\b",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_file) -> str:
    """Read all pages of a PDF and return plain text."""
    reader = PyPDF2.PdfReader(pdf_file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _fix_merged(text: str) -> str:
    """Fix wall-of-text (no spaces) from bad PDF copy-paste."""
    avg = len(text) / max(len(text.split()), 1)
    if avg < 15:
        return text
    try:
        import wordninja
        return " ".join(wordninja.split(text))
    except Exception:
        return text


def _clean(text: str) -> str:
    """Lowercase, remove punctuation, remove stop words, min length 2."""
    text = _fix_merged(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(w for w in text.split() if w not in STOP and len(w) > 2)


# ── Section splitter ──────────────────────────────────────────────────────────

def _split_into_sections(text: str) -> dict:
    sections = {s: "" for s in SECTION_PATTERNS}
    current = "Summary"
    for line in text.splitlines():
        low = line.lower().strip()
        matched = False
        for sec, pat in SECTION_PATTERNS.items():
            if re.search(pat, low) and len(low) < 60:  # headings are short
                current = sec
                matched = True
                break
        if not matched:
            sections[current] += " " + line
    return sections


# ── Dynamic keyword extraction from JD ───────────────────────────────────────

def extract_jd_keywords(jd_text: str, top_n: int = 60) -> list[str]:
    """
    Pull the most important keywords from ANY job description automatically.
    Uses TF-IDF on unigrams + bigrams so it captures both single words
    ('python') and phrases ('machine learning', 'project management').
    """
    cleaned = _clean(jd_text)
    if not cleaned.strip():
        return []
    vec = TfidfVectorizer(
        max_features=top_n,
        ngram_range=(1, 2),
        min_df=1,
    )
    vec.fit([cleaned])
    return list(vec.get_feature_names_out())


# ── Overall cosine similarity score ──────────────────────────────────────────

def get_overall_score(resume_text: str, jd_text: str) -> float:
    """Return 0-100 cosine similarity between resume and JD."""
    cr = _clean(resume_text)
    cj = _clean(jd_text)
    if not cr or not cj:
        return 0.0
    vec = TfidfVectorizer(ngram_range=(1, 2))
    v = vec.fit_transform([cr, cj])
    score = cosine_similarity(v[0], v[1])[0][0]
    return round(float(score) * 100, 2)


# ── Section-wise analysis ─────────────────────────────────────────────────────

def get_section_analysis(resume_text: str, jd_text: str) -> dict:
    """
    For each resume section, compare against the full JD keywords.
    Returns matched / missing lists, section score, and smart recommendations.
    """
    jd_keywords = extract_jd_keywords(jd_text, top_n=60)
    resume_sections = _split_into_sections(resume_text)
    # Build a set of ALL cleaned resume words (for global lookup too)
    all_resume_words = set(_clean(resume_text).split())

    results = {}
    for section, section_text in resume_sections.items():
        section_words = set(_clean(section_text).split())
        # A keyword counts as matched if it appears anywhere in the resume
        combined = section_words | all_resume_words

        matched, missing = [], []
        for kw in jd_keywords:
            kw_words = set(kw.split())
            if kw_words.issubset(combined):
                matched.append(kw)
            else:
                missing.append(kw)

        score = round(len(matched) / len(jd_keywords) * 100, 1) if jd_keywords else 0.0
        results[section] = {
            "matched":         matched,
            "missing":         missing,
            "score":           score,
            "recommendations": _smart_recommendations(section, matched, missing, jd_text),
        }
    return results


# ── Smart recommendations (universal, context-aware) ─────────────────────────

def _smart_recommendations(section: str, matched: list, missing: list, jd_text: str) -> list:
    """
    Generate actionable, role-agnostic recommendations based on what's missing
    in each section. Works for any job role or domain.
    """
    recs = []
    if not missing:
        recs.append("This section aligns well with the job description. Keep it as-is.")
        return recs

    top_missing = missing[:6]
    pct_missing = round(len(missing) / max(len(matched) + len(missing), 1) * 100)

    if section == "Skills":
        recs.append(
            f"Add these {len(missing)} missing skills/tools to your Skills section "
            f"(if you have experience with them): {', '.join(top_missing)}."
        )
        recs.append(
            "Mirror the exact wording from the JD — ATS systems do exact keyword matching. "
            "E.g. if JD says 'MS Excel', don't just write 'Excel'."
        )
        if pct_missing > 50:
            recs.append(
                "More than half the required skills are missing. Consider grouping skills "
                "into categories (Technical Skills, Soft Skills, Tools) for better ATS parsing."
            )

    elif section == "Experience":
        recs.append(
            f"Incorporate these keywords into your job bullet points: {', '.join(top_missing)}. "
            "Rewrite bullets to highlight responsibilities that match the JD."
        )
        recs.append(
            "Use quantifiable achievements: e.g. 'Increased sales by 20%' or "
            "'Managed a team of 5 engineers'. Numbers stand out to both ATS and recruiters."
        )
        recs.append(
            "Start each bullet with a strong action verb (Developed, Managed, Led, "
            "Designed, Implemented, Improved, Analysed)."
        )

    elif section == "Summary":
        recs.append(
            f"Your summary should mention the role title and key terms from the JD. "
            f"Try to include: {', '.join(top_missing[:4])}."
        )
        recs.append(
            "Keep it 3-4 lines. Tailor it specifically to THIS job — a generic summary "
            "hurts your ATS score."
        )

    elif section == "Education":
        recs.append(
            "Make sure your degree title, major, university name, and graduation year "
            "are clearly stated — ATS systems parse these fields specifically."
        )
        if any(w in jd_text.lower() for w in ["gpa", "grade", "cgpa"]):
            recs.append("The JD may value academic scores — consider adding your GPA/CGPA if strong.")

    elif section == "Certifications":
        recs.append(
            f"The JD values credentials. Consider earning certifications related to: "
            f"{', '.join(top_missing[:4])}. Many are free on Coursera, Google, or LinkedIn Learning."
        )
        recs.append(
            "List certification name, issuing body, and year. "
            "E.g. 'AWS Certified Cloud Practitioner — Amazon, 2024'."
        )

    elif section == "Projects":
        recs.append(
            f"Add 1-2 projects that demonstrate these skills: {', '.join(top_missing[:4])}. "
            "Projects are powerful proof of skills, especially for freshers."
        )
        recs.append(
            "For each project include: what you built, which tools/technologies you used, "
            "what the outcome or impact was, and a GitHub/live link if available."
        )

    elif section == "Achievements":
        recs.append(
            "Highlight awards, publications, competitions, or recognitions relevant to the role. "
            "These differentiate you from candidates with similar skills."
        )

    return recs


# ── Aggregate helpers ─────────────────────────────────────────────────────────

def get_all_matched(section_results: dict) -> list:
    seen, out = set(), []
    for d in section_results.values():
        for k in d["matched"]:
            if k not in seen:
                seen.add(k); out.append(k)
    return out


def get_all_missing(section_results: dict) -> list:
    seen, out = set(), []
    for d in section_results.values():
        for k in d["missing"]:
            if k not in seen:
                seen.add(k); out.append(k)
    return out


def get_predicted_score(overall: float, section_results: dict) -> float:
    """
    Realistic estimate of score if candidate adds all missing keywords.
    Uses a diminishing-returns model — not a simple linear jump.
    """
    total   = sum(len(d["matched"]) + len(d["missing"]) for d in section_results.values())
    matched = sum(len(d["matched"]) for d in section_results.values())
    if total == 0:
        return overall
    current_ratio = matched / total
    # Assume candidate can realistically add ~65% of missing keywords
    new_matched = matched + (total - matched) * 0.65
    predicted = round(min((new_matched / total) * 100, 98.0), 1)
    return predicted


def get_score_label(score: float) -> tuple[str, str]:
    """Return (label, css_color_class) for a given score."""
    if score >= 75:
        return "Excellent Match", "green"
    elif score >= 55:
        return "Good Match", "blue"
    elif score >= 35:
        return "Moderate Match", "orange"
    else:
        return "Weak Match", "red"