# Import libraries
import plotly.graph_objects as go

def create_barpolar_top_10(df, sort_by='Overstock Cost'):
    marker_color_map = {
        'ITR_norm': 'rgba(2, 76, 170, 0.8)',
        'stockout_ratio_norm': 'rgba(13, 146, 244, 0.8)',
        'overstock_cost_norm': 'rgba(119, 205, 255, 0.8)'
    }
    if sort_by!='ITR':
        df = df.nlargest(10, sort_by)
    else:
        df = df.nsmallest(10, sort_by)

    base_col = 'Product_ID'
    fig = go.Figure()

    # Evenly spaced angles within 0 to 90 degrees
    theta = [i * (90 / len(df)) for i in range(len(df))]

    for col, mc in marker_color_map.items():
        annotation_col = {'ITR_norm': 'ITR', 'stockout_ratio_norm': 'Stockout Ratio', 'overstock_cost_norm': 'Overstock Cost'}[col]
        fig.add_barpolar(
            r=df[col],
            theta=theta,
            customdata=list(zip(df[[annotation_col, base_col]].values, [annotation_col] * len(df))),
            hovertemplate='<b>%{customdata[0][1]}</b><br>%{customdata[1]}: %{customdata[0][0]}<br><extra></extra>',
            name=annotation_col, 
            opacity=0.8, 
            marker_color=mc,
        )

    # Update layout
    fig.update_layout(
        height=400, 
        margin=dict(l=10, r=0, t=15, b=0),
        template=None, font_size=12,
        paper_bgcolor='#585454',
        plot_bgcolor='#585454',
        font_color='whitesmoke',
    legend=dict(
        orientation='v',     
        x=1.02,              
        y=1,                 
        xanchor='left',      
        yanchor='top',
        title='Metrics', 
        font_color='whitesmoke'
    ),
    polar=dict(
            sector=[0, 90],
            bgcolor='#585454',
            domain=dict(x=[0,0.8]),
            radialaxis=dict(
                showticklabels=False, 
                ticks='', 
                color='whitesmoke', 
                gridcolor='rgba(255,255,255,0.1)'),
            angularaxis=dict(
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