import ast
import html
import re

import streamlit as st

from agent import ShoppingAgent


# ============================================================
# HELPERS
# ============================================================

def render_html(content: str):
    """
    Render actual HTML instead of sending it through Streamlit's
    Markdown renderer.

    This is the key fix for the issue where <div>, <strong>, etc.
    were appearing literally on the webpage.
    """
    st.html(content)


def render_markdown_to_html(text: str) -> str:
    """
    Convert the limited Markdown normally produced by the AI
    response into safe HTML.

    Raw HTML is escaped first so model-generated HTML cannot
    break the surrounding page.
    """
    escaped = html.escape(str(text))
    lines = escaped.splitlines()

    parts = []
    list_type = None
    paragraph_lines = []

    def flush_paragraph():
        if paragraph_lines:
            parts.append("<p>" + " ".join(paragraph_lines) + "</p>")
            paragraph_lines.clear()

    def close_list():
        nonlocal list_type

        if list_type:
            parts.append(f"</{list_type}>")
            list_type = None

    def inline(segment: str) -> str:
        # Bold
        segment = re.sub(
            r"\*\*(.+?)\*\*",
            r"<strong>\1</strong>",
            segment,
        )

        # Italic
        segment = re.sub(
            r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
            r"<em>\1</em>",
            segment,
        )

        return segment

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            flush_paragraph()
            close_list()
            continue

        # Headings
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)

        if heading_match:
            flush_paragraph()
            close_list()

            level = min(len(heading_match.group(1)) + 2, 6)

            parts.append(
                f"<h{level}>{inline(heading_match.group(2))}</h{level}>"
            )

            continue

        # Bullet list
        bullet_match = re.match(r"^[-*]\s+(.+)", line)

        if bullet_match:
            flush_paragraph()

            if list_type != "ul":
                close_list()
                parts.append("<ul>")
                list_type = "ul"

            parts.append(
                f"<li>{inline(bullet_match.group(1))}</li>"
            )

            continue

        # Numbered list
        numbered_match = re.match(r"^\d+[.)]\s+(.+)", line)

        if numbered_match:
            flush_paragraph()

            if list_type != "ol":
                close_list()
                parts.append("<ol>")
                list_type = "ol"

            parts.append(
                f"<li>{inline(numbered_match.group(1))}</li>"
            )

            continue

        close_list()
        paragraph_lines.append(inline(line))

    flush_paragraph()
    close_list()

    return "\n".join(parts)


def flatten_tradeoff_value(value) -> list:
    """
    Recursively flatten trade-off values into clean strings.

    Handles:
    - list
    - tuple
    - set
    - plain string
    - string representation of a Python list
    """

    if isinstance(value, (list, tuple, set)):
        items = []

        for item in value:
            items.extend(flatten_tradeoff_value(item))

        return items

    if isinstance(value, str):
        stripped = value.strip()

        # Handle strings such as:
        # "['costs ₹200 less', 'has lower battery']"
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = ast.literal_eval(stripped)
            except (ValueError, SyntaxError):
                parsed = None

            if isinstance(parsed, (list, tuple, set)):
                items = []

                for item in parsed:
                    items.extend(flatten_tradeoff_value(item))

                return items

        return [stripped] if stripped else []

    return [str(value)]


def tradeoff_items(tradeoff) -> list:
    """
    Convert the agent's trade-off payload into a clean,
    deduplicated list of strings.
    """

    if isinstance(tradeoff, dict):
        raw_values = list(tradeoff.values())
    else:
        raw_values = [tradeoff]

    items = []

    for value in raw_values:
        items.extend(flatten_tradeoff_value(value))

    seen = set()
    clean = []

    for item in items:
        if item and item not in seen:
            seen.add(item)
            clean.append(item)

    return clean


