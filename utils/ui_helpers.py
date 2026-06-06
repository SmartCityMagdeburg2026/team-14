"""Shared HTML components for the Smart City Magdeburg Dashboard."""
import base64
import os


def b64_icon(rel_path: str, size: str = "2rem", fallback: str = "") -> str:
    """Load an image from utils/icons/ and return an <img> tag for inline HTML use."""
    _base = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    _p = os.path.normpath(os.path.join(_base, rel_path))
    try:
        with open(_p, "rb") as _f:
            _b = base64.b64encode(_f.read()).decode()
        ext  = os.path.splitext(_p)[1].lstrip(".")
        mime = "image/gif" if ext == "gif" else f"image/{ext}"
        return (f"<img src='data:{mime};base64,{_b}' "
                f"style='width:{size};height:{size};object-fit:contain;vertical-align:middle;'>")
    except Exception:
        return fallback


def hero_stat(icon: str, value: str, description: str,
              delta_text: str, delta_positive: bool,
              color: str = "#007A6E") -> str:
    """Bold hero KPI block shown at the top of each page."""
    arrow = "↑" if delta_positive else "↓"
    delta_color = "#1B5E20" if delta_positive else "#B71C1C"
    delta_bg = "#E8F5E9" if delta_positive else "#FFEBEE"
    return f"""
<div style="background:linear-gradient(135deg,{color}18 0%,{color}04 100%);
            border-left:5px solid {color};border-radius:0 16px 16px 0;
            padding:24px 32px;margin-bottom:28px;">
  <div style="font-size:2.2rem;line-height:1;">{icon}</div>
  <div style="font-size:3rem;font-weight:800;color:#1A1A1A;line-height:1.15;margin-top:6px;">{value}</div>
  <div style="font-size:1.05rem;color:#555;margin-top:8px;">{description}</div>
  <div style="margin-top:12px;display:inline-block;background:{delta_bg};
              color:{delta_color};border-radius:20px;padding:4px 16px;
              font-size:0.88rem;font-weight:700;">{arrow}&nbsp;{delta_text}</div>
</div>
"""


