import pandas as pd
import plotly.graph_objects as go
from .helper import format_number, format_number_v2

def create_overstock_cost_scorecard(overstock_cost):  
    # Output latest overstock_cost data
    overstock_cost_yr_q = sorted(overstock_cost['Year_Quarter'].unique())
    latest_overstock_cost = overstock_cost[overstock_cost['Year_Quarter'] == overstock_cost['Year_Quarter'].max()]['Overstock_Cost'].values[0]
    latestmin1_overstock_cost = overstock_cost[overstock_cost['Year_Quarter'] == overstock_cost_yr_q[-2]]['Overstock_Cost'].values[0]

    formatted_value, suffix = format_number(latest_overstock_cost)

    # Create the scorecard figure
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode='number+delta',
        value=formatted_value,
        number={
            'valueformat': ',.0f',
            'prefix': 'Rp', 
            'suffix': suffix, 
            'font': {'size':22,'color': 'whitesmoke'}
        },
        delta={
            'position': 'bottom', 
            'reference': latestmin1_overstock_cost,
            'relative': True,
            'valueformat': '.1%',
            'decreasing': {'color': '#b62a4e'},
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

def create_overstock_cost_sparkline(overstock_cost):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=overstock_cost['Year_Quarter'],
        y=overstock_cost['Overstock_Cost'],
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

def create_overstock_cost_linechart(overstock_cost):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=overstock_cost['Year_Quarter'],
        y=overstock_cost['Overstock_Cost'],
        mode='lines+markers+text',
        text=overstock_cost['Overstock_Cost'].apply(format_number_v2),
        textposition='bottom center',
        textfont=dict(
            color='whitesmoke',
            size=10
        ),
        cliponaxis=False,
        name='Overstock Cost',
        line=dict(color='skyblue'),
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