def preference_pills(preferences) -> list:
    """
    Build preference badges describing what the agent understood.
    """

    pills = []

    if preferences is None:
        return pills

    if preferences.budget is not None:
        pills.append(
            f"""
            <span class="preference">
                <strong>Budget</strong>
                ₹{preferences.budget:.0f}
            </span>
            """
        )

    if preferences.min_playtime is not None:
        pills.append(
            f"""
            <span class="preference">
                <strong>Battery</strong>
                {preferences.min_playtime:.0f}+ hrs
            </span>
            """
        )

    if preferences.gaming:
        pills.append(
            """
            <span class="preference">
                <strong>Gaming</strong> Required
            </span>
            """
        )

    if preferences.anc:
        pills.append(
            """
            <span class="preference">
                <strong>ANC</strong> Required
            </span>
            """
        )

    if preferences.enc:
        pills.append(
            """
            <span class="preference">
                <strong>ENC</strong> Required
            </span>
            """
        )

    if preferences.connectivity:
        pills.append(
            f"""
            <span class="preference">
                <strong>Connection</strong>
                {html.escape(str(preferences.connectivity))}
            </span>
            """
        )

    return pills


def render_preference_pills(preferences):
    pills = preference_pills(preferences)

    if pills:
        render_html(
            '<div class="preference-row">'
            + "".join(pills)
            + "</div>"
        )


# ============================================================
# RESULT RENDERER
# ============================================================