def topic_card(icon: str, title: str, value: str, unit: str,
               delta_text: str, delta_positive: bool,
               year: str, color: str = "#007A6E",
               status: str = None, subtext: str = None,
               href: str = None) -> str:
    """Topic card for the Home page grid. Pass href to make the card clickable."""
    arrow = "↑" if delta_positive else "↓"
    delta_color = "#1B5E20" if delta_positive else "#B71C1C"
    delta_bg = "#E8F5E9" if delta_positive else "#FFEBEE"
    status_dot_map = {"good": "#22C55E", "watch": "#F59E0B", "alert": "#EF4444"}
    status_html = ""
    if status and status in status_dot_map:
        dot_color = status_dot_map[status]
        status_label = {"good": "Good", "watch": "Watch", "alert": "Alert"}[status]
        status_html = (
            f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'font-size:0.68rem;font-weight:700;color:{dot_color};margin-left:6px;">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:{dot_color};'
            f'display:inline-block;"></span>{status_label}</span>'
        )
    subtext_html = ""
    if subtext:
        subtext_html = (
            f'<div style="font-size:0.72rem;color:#94a3b8;margin-top:4px;'
            f'line-height:1.4;">{subtext}</div>'
        )
    click_attrs = (
        f'onclick="window.location.href=\'{href}\'" '
        f'style="cursor:pointer;" '
    ) if href else 'style=""'
    return (
        f'<div {click_attrs}>'
        f'<div style="background:#fff;border-radius:14px;padding:20px 18px;'
        f'box-shadow:0 2px 16px rgba(0,0,0,0.07);'
        f'border-top:4px solid {color};margin-bottom:4px;">'
        f'<div style="display:flex;align-items:flex-start;gap:14px;">'
        f'<div style="flex-shrink:0;font-size:2rem;line-height:1;margin-top:2px;">{icon}</div>'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
        f'<div style="font-size:0.7rem;font-weight:800;color:#999;text-transform:uppercase;'
        f'letter-spacing:0.12em;">{title}{status_html}</div>'
        f'<span style="font-size:0.68rem;color:#bbb;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.06em;">{year}</span>'
        f'</div>'
        f'<div style="font-size:1.9rem;font-weight:800;color:#1A1A1A;line-height:1.1;">{value}</div>'
        f'<div style="font-size:0.78rem;color:#bbb;margin-top:2px;margin-bottom:12px;">{unit}</div>'
        f'<div style="display:inline-block;background:{delta_bg};color:{delta_color};'
        f'border-radius:16px;padding:3px 12px;font-size:0.76rem;font-weight:700;">'
        f'{arrow}&nbsp;{delta_text}'
        f'</div>'
        f'{subtext_html}'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def live_card(icon: str, title: str, value: str, subtitle: str,
              status_color: str = "#007A6E") -> str:
    """Compact live-data indicator card — horizontal layout (icon left, text right)."""
    return f"""
<div style="background:#fff;border-radius:12px;padding:18px 16px;
            box-shadow:0 2px 12px rgba(0,0,0,0.06);
            border-left:4px solid {status_color};margin-bottom:4px;">
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="flex-shrink:0;font-size:1.8rem;line-height:1;">{icon}</div>
    <div>
      <div style="font-size:0.68rem;font-weight:800;color:#999;text-transform:uppercase;
                  letter-spacing:0.1em;margin-bottom:4px;">{title}</div>
      <div style="font-size:1.8rem;font-weight:800;color:#1A1A1A;line-height:1.1;">{value}</div>
      <div style="font-size:0.78rem;color:#999;margin-top:4px;">{subtitle}</div>
    </div>
  </div>
</div>
"""


def section_header(label: str, color: str = "#007A6E") -> str:
    """Styled section divider with a coloured left-bar."""
    return f"""
<div style="display:flex;align-items:center;gap:12px;margin:28px 0 16px 0;">
  <div style="width:4px;height:20px;background:{color};border-radius:2px;flex-shrink:0;"></div>
  <div style="font-size:0.7rem;font-weight:800;color:#64748b;
              text-transform:uppercase;letter-spacing:0.16em;white-space:nowrap;">{label}</div>
  <div style="flex:1;height:1px;background:#e2e8f0;"></div>
</div>
"""


def insight_box(text: str) -> str:
    """Plain-language insight callout shown below a chart."""
    return f"""
<div style="background:#f0faf8;border-left:4px solid #007A6E;border-radius:0 10px 10px 0;
            padding:11px 18px;margin:6px 0 22px 0;
            font-size:0.88rem;color:#1e4e47;line-height:1.55;font-weight:500;">
  \U0001f4a1 {text}
</div>
"""


GLOBAL_CSS = """
<style>
/* ── Streamlit chrome ──────────────────────────────────────── */
#MainMenu          { visibility: hidden; }
footer             { visibility: hidden; }
header             { visibility: hidden; }
[data-testid="stSidebar"]         { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }
[data-testid="stSidebarNav"]      { display: none !important; }
.nav-sentinel      { display: none; }

/* ── Main content padding ───────────────────────────────────── */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1160px;
}

/* ── Nav page_link styling ─────────────────────────────── */
[data-testid="stPageLink"] a {
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    text-decoration: none !important;
    display: flex !important;
    justify-content: center !important;
    padding: 2px 8px 4px !important;
}
[data-testid="stPageLink"] a:hover { color: #007A6E !important; }

/* ── Typography ─────────────────────────────────────────── */
h1 { font-size: 2.1rem !important; font-weight: 800 !important; color: #1A1A1A !important; }
h2 { font-size: 1.35rem !important; font-weight: 700 !important; color: #2A2A2A !important; }
h3 { font-size: 1.1rem  !important; font-weight: 700 !important; }
.js-plotly-plot { border-radius: 12px; }
hr { border-color: #e8ecec !important; }
.stCaption, caption { color: #999 !important; font-size: 0.78rem !important; }
</style>
"""
