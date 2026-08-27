"""Branding & styling bersama untuk seluruh halaman Raya Houses."""
import streamlit as st

GOLD = "#F2A93B"
GOLD_DARK = "#C9821A"
BLACK = "#141414"
CARD_BG = "#1F1F1F"

CSS = f"""
<style>
:root {{
    --gold: {GOLD};
}}
.rh-header {{
    display:flex; align-items:center; gap:14px;
    padding: 14px 20px; border-radius: 12px;
    background: linear-gradient(90deg, {BLACK} 0%, #2b2b2b 100%);
    margin-bottom: 18px;
    border: 1px solid {GOLD_DARK};
}}
.rh-header .rh-logo {{
    font-size: 30px; font-weight: 800; color: {GOLD};
    border: 2px solid {GOLD}; border-radius: 8px; padding: 2px 10px;
    font-family: 'Georgia', serif;
}}
.rh-header .rh-title {{
    color: {GOLD}; font-size: 22px; font-weight: 700; letter-spacing: 1px; margin:0;
}}
.rh-header .rh-subtitle {{
    color: #d9d9d9; font-size: 13px; margin:0;
}}
.rh-card {{
    background: {CARD_BG}; border-radius: 12px; padding: 16px;
    border: 1px solid #333; margin-bottom: 14px; color: #EAEAEA;
}}
.rh-card h2, .rh-card h3, .rh-card h4, .rh-card p, .rh-card li {{
    color: #EAEAEA !important;
}}
.rh-card hr {{
    border-color: #3a3a3a;
}}
.rh-badge {{
    display:inline-block; padding: 2px 10px; border-radius: 999px;
    font-size: 12px; font-weight: 600; margin-right: 6px;
}}
.badge-tersedia {{ background:#1e4620; color:#7CFC8B; }}
.badge-pending {{ background:#4a3a12; color:#F2C94C; }}
.badge-terjual {{ background:#4a1414; color:#FF8080; }}
.badge-disewa {{ background:#123a4a; color:#78D6FF; }}
.rh-price {{
    color: {GOLD}; font-weight: 700; font-size: 18px;
}}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="rh-header">
            <div class="rh-logo">R</div>
            <div>
                <p class="rh-title">RAYA HOUSES · {title}</p>
                <p class="rh-subtitle">{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    cls = {
        "Tersedia": "badge-tersedia",
        "Pending": "badge-pending",
        "Terjual": "badge-terjual",
        "Disewa": "badge-disewa",
    }.get(status, "badge-tersedia")
    return f'<span class="rh-badge {cls}">{status}</span>'


def format_rupiah(value) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "Rp 0"
    if abs(value) >= 1e9:
        return f"Rp {value/1e9:,.2f} M".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(value) >= 1e6:
        return f"Rp {value/1e6:,.0f} Jt".replace(",", ".")
    return f"Rp {value:,.0f}".replace(",", ".")
