# Entry point for the application
from dash import Dash, html, Input, Output
import os

# Import your data
from dashboard import *

app = Dash()

app.layout = html.Div([
    html.Div([
            html.H1(
                "STOCK OPTIMIZATION HUB DASHBOARD", 
                style={
                    'textAlign': 'left',
                    'fontFamily': 'Helvetica',
                    'marginBottom': '20px',
                }
            ),
    product_filter(),
    ],style={
        'display': 'flex',          
        'alignItems': 'center',     
        'justifyContent': 'space-between',  
        'marginBottom': '10px',     
    }),
    html.Div([
        create_stock_optim(),
        create_table(),
    ])

])

@app.callback(
    [Output('stock_pivot', 'data'),
     Output('stock_optimization', 'data')],
    Input('filter_dropdown', 'value')
)
def callback_update_tables(selected_value):
    return update_tables(selected_value) 

if __name__ == "__main__":
    app.run_server(debug=True)
