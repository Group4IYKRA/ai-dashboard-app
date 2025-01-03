import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from project import download_from_gcs

def create_overstock_cost_linechart(metrics_raw_data=None):
    # Load the data if no external df is provided
    if metrics_raw_data is None:
        blob_name = 'query_result/metrics_raw_data.csv'
        metrics_raw_data_file = download_from_gcs(blob_name)
        metrics_raw_data = pd.read_csv(metrics_raw_data_file)
    
    metrics_raw_data['Overstock_Cost'] = (metrics_raw_data['Stock_Level'] - metrics_raw_data['Daily_Sales']) * metrics_raw_data['Inventory_Holding_Cost']
    overstock_cost = metrics_raw_data.groupby('Year_Quarter', as_index=False).agg({'Overstock_Cost':'sum'})
    overstock_cost['Overstock_Cost'] = overstock_cost['Overstock_Cost'] / 1000000000

    # Create the line chart figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=overstock_cost['Year_Quarter'],
        y=overstock_cost['Overstock_Cost'],
        mode='lines+markers+text',
        text=overstock_cost['Overstock_Cost'].apply(lambda x: f"{x:,.0f} M"),
        textposition='top center',
        name='Overstock Cost',
        line=dict(color='royalblue'),
        fill='tozeroy'
    ))

    fig.update_layout(
        title='Overstock Cost by Year-Quarter',
        xaxis_title='Year-Quarter',
        yaxis_title='Overstock Cost (in Millions)',
        template='plotly_white'
    )

    return fig