import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from project import download_from_gcs

def create_stockout_linechart(metrics_raw_data=None):
    # Define the project root and load the data
    if metrics_raw_data is None:
        blob_name = 'query_result/metrics_raw_data.csv'
        metrics_raw_data_file = download_from_gcs(blob_name)
        metrics_raw_data = pd.read_csv(metrics_raw_data_file)

    # Calculate Stockout Ratio per Year-Quarter
    stockout_ratio = metrics_raw_data.groupby('Year_Quarter', as_index=False).agg({'Daily_Sales':'sum', 'Lost_Sales':'sum'})
    stockout_ratio['stockout_ratio'] = (stockout_ratio['Lost_Sales'] / (stockout_ratio['Lost_Sales'] + stockout_ratio['Daily_Sales'])) * 100
    stockout_ratio.drop(columns=['Daily_Sales', 'Lost_Sales'], inplace=True)

    # Create the area chart figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=stockout_ratio['Year_Quarter'],
        y=stockout_ratio['stockout_ratio'],
        mode='lines+markers+text',
        text=stockout_ratio['stockout_ratio'].apply(lambda x: f"{x:.2f}%"),
        textposition='top center',
        name='Stockout Ratio',
        line=dict(color='royalblue'),
        fill='tozeroy'
    ))

    fig.update_layout(
        title='Stockout Ratio by Year-Quarter',
        xaxis_title='Year-Quarter',
        yaxis_title='Stockout Ratio (%)',
        template='plotly_white'
    )

    return fig