def render_result(result):
    """
    Render one complete assistant result.

    Supports:
    - clarification questions
    - understood preferences
    - top recommendation
    - explanation
    - ranking breakdown
    - alternatives
    - trade-offs
    - AI decision analysis
    """

    if result is None:
        return

    # --------------------------------------------------------
    # FOLLOW-UP
    # --------------------------------------------------------

    if result.get("type") == "follow_up":

        follow_up = result.get("follow_up")

        if follow_up:
            render_html(
                f"""
                <div class="follow-up-text">
                    {html.escape(str(follow_up))}
                </div>
                """
            )

        preferences = result.get("preferences")

        if preferences:
            render_html(
                """
                <div class="section-label">
                    What I understood so far
                </div>
                """
            )

            render_preference_pills(preferences)

        return

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    if result.get("type") != "results":
        return

    preferences = result.get("preferences")
    recommendations = result.get("recommendations", [])

    # --------------------------------------------------------
    # NO RESULTS
    # --------------------------------------------------------

    if not recommendations:
        render_html(
            """
            <div class="empty-state">
                <div style="
                    font-family:'Space Grotesk', sans-serif;
                    font-size:1.1rem;
                    font-weight:700;
                    color:var(--text);
                    margin-bottom:.5rem;
                ">
                    No products matched your requirements.
                </div>

                <div>
                    Try increasing your budget or relaxing one
                    of your must-have features.
                </div>
            </div>
            """
        )

        return

    # --------------------------------------------------------
    # UNDERSTOOD
    # --------------------------------------------------------

    render_html(
        """
        <div class="section-label">
            What I understood
        </div>
        """
    )

    render_preference_pills(preferences)

    # --------------------------------------------------------
    # TOP MATCH
    # --------------------------------------------------------

    best = recommendations[0]

    product = best["product"]
    explanation = best.get("explanation", {})
    breakdown = best.get("score_breakdown", {})

    title = html.escape(str(product["Title"]))
    price = float(product["Selling_Price"])
    score = float(best["final_score"])

    render_html(
        """
        <div class="section-label">
            Top match
        </div>
        """
    )

    render_html(
        f"""
        <div class="top-card">

            <div class="rank-label">
                Best overall match
            </div>

            <div class="product-name">
                {title}
            </div>

            <div class="product-price">
                ₹{price:,.0f}
            </div>

            <div class="score-wrapper">

                <div class="score-box">

                    <div class="score-caption">
                        Recommendation score
                    </div>

                    <div class="score-number">
                        {score:.3f}
                    </div>

                </div>

            </div>

        </div>
        """
    )

    # --------------------------------------------------------
    # WHY THIS WON
    # --------------------------------------------------------

    reasons = (
        explanation.get("reasons", [])
        if isinstance(explanation, dict)
        else []
    )

    if reasons:

        render_html(
            """
            <div class="section-label">
                Why this won
            </div>
            """
        )

        reason_html = ""

        for reason in reasons:
            reason_html += f"""
            <div class="reason-item">
                {html.escape(str(reason))}
            </div>
            """

        render_html(
            f"""
            <div class="reason-card">

                <div class="reason-title">
                    What the engine found
                </div>

                {reason_html}

            </div>
            """
        )

    # --------------------------------------------------------
    # RANKING LOGIC
    # --------------------------------------------------------

    if breakdown:

        render_html(
            """
            <div class="section-label">
                Ranking logic
            </div>
            """
        )

        rows = []

        for name, values in breakdown.items():

            if not isinstance(values, dict):
                continue

            contribution = float(
                values.get("contribution", 0)
            )

            weight = float(
                values.get("weight", 0)
            )

            feature_score = float(
                values.get("feature_score", 0)
            )

            rows.append(
                (
                    name,
                    contribution,
                    weight,
                    feature_score,
                )
            )

        rows.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        breakdown_html = ""

        for name, contribution, weight, feature_score in rows:

            width = min(
                max(feature_score * 100, 0),
                100,
            )

            display_name = (
                html.escape(str(name))
                .replace("_", " ")
                .title()
            )

            breakdown_html += f"""
            <div class="breakdown-row">

                <div class="breakdown-top">

                    <span class="breakdown-name">
                        {display_name}
                    </span>

                    <span class="breakdown-value">
                        +{contribution:.3f}
                    </span>

                </div>

                <div class="bar">
                    <div
                        class="bar-fill"
                        style="width:{width:.2f}%"
                    ></div>
                </div>

                <div class="breakdown-meta">
                    Priority weight: {weight:.3f}
                    &nbsp; | &nbsp;
                    Feature score: {feature_score:.3f}
                </div>

            </div>
            """

        render_html(
            f"""
            <div class="breakdown-card">

                <div class="breakdown-title">
                    What influenced the ranking
                </div>

                {breakdown_html}

            </div>
            """
        )

    # --------------------------------------------------------
    # ALTERNATIVES
    # --------------------------------------------------------

    if len(recommendations) > 1:

        render_html(
            """
            <div class="section-label">
                Other strong matches
            </div>
            """
        )

        alt_items = recommendations[1:3]

        cols = st.columns(len(alt_items))

        for index, item in enumerate(alt_items):

            product_alt = item["product"]

            with cols[index]:

                rec_title = html.escape(
                    str(product_alt["Title"])
                )

                rec_price = float(
                    product_alt["Selling_Price"]
                )

                rec_score = float(
                    item["final_score"]
                )

                render_html(
                    f"""
                    <div class="rec-card">

                        <div class="rec-number">
                            ALTERNATIVE {index + 1}
                        </div>

                        <div class="rec-title">
                            {rec_title}
                        </div>

                        <div class="rec-price">
                            ₹{rec_price:,.0f}
                        </div>

                        <div class="rec-score">
                            Score {rec_score:.3f}
                        </div>

                    </div>
                    """
                )

    # --------------------------------------------------------
    # TRADE-OFF
    # --------------------------------------------------------

    tradeoff = result.get("tradeoff")

    if tradeoff:

        clean_items = tradeoff_items(tradeoff)

        if clean_items:

            render_html(
                """
                <div class="section-label">
                    Trade-off
                </div>
                """
            )

            bullets = ""

            for item in clean_items:

                clean_text = (
                    item[0].upper() + item[1:]
                    if item
                    else item
                )

                bullets += (
                    f"<li>{html.escape(clean_text)}</li>"
                )

            render_html(
                f"""
                <div class="tradeoff">

                    <strong>
    Where the alternatives differ from the top match
</strong>

                    <ul>
                        {bullets}
                    </ul>

                </div>
                """
            )

    # --------------------------------------------------------
    # AI DECISION ANALYSIS
    # --------------------------------------------------------

    gemini_response = result.get("gemini_response")

    if gemini_response:

        render_html(
            """
            <div class="section-label">
                Decision analysis
            </div>
            """
        )

        gemini_html = render_markdown_to_html(
            gemini_response
        )

        render_html(
            f"""
            <div class="ai-card">

                <div class="ai-label">
                    AI Decision Analysis
                </div>

                <div class="ai-content">
                    {gemini_html}
                </div>

            </div>
            """
        )


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Shopping Decision Agent",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# SESSION STATE
# ============================================================

