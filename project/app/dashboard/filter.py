# Utility functions for the dashboard
from dash import dcc
import pandas as pd

def product_filter(stock_pivot):
    return dcc.Dropdown(
        id='product_filter_dropdown',
        options=[
            {'label': val, 'value': val} for val in sorted(stock_pivot['Product_ID'].unique())
        ],
        multi=True,
        placeholder="Product_ID",
    )

def from_filter(optim_df):
    return dcc.Dropdown(
        id='from_filter_dropdown',
        options=[
            {'label': val, 'value': val} for val in sorted(optim_df['From'].unique())
        ],
        multi=True,
        placeholder="From Warehouse",
    )

def to_filter(optim_df):
    return dcc.Dropdown(
        id='to_filter_dropdown',
        options=[
            {'label': val, 'value': val} for val in sorted(optim_df['To'].unique())
        ],
        multi=True,
        placeholder="To Warehouse",
    )