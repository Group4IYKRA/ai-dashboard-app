import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from project import download_from_gcs

def create_overstock_cost_scorecard(metrics_raw_data=None):
    # Load the data if no external df is provided
    if metrics_raw_data is None:
        blob_name = 'query_result/metrics_raw_data.csv'
        metrics_raw_data_file = download_from_gcs(blob_name)
        metrics_raw_data = pd.read_csv(metrics_raw_data_file)
    
    metrics_raw_data['Overstock_Cost'] = (metrics_raw_data['Stock_Level'] - metrics_raw_data['Daily_Sales']) * metrics_raw_data['Inventory_Holding_Cost']
    overstock_cost = metrics_raw_data.groupby('Year_Quarter', as_index=False).agg({'Overstock_Cost':'sum'})
    overstock_cost['Overstock_Cost'] = overstock_cost['Overstock_Cost'] / 1000000000

    # Output latest overstock_cost data
    latest_overstock_cost = overstock_cost[overstock_cost['Year_Quarter'] == overstock_cost['Year_Quarter'].max()]['Overstock_Cost'].values[0]

    # Create the scorecard figure
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=latest_overstock_cost,
        number={"valueformat": ",.0f", "prefix": "Rp", "suffix": "M"},
        title={"text": "Overstock Cost (Current Quarter)"},
        domain={'x': [0, 1], 'y': [0, 1]}
    ))

    fig.update_layout(
        template="plotly_white",
        height=300
    )

    return fig