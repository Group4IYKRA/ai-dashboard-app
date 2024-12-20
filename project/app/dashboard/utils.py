# Utility functions for the dashboard
from dash import dcc
import os
import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

stock_pivot_file = os.path.join(project_root, "data/query_result/stock_pivot_data.pkl")
stock_pivot = pd.read_pickle(stock_pivot_file)

pulp_result_file = os.path.join(project_root, "models/models_result/pulp_result_data.pkl")
optim_df = pd.read_pickle(pulp_result_file)

def product_filter():
    return \
        dcc.Dropdown(
        id='filter_dropdown',
        options=[
            {'label': val, 'value': val} for val in stock_pivot['Product_ID'].unique()],
        multi=False,
        placeholder="Select Product_ID to filter",
        style={
            'width': '35%', 
            'margin': '10px 0',
            'textAlign':'left',
            'padding':'0',
            'fontSize':'12px',
            'fontFamily':'Helvetica'
            }
    )

def update_tables(selected_value):
    if selected_value:
        # Filter both datasets based on the selected value
        filtered_pivot = stock_pivot[stock_pivot['Product_ID'] == selected_value]
        filtered_optim = optim_df[optim_df['Product_ID'] == selected_value]
    else:
        # If no filter is selected, show all data
        filtered_pivot = stock_pivot
        filtered_optim = optim_df
    
    return filtered_pivot.to_dict('records'), filtered_optim.to_dict('records')