if "theme_toggle" not in st.session_state:
    st.session_state.theme_toggle = False

if "agent" not in st.session_state:
    st.session_state.agent = ShoppingAgent()

if "turns" not in st.session_state:
    st.session_state.turns = []


def reset_chat():
    st.session_state.agent = ShoppingAgent()
    st.session_state.turns = []


# ============================================================
# THEMES
# ============================================================

AMBER_THEME = {
    "bg": "#18120F",
    "surface": "#241B17",
    "surface_2": "#2B211C",
    "text": "#F4EDE4",
    "muted": "#B8A79A",
    "label": "#C7A98C",
    "border": "#403129",
    "accent": "#D5A84A",
    "accent_hover": "#E1B961",
    "accent_soft": "rgba(213, 168, 74, 0.14)",
    "secondary": "#C8795D",
    "secondary_soft": "rgba(200, 121, 93, 0.14)",
    "hero": "#211713",
    "hero_text": "#F8F0E7",
    "hero_muted": "#CDBCAF",
    "score_bg": "#30231D",
    "track": "#574237",
    "shadow": "0, 0, 0",
}

CYBER_THEME = {
    "bg": "#0F1226",
    "surface": "#171B36",
    "surface_2": "#1E2444",
    "text": "#EDEFFB",
    "muted": "#9AA0C7",
    "label": "#7FE7C4",
    "border": "#2C3260",
    "accent": "#37E8B0",
    "accent_hover": "#2BC99A",
    "accent_soft": "rgba(55, 232, 176, 0.14)",
    "secondary": "#FF6FA5",
    "secondary_soft": "rgba(255, 111, 165, 0.14)",
    "hero": "#0B0E22",
    "hero_text": "#F4F5FF",
    "hero_muted": "#B7BEE8",
    "score_bg": "#12163A",
    "track": "#2A2F5C",
    "shadow": "5, 8, 30",
}

