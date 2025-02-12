# Import libraries
import plotly.graph_objects as go
import numpy as np

def create_barpolar_top_10(df, sort_by='Overstock Cost'):
    marker_color_map = {
        'ITR_norm': 'rgba(119, 205, 255, 0.8)',
        'stockout_ratio_norm': 'rgba(135, 162, 255, 0.8)',
        'overstock_cost_norm': 'rgba(13, 146, 244, 0.8)'
    }
    if sort_by=='ITR':
        df = df.nsmallest(10, sort_by)
    elif sort_by=='Overstock Cost' or sort_by=='Stockout Ratio':
        df = df.nlargest(10, sort_by)
    else:
        df = df.nlargest(10, 'Overstock Cost')

    base_col = 'Product_ID'
    fig = go.Figure()

    # Evenly spaced angles within 0 to 90 degrees
    theta = np.arange(len(df)) * (360 / len(df))
    n = -12

    for col, mc in marker_color_map.items():
        annotation_col = {'ITR_norm': 'ITR', 'stockout_ratio_norm': 'Stockout Ratio', 'overstock_cost_norm': 'Overstock Cost'}[col]
        fig.add_barpolar(
            r=df[col],
            theta=theta + n,
            width=12,
            customdata=list(zip(df[[annotation_col, base_col]].values, [annotation_col] * len(df))),
            hovertemplate='<b>%{customdata[0][1]}</b><br>%{customdata[1]}: %{customdata[0][0]}<br><extra></extra>',
            name=annotation_col, 
            opacity=1, 
            marker=dict(
                color=mc,
                line=dict(
                    color='#3A3D43',
                    width=0.1,
                ),
            ),
            marker_color=mc,
        )
        n+=12

    # Update layout
    fig.update_layout(
        height=400, 
        margin=dict(l=0, r=0, t=0, b=0),
        template=None, font_size=12,
        paper_bgcolor='#585454',
        plot_bgcolor='#585454',
        font_color='whitesmoke',
    legend=dict(
        orientation='h',     
        x=0.5,              
        y=1.1,                 
        xanchor='center',      
        yanchor='bottom',
        title=dict(
            text='Double click to highlight:',
            side='left',
            font=dict(size=12),
        ),
        font_color='whitesmoke',
        itemclick='toggleothers',
        itemdoubleclick='toggle',
        valign='middle'
    ),
    polar=dict(
            sector=[0, 360],
            bgcolor='#585454',
            domain=dict(x=[0,1], y=[0, 1]),
            radialaxis=dict(
                showline=False,
                showticklabels=False, 
                ticks='', 
                color='whitesmoke', 
                gridcolor='rgba(255,255,255,0.1)'),
            angularaxis=dict(
                showline=False,
                showticklabels=True,
                ticks='',
                rotation=86.5,
                direction="clockwise",
                tickvals=theta,
                ticktext=df['Product_ID'],
                color='whitesmoke',
                gridcolor='rgba(255,255,255,0.1)'
            )
        )
    )

    return fig