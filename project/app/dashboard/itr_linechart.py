import os
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from project import download_from_gcs

def create_itr_linechart(metrics_raw_data=None):
    # Define the project root and load the data
    if metrics_raw_data is None:
        blob_name = 'query_result/metrics_raw_data.csv'
        metrics_raw_data_file = download_from_gcs(blob_name)
        metrics_raw_data = pd.read_csv(metrics_raw_data_file)

    metrics_raw_data['Date'] = pd.to_datetime(metrics_raw_data['Date'])
    itr = metrics_raw_data.groupby('Year_Quarter', as_index=False).agg({'Date':['min','max'], 'Daily_Sales':'sum'})
    itr.columns = ['_'.join(col).strip() if col[1] else col[0] for col in itr.columns.values]

    earliest_stock_sum = [(metrics_raw_data[metrics_raw_data['Date']==i]['Stock_Level'].sum()) for i in itr['Date_min']]
    latest_stock_sum = [(metrics_raw_data[metrics_raw_data['Date']==i]['Stock_Level'].sum()) for i in itr['Date_max']]

    itr['Earliest_Stock_Sum'] = earliest_stock_sum
    itr['Latest_Stock_Sum'] = latest_stock_sum

    itr['ITR'] = (itr['Daily_Sales_sum']/((itr['Latest_Stock_Sum']+itr['Earliest_Stock_Sum'])/2)).round(2)
    itr.drop(columns=['Date_min','Date_max', 'Daily_Sales_sum', 'Earliest_Stock_Sum', 'Latest_Stock_Sum'], inplace=True)

    # Create the line chart figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=itr['Year_Quarter'],
        y=itr['ITR'],
        mode='lines+markers+text',
        text=itr['ITR'],
        textposition='top center',
        name='ITR',
        line=dict(color='royalblue'),
        fill='tozeroy'
    ))

    fig.update_layout(
        title='ITR by Year-Quarter',
        xaxis_title='Year-Quarter',
        yaxis_title='ITR',
        template='plotly_white'
    )

    return fig