theme = (
    CYBER_THEME
    if st.session_state.theme_toggle
    else AMBER_THEME
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap'
    );

    :root {{
        --bg: {theme["bg"]};
        --surface: {theme["surface"]};
        --surface-2: {theme["surface_2"]};
        --text: {theme["text"]};
        --muted: {theme["muted"]};
        --label: {theme["label"]};
        --border: {theme["border"]};
        --accent: {theme["accent"]};
        --accent-hover: {theme["accent_hover"]};
        --accent-soft: {theme["accent_soft"]};
        --secondary: {theme["secondary"]};
        --secondary-soft: {theme["secondary_soft"]};
        --hero: {theme["hero"]};
        --hero-text: {theme["hero_text"]};
        --hero-muted: {theme["hero_muted"]};
        --score-bg: {theme["score_bg"]};
        --track: {theme["track"]};
        --shadow: {theme["shadow"]};
    }}

    html,
    body,
    [class*="css"] {{
        font-family: "DM Sans", sans-serif;
    }}

    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"] {{
        background: var(--bg);
    }}

    .stApp {{
        color: var(--text);
    }}

    .block-container {{
        max-width: 900px;
        padding-top: 1.2rem;
        padding-bottom: 7rem;
    }}

    #MainMenu,
    footer,
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {{
        display: none !important;
    }}


    /* ========================================================
       NAV BAR
       ======================================================== */

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.brand) {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: .3rem .6rem;
        margin-bottom: 1.4rem;
    }}

    .brand {{
        display: flex;
        align-items: center;
        gap: .6rem;
        height: 100%;
        font-family: "Space Grotesk", sans-serif;
        font-weight: 700;
        font-size: 1.02rem;
        color: var(--text);
        padding: .5rem 0;
    }}

    [data-testid="stWidgetLabel"] p {{
        font-size: .85rem;
        font-weight: 600;
    }}

    div[data-baseweb="toggle"] > div {{
        background: var(--track) !important;
    }}

    div[data-baseweb="toggle"][aria-checked="true"] > div {{
        background: var(--accent) !important;
    }}


    /* ========================================================
       CHAT
       ======================================================== */

    [data-testid="stChatMessage"] {{
        border-radius: 18px;
        padding: .5rem .7rem;
        margin-bottom: 1rem;
        border: 1px solid var(--border);
        max-width: 82%;
        background: var(--surface);
    }}

    [data-testid="stChatMessage"]:has(
        [data-testid="stChatMessageAvatarUser"]
    ) {{
        background: var(--accent-soft);
        border-color: var(--accent);
        flex-direction: row-reverse;
        margin-left: auto;
    }}

    [data-testid="stChatMessage"]:has(
        [data-testid="stChatMessageAvatarAssistant"]
    ) {{
        background: var(--surface);
        margin-right: auto;
    }}

    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"] {{
        background: var(--surface-2) !important;
        border: 1px solid var(--border);
    }}

    [data-testid="stChatInput"] textarea {{
        background: var(--surface) !important;
        color: var(--text) !important;
    }}

    [data-testid="stChatInput"] {{
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
    }}


    /* ========================================================
       FOLLOW UP
       ======================================================== */

    .follow-up-text {{
        color: var(--text);
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.05rem;
        line-height: 1.5;
        margin-bottom: .6rem;
    }}


    /* ========================================================
       HERO
       ======================================================== */

    .hero {{
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(
                circle at 88% 12%,
                rgba(213,168,74,.22),
                transparent 27%
            ),
            radial-gradient(
                circle at 75% 105%,
                rgba(200,121,93,.16),
                transparent 28%
            ),
            var(--hero);

        border: 1px solid rgba(255,255,255,.07);
        border-radius: 26px;
        padding: 2.6rem 2.8rem;
        margin-bottom: 1.6rem;
        box-shadow:
            0 24px 60px
            rgba(var(--shadow), .24);
    }}

    .hero-content {{
        max-width: 720px;
    }}

    .hero-kicker {{
        color: var(--accent);
        font-size: .72rem;
        font-weight: 700;
        letter-spacing: .18em;
        text-transform: uppercase;
        margin-bottom: .9rem;
    }}

    .hero h1 {{
        font-family: "Space Grotesk", sans-serif;
        color: var(--hero-text);
        font-size: clamp(2rem, 4.5vw, 3.1rem);
        line-height: 1.05;
        letter-spacing: -.04em;
        margin: 0;
    }}

    .hero p {{
        color: var(--hero-muted);
        max-width: 650px;
        font-size: 1rem;
        line-height: 1.7;
        margin-top: 1rem;
    }}

    .hero-examples {{
        margin-top: 1.3rem;
        display: flex;
        flex-wrap: wrap;
        gap: .5rem;
    }}

    .hero-examples span {{
        color: var(--hero-muted);
        border: 1px solid rgba(255,255,255,.14);
        border-radius: 999px;
        padding: .45rem .85rem;
        font-size: .82rem;
    }}


    /* ========================================================
       SECTION LABEL
       ======================================================== */

    .section-label {{
        color: var(--label);
        font-size: .68rem;
        font-weight: 700;
        letter-spacing: .18em;
        text-transform: uppercase;
        margin-top: 1.4rem;
        margin-bottom: .6rem;
    }}


    /* ========================================================
       PREFERENCE PILLS
       ======================================================== */

    .preference-row {{
        display: flex;
        flex-wrap: wrap;
        gap: .55rem;
        margin-bottom: .6rem;
    }}

    .preference {{
        display: inline-block;
        background: var(--surface-2);
        border: 1px solid var(--border);
        color: var(--text);
        border-radius: 999px;
        padding: .5rem .8rem;
        font-size: .8rem;
    }}

    .preference strong {{
        color: var(--accent);
        margin-right: .2rem;
    }}


    /* ========================================================
       GENERAL CARDS
       ======================================================== */

    .top-card,
    .rec-card,
    .reason-card,
    .ai-card {{
        background: var(--surface-2);
        border: 1px solid var(--border);
        box-shadow:
            0 14px 38px
            rgba(var(--shadow), .08);
    }}


    /* ========================================================
       TOP CARD
       ======================================================== */

    .top-card {{
        border-radius: 20px;
        padding: 1.6rem 1.8rem;
    }}

    .rank-label {{
        display: inline-block;
        color: var(--accent);
        background: var(--accent-soft);
        border-radius: 999px;
        padding: .34rem .68rem;
        font-size: .68rem;
        font-weight: 700;
        text-transform: uppercase;
    }}

    .product-name {{
        font-family: "Space Grotesk", sans-serif;
        color: var(--text);
        font-size: 1.28rem;
        font-weight: 700;
        line-height: 1.35;
        margin-top: .9rem;
    }}

    .product-price {{
        color: var(--accent);
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.7rem;
        font-weight: 700;
        margin-top: .6rem;
    }}

    .score-wrapper {{
        margin-top: 1rem;
        max-width: 210px;
    }}

    .score-box {{
        background: var(--score-bg);
        border-radius: 14px;
        padding: .8rem 1rem;
        text-align: center;
    }}

    .score-caption {{
        color: var(--hero-muted);
        font-size: .65rem;
        text-transform: uppercase;
    }}

    .score-number {{
        color: var(--accent);
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.7rem;
        font-weight: 700;
    }}


    /* ========================================================
       REASONS
       ======================================================== */

    .reason-card {{
        border-radius: 18px;
        padding: 1.2rem 1.4rem;
    }}

    .reason-title {{
        color: var(--text);
        font-family: "Space Grotesk", sans-serif;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: .5rem;
    }}

    .reason-item {{
        color: var(--muted);
        padding: .6rem 0;
        border-bottom: 1px solid var(--border);
        line-height: 1.5;
    }}

    .reason-item:last-child {{
        border-bottom: none;
    }}


    /* ========================================================
       BREAKDOWN
       ======================================================== */

    .breakdown-card {{
        background: var(--score-bg);
        border-radius: 19px;
        padding: 1.4rem;
        color: var(--text);
    }}

    .breakdown-title {{
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }}

    .breakdown-row {{
        margin-bottom: .9rem;
    }}

    .breakdown-top {{
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: .35rem;
    }}

    .breakdown-name {{
        color: var(--hero-text);
        font-weight: 600;
    }}

    .breakdown-value {{
        color: var(--accent);
        font-weight: 700;
    }}

    .bar {{
        height: 6px;
        border-radius: 999px;
        background: var(--track);
        overflow: hidden;
    }}

    .bar-fill {{
        height: 100%;
        border-radius: 999px;
        background: var(--accent);
    }}

    .breakdown-meta {{
        margin-top: .3rem;
        color: var(--hero-muted);
        font-size: .68rem;
    }}


    /* ========================================================
       ALTERNATIVES
       ======================================================== */

    .rec-card {{
        border-radius: 17px;
        padding: 1.2rem;
        height: 100%;
    }}

    .rec-number {{
        color: var(--secondary);
        font-size: .65rem;
        font-weight: 700;
        letter-spacing: .12em;
    }}

    .rec-title {{
        color: var(--text);
        font-family: "Space Grotesk", sans-serif;
        font-size: .95rem;
        font-weight: 700;
        line-height: 1.4;
        margin-top: .5rem;
    }}

    .rec-price {{
        color: var(--accent);
        font-size: 1.2rem;
        font-weight: 700;
        margin-top: .6rem;
    }}

    .rec-score {{
        display: inline-block;
        margin-top: .5rem;
        padding: .3rem .6rem;
        border-radius: 999px;
        background: var(--secondary-soft);
        color: var(--secondary);
        font-size: .7rem;
        font-weight: 700;
    }}


    /* ========================================================
       TRADE-OFF
       ======================================================== */

    .tradeoff {{
        background: var(--secondary-soft);
        border-left: 4px solid var(--secondary);
        border-radius: 14px;
        padding: 1.05rem 1.2rem;
        color: var(--text);
        line-height: 1.5;
    }}

    .tradeoff ul {{
        margin: .6rem 0 0;
        padding-left: 1.2rem;
    }}

    .tradeoff li {{
        margin-bottom: .25rem;
    }}


    /* ========================================================
       AI CARD
       ======================================================== */

    .ai-card {{
        border-radius: 19px;
        padding: 1.5rem 1.7rem;
        line-height: 1.6;
    }}

    .ai-content p,
    .ai-content li {{
        color: var(--text);
    }}

    .ai-content ul,
    .ai-content ol {{
        padding-left: 1.3rem;
        margin: .5rem 0;
    }}

    .ai-content strong {{
        color: var(--text);
    }}

    .ai-content h3,
    .ai-content h4,
    .ai-content h5,
    .ai-content h6 {{
        color: var(--text);
        font-family: "Space Grotesk", sans-serif;
    }}

    .ai-label {{
        color: var(--accent);
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }}


    /* ========================================================
       EMPTY STATE
       ======================================================== */

    .empty-state {{
        text-align: center;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 2.4rem 1.5rem;
        color: var(--muted);
    }}


    /* ========================================================
       STREAMLIT HTML CONTAINER
       ======================================================== */

    [data-testid="stHtml"] {{
        width: 100%;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TOP BAR
# ============================================================

with st.container(border=True):

    nav_brand, nav_toggle, nav_reset = st.columns(
        [6, 2.4, 2]
    )

    with nav_brand:

        st.markdown(
            """
            <div class="brand">
                🎧
                <span>Shopping Decision Agent</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with nav_toggle:

        st.toggle(
            "🟢 Cyber Mint"
            if st.session_state.theme_toggle
            else "🟠 Amber Study",
            key="theme_toggle",
        )

    with nav_reset:

        if st.button(
            "Reset",
            use_container_width=True,
        ):
            reset_chat()
            st.rerun()


# ============================================================
# WELCOME / HERO
# ============================================================

if not st.session_state.turns:

    render_html(
        """
        <div class="hero">

            <div class="hero-content">

                <div class="hero-kicker">
                    Shopping Decision Agent
                </div>

                <h1>
                    Shopping, without the guesswork.
                </h1>

                <p>
                    Tell me what matters to you - budget,
                    must-have features, what you'll use it for -
                    and I'll rank the options and explain the
                    trade-offs, right here in chat.
                </p>

                <div class="hero-examples">

                    <span>
                        gaming earbuds under ₹1500
                    </span>

                    <span>
                        ANC headphones for travel
                    </span>

                    <span>
                        30+ hour battery life
                    </span>

                </div>

            </div>

        </div>
        """
    )


# ============================================================
# CONVERSATION
# ============================================================

for turn in st.session_state.turns:

    with st.chat_message(
        "user",
        avatar="🛒",
    ):
        st.write(turn["query"])

    with st.chat_message(
        "assistant",
        avatar="🎧",
    ):
        render_result(turn["result"])


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Describe what you're looking for, e.g. gaming earbuds under ₹1500 with 30+ hours battery"
)

if prompt:

    with st.chat_message(
        "user",
        avatar="🛒",
    ):
        st.write(prompt)

    with st.chat_message(
        "assistant",
        avatar="🎧",
    ):

        with st.spinner("Thinking..."):

            result = st.session_state.agent.process(prompt)

        render_result(result)

    st.session_state.turns.append(
        {
            "query": prompt,
            "result": result,
        }
    )