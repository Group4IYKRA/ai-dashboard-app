import pandas as pd
import plotly.graph_objects as go

def create_fct_vs_act_linechart(fct_vs_act):
    fct = fct_vs_act['Forecasted_Demand']
    act = fct_vs_act['Daily_Sales']
    fct_text = [None] * (len(fct) - 1) + [fct.iloc[-1]]
    fct_text = [f'{x:,.0f}' if x is not None else None for x in fct_text]
    act_text = [None] * (len(act) - 1) + [act.iloc[-1]]
    act_text = [f'{x:,.0f}' if x is not None else None for x in act_text]

    # Create the area chart figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=fct_vs_act['Date'],
        y=fct_vs_act['Daily_Sales'],
        mode='lines+markers+text',
        text=act_text,
        textposition='bottom center',
        textfont=dict(size=9.5, color='whitesmoke'),
        cliponaxis=False,
        name='Actual',
        line=dict(color='#0D92F4'),
    ))

    fig.add_trace(go.Scatter(
        x=fct_vs_act['Date'],
        y=fct_vs_act['Forecasted_Demand'],
        mode='lines+markers+text',
        text=fct_text,
        textposition='bottom center',
        textfont=dict(size=9.5, color='whitesmoke'),
        cliponaxis=False,
        name='Forecast',
        line=dict(color='#f2b344'),
    ))

    fig.update_layout(
        xaxis={
            'tickfont':{'size':10, 'color': 'whitesmoke'},
            'automargin':True,
            'gridcolor': 'rgba(255, 255, 255, 0)',
            'gridwidth': 0.5
        },
        yaxis = {
            'visible':False,
        },
        showlegend=True,
        legend={
            'x':0,
            'y':1.1,
            'xanchor':'left',
            'yanchor':'top',
            'orientation':'h',
            'font':{'size':9, 'color':'whitesmoke'},
        },
        height=220,
        width=400,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig


