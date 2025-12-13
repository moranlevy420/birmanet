"""
Reusable chart components.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional

from config.settings import COLORS


def apply_chart_style(
    fig: go.Figure, 
    height: int = 400, 
    show_legend: bool = True, 
    is_time_series: bool = False, 
    historical_df: Optional[pd.DataFrame] = None
) -> go.Figure:
    """Apply consistent chart styling across all charts."""
    layout_opts = {
        'height': height,
        'hovermode': 'closest',
        'yaxis': dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.3)',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='rgba(128,128,128,0.5)'
        )
    }
    
    if show_legend:
        layout_opts['legend'] = dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=10)
        )
        layout_opts['margin'] = dict(t=50, b=80, r=150, l=50)
    else:
        layout_opts['showlegend'] = False
        layout_opts['margin'] = dict(t=50, b=80, r=30, l=50)
    
    if is_time_series and historical_df is not None:
        layout_opts['xaxis'] = dict(
            tickformat='%Y/%m',
            tickmode='array',
            tickvals=historical_df['REPORT_DATE'].unique() if 'REPORT_DATE' in historical_df.columns else None,
            tickangle=-45,
            showticklabels=True,
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            gridwidth=1
        )
    else:
        layout_opts['xaxis'] = dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            gridwidth=1
        )
    
    fig.update_layout(**layout_opts)
    return fig


def create_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str = "",
    labels: Optional[dict] = None,
    custom_data: Optional[List[str]] = None,
    height: int = 320,
    show_markers: bool = True,
    category_orders: Optional[dict] = None
) -> go.Figure:
    """Create a styled line chart."""
    fig = px.line(
        df.sort_values([color, x]) if color in df.columns else df,
        x=x,
        y=y,
        color=color,
        custom_data=custom_data,
        labels=labels or {},
        color_discrete_sequence=COLORS,
        category_orders=category_orders
    )
    
    if title:
        fig.update_layout(title=title)
    
    if show_markers:
        fig.update_traces(mode='lines+markers')
    
    fig = apply_chart_style(fig, height=height, is_time_series=True, historical_df=df)
    
    return fig


def create_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    orientation: str = 'v',
    title: str = "",
    labels: Optional[dict] = None,
    color: Optional[str] = None,
    color_scale: str = 'Viridis',
    height: int = 400
) -> go.Figure:
    """Create a styled bar chart."""
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation=orientation,
        title=title,
        labels=labels or {},
        color=color or (x if orientation == 'h' else y),
        color_continuous_scale=color_scale
    )
    
    fig = apply_chart_style(fig, height=height, show_legend=False)
    
    if orientation == 'h':
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    
    return fig


def create_scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    size: Optional[str] = None,
    color: Optional[str] = None,
    hover_name: Optional[str] = None,
    title: str = "",
    labels: Optional[dict] = None,
    height: int = 400
) -> go.Figure:
    """Create a styled scatter chart."""
    fig = px.scatter(
        df,
        x=x,
        y=y,
        size=size,
        color=color,
        hover_name=hover_name,
        title=title,
        labels=labels or {},
        color_discrete_sequence=COLORS
    )
    
    fig = apply_chart_style(fig, height=height)
    
    return fig


def create_histogram(
    df: pd.DataFrame,
    x: str,
    nbins: int = 30,
    title: str = "",
    labels: Optional[dict] = None,
    add_mean_line: bool = True,
    height: int = 400
) -> go.Figure:
    """Create a styled histogram."""
    fig = px.histogram(
        df,
        x=x,
        nbins=nbins,
        title=title,
        labels=labels or {},
        color_discrete_sequence=['#2563eb']
    )
    
    if add_mean_line and x in df.columns:
        mean_val = df[x].mean()
        fig.add_vline(
            x=mean_val, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"Mean: {mean_val:.2f}"
        )
    
    fig = apply_chart_style(fig, height=height, show_legend=False)
    
    return fig


def create_pie_chart(
    df: pd.DataFrame,
    values: str,
    names: str,
    title: str = "",
    height: int = 350
) -> go.Figure:
    """Create a styled pie chart."""
    fig = px.pie(
        df,
        values=values,
        names=names,
        title=title,
        color_discrete_sequence=COLORS
    )
    
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Value: %{value:,.0f}<br>%{percent}<extra></extra>'
    )
    
    fig = apply_chart_style(fig, height=height)
    
    return fig


def create_multi_subplot(
    data: List[dict],
    rows: int = 2,
    cols: int = 2,
    titles: Optional[List[str]] = None,
    height: int = 700
) -> go.Figure:
    """
    Create a multi-subplot figure.
    
    Args:
        data: List of dicts with 'x', 'y', 'name', 'color' keys
        rows: Number of rows
        cols: Number of columns
        titles: List of subplot titles
        height: Figure height
        
    Returns:
        Plotly figure
    """
    fig = make_subplots(
        rows=rows, 
        cols=cols,
        subplot_titles=titles,
        vertical_spacing=0.18,
        horizontal_spacing=0.10
    )
    
    for i, trace_data in enumerate(data):
        row = (i // cols) + 1
        col = (i % cols) + 1
        
        fig.add_trace(
            go.Scatter(
                x=trace_data['x'],
                y=trace_data['y'],
                mode='lines+markers',
                name=trace_data.get('name', f'Series {i+1}'),
                line=dict(color=trace_data.get('color', COLORS[i % len(COLORS)])),
                hovertemplate='%{x|%Y/%m}: %{y:.2f}<extra></extra>'
            ),
            row=row, col=col
        )
    
    fig.update_layout(
        height=height,
        showlegend=False,
        hovermode='closest'
    )
    
    fig.update_xaxes(
        tickformat='%Y/%m',
        tickangle=-45,
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor='rgba(128,128,128,0.3)',
        zeroline=True,
        zerolinecolor='rgba(128,128,128,0.5)'
    )
    
    return fig

