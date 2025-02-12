import pandas as pd
import plotly.graph_objects as go

def create_itr_scorecard(itr):
    # Output latest ITR data
    itr_yr_q = sorted(itr['Year_Quarter'].unique())
    latest_itr = itr[itr['Year_Quarter'] == itr['Year_Quarter'].max()]['ITR'].values[0]
    latestmin1_itr = itr[itr['Year_Quarter'] == itr_yr_q[-2]]['ITR'].values[0]
    
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=latest_itr,
        number={
            'font': {'color': 'whitesmoke'}
        },
        delta={
            'position': "bottom", 
            'reference': latestmin1_itr,
            'relative': True,
            'valueformat': '.1%',
            'decreasing': {'color': 'whitesmoke'},
            'increasing': {'color': 'whitesmoke'},
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

def create_itr_sparkline(itr):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=itr['Year_Quarter'],
        y=itr['ITR'],
        mode='lines',
        text=itr['ITR'],
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

def create_itr_linechart(itr):
    quarter_mapping = {
        '2023-Q1': 'Q1-23',
        '2023-Q2': 'Q2-23',
        '2023-Q3': 'Q3-23',
        '2023-Q4': 'Q4-23',
        '2024-Q1': 'Q1-24',
        '2024-Q2': 'Q2-24',
        '2024-Q3': 'Q3-24',
        '2024-Q4': 'Q4-24'
    }

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=itr['Year_Quarter'],
        y=itr['ITR'],
        mode='lines+markers+text',
        text=itr['ITR'],
        textposition='bottom center',
        textfont=dict(
            color='whitesmoke',
            size=10
        ),
        cliponaxis=False,
        name='ITR',
        line=dict(color='#77CDFF'),
        fill='tozeroy'
    ))

    fig.update_layout(
        xaxis={
            'tickvals': itr['Year_Quarter'],
            'ticktext': itr['Year_Quarter'].map(quarter_mapping),
            'tickfont':{'size':10, 'color': 'whitesmoke'},
            'automargin':True,
            'gridcolor': 'rgba(255, 255, 255, 0)',
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