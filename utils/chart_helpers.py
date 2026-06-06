import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.constants import PLOTLY_TEMPLATE, MD_TEAL


def _base_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=dict(text=title, font=dict(size=15)),
        font=dict(family="sans-serif", size=12),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str | list,
    title: str,
    y_label: str = "",
    color: str | None = None,
) -> go.Figure:
    if isinstance(y, list):
        fig = go.Figure()
        colours = px.colors.qualitative.Set2
        for i, col in enumerate(y):
            fig.add_trace(go.Scatter(
                x=df[x], y=df[col], mode="lines", name=col,
                line=dict(color=colours[i % len(colours)]),
            ))
    else:
        fig = go.Figure(go.Scatter(
            x=df[x], y=df[y], mode="lines",
            line=dict(color=color or MD_TEAL),
            name=y,
        ))
    fig.update_yaxes(title_text=y_label)
    return _base_layout(fig, title)


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    orientation: str = "v",
    color: str | None = None,
    color_discrete_map: dict | None = None,
) -> go.Figure:
    if orientation == "h":
        fig = go.Figure(go.Bar(
            y=df[x], x=df[y], orientation="h",
            marker_color=color or MD_TEAL,
        ))
    else:
        fig = go.Figure(go.Bar(
            x=df[x], y=df[y],
            marker_color=color or MD_TEAL,
        ))
    return _base_layout(fig, title)


def heatmap(
    pivot_df: pd.DataFrame,
    title: str,
    colorscale: str = "RdYlGn",
    zmin: float | None = None,
    zmax: float | None = None,
    x_label: str = "",
    y_label: str = "",
) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns.tolist(),
        y=pivot_df.index.tolist(),
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax,
        colorbar=dict(thickness=12),
    ))
    fig.update_xaxes(title_text=x_label)
    fig.update_yaxes(title_text=y_label)
    return _base_layout(fig, title)
