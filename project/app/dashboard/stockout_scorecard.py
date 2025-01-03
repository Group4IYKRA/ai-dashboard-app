import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from project import download_from_gcs

def create_stockout_scorecard(metrics_raw_data=None):
    # Define the project root and load the data
    if metrics_raw_data is None:
        blob_name = 'query_result/metrics_raw_data.csv'
        metrics_raw_data_file = download_from_gcs(blob_name)
        metrics_raw_data = pd.read_csv(metrics_raw_data_file)

    # Calculate Stockout Ratio per Year-Quarter
    stockout_ratio = metrics_raw_data.groupby('Year_Quarter', as_index=False).agg({'Daily_Sales':'sum', 'Lost_Sales':'sum'})
    stockout_ratio['stockout_ratio'] = (stockout_ratio['Lost_Sales'] / (stockout_ratio['Lost_Sales'] + stockout_ratio['Daily_Sales'])) * 100
    stockout_ratio.drop(columns=['Daily_Sales', 'Lost_Sales'], inplace=True)

    # Calculate Current
    current_quarter = stockout_ratio['Year_Quarter'].max()
    cq_stockout_ratio = stockout_ratio[stockout_ratio['Year_Quarter'] == current_quarter]
    stockout_ratio_val = cq_stockout_ratio['stockout_ratio'].values[0]

    # Create the scorecard
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=stockout_ratio_val,
        number={"suffix": "%"},
        title={"text": "Stockout Ratio (Current Quarter)"},
        domain={'x': [0, 1], 'y': [0, 1]}
    ))

    fig.update_layout(
        template="plotly_white",
        height=300
    )

    return fig