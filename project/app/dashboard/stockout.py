import pandas as pd
import plotly.graph_objects as go
from project.config import download_from_gcs

def create_stockout_scorecard(stockout_ratio):
    # Calculate Current
    stockout_yr_q = sorted(stockout_ratio['Year_Quarter'].unique())
    latest_stockout_ratio = stockout_ratio[stockout_ratio['Year_Quarter'] == stockout_ratio['Year_Quarter'].max()]['stockout_ratio'].values[0]
    latestmin1_stockout_ratio = stockout_ratio[stockout_ratio['Year_Quarter'] == stockout_yr_q[-2]]['stockout_ratio'].values[0]

    # Create the scorecard
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode='number+delta',
        value=latest_stockout_ratio,
        number={
            'suffix': '%',
            'font': {'color': 'whitesmoke'}            
            },
        delta={
            'position': 'bottom', 
            'reference': latestmin1_stockout_ratio,
            'relative': True,
            'valueformat':'.1%',
            'decreasing': {'color': '#34ad82'},
            'increasing': {'color': 'rgba(255, 80, 80, 0.9)'},
        },
        domain={'x': [0, 1], 'y': [0, 1]}
    ))

    fig.update_layout(
        height=50,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'     
    )

    return fig

def create_stockout_sparkline(stockout_ratio):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=stockout_ratio['Year_Quarter'],
        y=stockout_ratio['stockout_ratio'],
        mode='lines',
        line=dict(color='rgba(119, 205, 255, 1)', width=2),
        fill='tozeroy',
        hoverinfo='skip'
    ))

    fig.update_layout(
        margin=dict(t=10, b=10, l=0, r=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=50,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        dragmode=False
    )

    return fig

def create_stockout_linechart(stockout_ratio):
    # Create the area chart figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=stockout_ratio['Year_Quarter'],
        y=stockout_ratio['stockout_ratio'],
        mode='lines+markers+text',
        text=stockout_ratio['stockout_ratio'].apply(lambda x: f'{x:.1f}%'),
        textposition='bottom center',
        textfont=dict(
            color='whitesmoke',
            size=10
        ),
        cliponaxis=False,
        name='Stockout Ratio',
        line=dict(color='royalblue'),
        fill='tozeroy'
    ))

    fig.update_layout(
        xaxis={
            'tickfont':{'size':10, 'color': 'whitesmoke'},
            'automargin':True,
            'gridcolor': 'rgba(255, 255, 255, 0.2)',
            'gridwidth': 0.5
        },
        yaxis = {
            'visible':False,
        },
        height=220,
        width=400,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'   
    )

    return fig