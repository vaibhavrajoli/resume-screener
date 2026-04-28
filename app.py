"""
app.py — AI Resume ATS Analyzer
Works for ANY job role / domain — no hardcoded keywords.
"""

import streamlit as st
from matcher import (
    extract_text_from_pdf,
    extract_jd_keywords,
    get_overall_score,
    get_section_analysis,
    get_predicted_score,
    get_all_matched,
    get_all_missing,
    get_score_label,
)
from report import generate_pdf_report

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume ATS Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* keyword badges */
.kw-green { display:inline-block; background:#dcfce7; color:#15803d;
            border-radius:6px; padding:4px 11px; margin:3px; font-size:13px; font-weight:500; }
.kw-red   { display:inline-block; background:#fee2e2; color:#b91c1c;
            border-radius:6px; padding:4px 11px; margin:3px; font-size:13px; font-weight:500; }
.kw-blue  { display:inline-block; background:#dbeafe; color:#1d4ed8;
            border-radius:6px; padding:4px 11px; margin:3px; font-size:13px; font-weight:500; }

/* recommendation box */
.rec-box { background:#eff6ff; border-left:3px solid #2563eb;
           border-radius:0 8px 8px 0; padding:10px 14px;
           margin:5px 0; font-size:14px; color:#1e3a5f; line-height:1.6; }

/* score cards */
.score-card { background:#f8fafc; border:1px solid #e2e8f0;
              border-radius:14px; padding:1.4rem 1rem; text-align:center; }
.score-num  { font-size:2.6rem; font-weight:700; line-height:1.1; }
.score-sub  { font-size:13px; color:#64748b; margin-top:4px; }

/* color helpers */
.c-green  { color:#16a34a; }
.c-blue   { color:#2563eb; }
.c-orange { color:#ea580c; }
.c-red    { color:#dc2626; }

/* section score pill */
.sec-pill { display:inline-block; border-radius:999px; padding:2px 12px;
            font-size:13px; font-weight:600; }
.pill-green  { background:#dcfce7; color:#15803d; }
.pill-blue   { background:#dbeafe; color:#1d4ed8; }
.pill-orange { background:#ffedd5; color:#c2410c; }
.pill-red    { background:#fee2e2; color:#b91c1c; }

/* info box */
.info-box { background:#f0f9ff; border:1px solid #bae6fd;
            border-radius:10px; padding:1rem; margin-bottom:1rem; font-size:14px; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/document--v1.png", width=60)
    st.markdown("## AI Resume ATS Analyzer")
    st.markdown("---")
    st.markdown("""
**How to use:**
1. Upload your resume as a PDF
2. Upload or paste the Job Description
3. Click **Analyze**
4. Review your section scores
5. Follow the recommendations
6. Download your PDF report

---
**Works for ALL roles:**
- Software Engineering
- Data Science / Analytics
- Marketing & Sales
- Finance & Accounting
- HR & Operations
- Design & Product
- Any other domain!

---
""")
    st.caption("No keywords are hardcoded. The app reads the JD and automatically extracts what matters for that specific role.")


# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 AI Resume ATS Analyzer")
st.markdown(
    "Upload your resume and the job description — the app **automatically understands** "
    "what the JD is looking for and tells you exactly how well your resume matches."
)

st.markdown('<div class="info-box">💡 <strong>No hardcoded keywords.</strong> '
            'This tool works for <strong>any job role in any domain</strong>. '
            'The AI reads the JD and extracts what matters for that specific position.</div>',
            unsafe_allow_html=True)

# ── Upload section ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("📄 Your Resume")
    resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"], key="resume")

with col2:
    st.subheader("💼 Job Description")
    jd_mode = st.radio("Input method", ["Paste text", "Upload PDF"], horizontal=True)
    if jd_mode == "Paste text":
        jd_text_input = st.text_area(
            "Paste the full job description here",
            height=220,
            placeholder="Copy and paste the complete job description...",
        )
        jd_file = None
    else:
        jd_file = st.file_uploader("Upload JD (PDF)", type=["pdf"], key="jd")
        jd_text_input = ""

analyze_btn = st.button("🔍 Analyze My Resume", type="primary", use_container_width=True)


# ── Analysis ──────────────────────────────────────────────────────────────────
if analyze_btn:
    # Gather inputs
    if not resume_file:
        st.warning("Please upload your resume PDF.")
        st.stop()

    if jd_mode == "Paste text" and not jd_text_input.strip():
        st.warning("Please paste the job description.")
        st.stop()

    if jd_mode == "Upload PDF" and not jd_file:
        st.warning("Please upload the job description PDF.")
        st.stop()

    with st.spinner("Reading and analysing your resume..."):
        resume_text = extract_text_from_pdf(resume_file)

        if jd_mode == "Upload PDF":
            jd_text = extract_text_from_pdf(jd_file)
        else:
            jd_text = jd_text_input

        # Core analysis
        overall        = get_overall_score(resume_text, jd_text)
        section_res    = get_section_analysis(resume_text, jd_text)
        predicted      = get_predicted_score(overall, section_res)
        all_matched    = get_all_matched(section_res)
        all_missing    = get_all_missing(section_res)
        jd_keywords    = extract_jd_keywords(jd_text, top_n=60)
        label, _       = get_score_label(overall)
        gain           = round(predicted - overall, 1)

    st.markdown("---")

    # ── Score cards ───────────────────────────────────────────────────────────
    st.subheader("🎯 Your ATS Match Score")

    if overall >= 75:
        score_color = "c-green"
    elif overall >= 55:
        score_color = "c-blue"
    elif overall >= 35:
        score_color = "c-orange"
    else:
        score_color = "c-red"

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(
            f'<div class="score-card"><div class="score-num {score_color}">{overall}%</div>'
            f'<div class="score-sub">Current ATS Score</div>'
            f'<div class="score-sub"><strong>{label}</strong></div></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f'<div class="score-card"><div class="score-num c-blue">{predicted}%</div>'
            f'<div class="score-sub">Predicted Score</div>'
            f'<div class="score-sub">After all fixes</div></div>',
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            f'<div class="score-card"><div class="score-num c-green">+{gain}%</div>'
            f'<div class="score-sub">Potential Gain</div>'
            f'<div class="score-sub">If you apply recommendations</div></div>',
            unsafe_allow_html=True,
        )
    with s4:
        st.markdown(
            f'<div class="score-card"><div class="score-num" style="font-size:1.8rem">'
            f'{len(all_matched)}/{len(jd_keywords)}</div>'
            f'<div class="score-sub">Keywords Matched</div>'
            f'<div class="score-sub">out of JD keywords</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.progress(int(overall), text=f"Current score: {overall}%")
    st.progress(int(predicted), text=f"Predicted after improvements: {predicted}%")

    # ── What the JD is looking for ────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔎 What This JD Is Looking For")
    st.caption("These keywords were automatically extracted from the job description — no hardcoding.")
    st.markdown(
        " ".join(f'<span class="kw-blue">{k}</span>' for k in jd_keywords),
        unsafe_allow_html=True,
    )

    # ── Keyword match breakdown ───────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Keyword Match Breakdown")
    ka, kb = st.columns(2, gap="large")

    with ka:
        st.markdown(f"**✅ Matched Keywords** ({len(all_matched)})")
        if all_matched:
            st.markdown(
                " ".join(f'<span class="kw-green">{k}</span>' for k in all_matched),
                unsafe_allow_html=True,
            )
        else:
            st.error("No matching keywords found. Your resume needs significant updates.")

    with kb:
        st.markdown(f"**❌ Missing Keywords** ({len(all_missing)})")
        if all_missing:
            st.markdown(
                " ".join(f'<span class="kw-red">{k}</span>' for k in all_missing),
                unsafe_allow_html=True,
            )
        else:
            st.success("No missing keywords — excellent match!")

    # ── Section-wise analysis ─────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📂 Section-wise Analysis & Recommendations")
    st.caption("Each section of your resume is scored separately. Red sections need the most work.")

    for section, data in section_res.items():
        s = data["score"]
        if s >= 75:
            pill_cls, icon = "pill-green", "🟢"
        elif s >= 55:
            pill_cls, icon = "pill-blue", "🔵"
        elif s >= 35:
            pill_cls, icon = "pill-orange", "🟡"
        else:
            pill_cls, icon = "pill-red", "🔴"

        expand = s < 70  # auto-expand sections that need work
        with st.expander(
            f"{icon} {section}  —  {s}% match",
            expanded=expand,
        ):
            ea, eb = st.columns(2, gap="medium")
            with ea:
                st.markdown("**✅ Matched**")
                if data["matched"]:
                    st.markdown(
                        " ".join(f'<span class="kw-green">{k}</span>' for k in data["matched"]),
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Nothing matched in this section.")

            with eb:
                st.markdown("**❌ Missing**")
                if data["missing"]:
                    st.markdown(
                        " ".join(f'<span class="kw-red">{k}</span>' for k in data["missing"]),
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Nothing missing — great!")

            st.markdown("**💡 What to do:**")
            for rec in data["recommendations"]:
                st.markdown(f'<div class="rec-box">{rec}</div>', unsafe_allow_html=True)

    # ── Action plan summary ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🗺️ Your Priority Action Plan")

    # Sort sections by score ascending (most work needed first)
    sorted_secs = sorted(section_res.items(), key=lambda x: x[1]["score"])
    priority_items = [(sec, d) for sec, d in sorted_secs if d["score"] < 75]

    if priority_items:
        for i, (sec, d) in enumerate(priority_items[:4], 1):
            top_missing = d["missing"][:4]
            missing_str = ", ".join(top_missing) if top_missing else "see recommendations"
            st.markdown(
                f'<div class="rec-box">'
                f'<strong>Priority {i} — Fix your {sec} section</strong> '
                f'(currently {d["score"]}%)<br>'
                f'Add: <em>{missing_str}</em>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("Your resume is well optimised for this role! Focus on tailoring your summary and cover letter.")

    # ── Download report ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📥 Download Your Full Report")
    st.caption("A complete PDF report with all scores, keywords, and recommendations.")

    with st.spinner("Generating PDF..."):
        pdf_bytes = generate_pdf_report(
            overall, predicted, section_res,
            all_matched, all_missing,
        )

    st.download_button(
        label="⬇️ Download PDF Report",
        data=pdf_bytes,
        file_name="ats_resume_report.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary",
    )

    # ── Raw text debug ────────────────────────────────────────────────────────
    with st.expander("🔍 View extracted resume text (debug)"):
        st.text(resume_text[:3000])
    with st.expander("🔍 View extracted JD text (debug)"):
        st.text(jd_text[:2000])