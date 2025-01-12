# Entry point for the application
from dash import Dash, html, Input, Output
from .dashboard import *
from .chatbot import *
from project.data.weekly_pipeline import run_weekly_pipeline
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Get all necessary dfs
current_dir = os.getcwd()
processed_dir = 'project/data/processed/'
file_path1 = os.path.join(processed_dir, 'pulp_result_data.csv')
file_path2 = os.path.join(processed_dir, 'stock_pivot_data.csv')
file_path3 = os.path.join(processed_dir, 'metrics_raw_data.csv')

# Store the original data globally
if all(os.path.exists(file) for file in [file_path1, file_path2, file_path3]):
    optim_df = pd.read_csv(os.path.join(processed_dir, 'pulp_result_data.csv'))
    optim_df = optim_df.drop(columns=['Unnamed: 0'])
    stock_pivot = pd.read_csv(os.path.join(processed_dir, 'stock_pivot_data.csv'))
    stock_pivot = stock_pivot.drop(columns=['Unnamed: 0'])
    metrics_raw_data = pd.read_csv(os.path.join(processed_dir, 'metrics_raw_data.csv'))
    logging.info(f'File Ready! in {file_path1}, current working directory: {current_dir}')
else:
    logging.info(f'File not ready in {file_path1}. Please wait while we get the data.')
    run_weekly_pipeline()
    logging.info('Successfully running pipeline!')
    stock_pivot = pd.read_csv(os.path.join(processed_dir, 'stock_pivot_data.csv'))
    stock_pivot = stock_pivot.drop(columns=['Unnamed: 0'])
    optim_df = pd.read_csv(os.path.join(processed_dir, 'pulp_result_data.csv'))
    optim_df = optim_df.drop(columns=['Unnamed: 0'])
    metrics_raw_data = pd.read_csv(os.path.join(processed_dir, 'metrics_raw_data.csv'))

app = Dash(__name__)
server = app.server

dashboard_layout = html.Div([
    html.Div([
        html.Div([
            html.H1(
                "STOCK OPTIMIZATION HUB DASHBOARD", 
                style={
                    'position': 'sticky',
                    'top':'0',
                    'textAlign': 'left',
                    'fontFamily': 'Helvetica',
                    'marginBottom': '20px',
                    'marginLeft': '20px',
                    'color': 'white',
                    'padding-left': '25px',
                    'zIndex':'1000',
                }
            ),
        ], style={
            'flex': '1',
            'width': '39%',
            'position': 'sticky',
            'zIndex':'1000',
        }),
        html.Div([
            product_filter(stock_pivot),
            from_filter(optim_df),
            to_filter(optim_df),
            html.Div([
                html.Button('Get new data', id='refresh-button', n_clicks=0),
                html.Div(id='status-message'),
            ]),
        ], style={
            'position': 'sticky',
            'top': '0',
            'display': 'flex',          
            'alignItems': 'center',     
            'justifyContent': 'space-between',  
            'marginBottom': '2px',
            'width': '59%',
            'flex': '1',
            'zIndex':'1000',
        }),
    ], style={
        'position':'sticky',
        'top': '0',
        'display': 'flex',          
        'alignItems': 'center',  
        'marginBottom': '2px',
        'width': '100%',
        'backgroundColor': '#007BFF',
        'border': '1px solid #ddd', 
        'borderRadius': '10px',
        'zIndex': '1000',
    }),
    html.Div([
        dcc.Graph(id="stockout-ratio-scorecard", 
                figure=create_stockout_scorecard(metrics_raw_data), style={'width': '50%'}),
        dcc.Graph(id="stockout-ratio-linechart", 
                figure=create_stockout_linechart(metrics_raw_data), style={'width': '50%'}),
        dcc.Graph(id="stockout-ratio-barchart", 
                figure=create_stockout_barchart(metrics_raw_data), style={'width': '50%'}),
    ], style={
        'display': 'flex',          
        'alignItems': 'flex-start',  
        'marginBottom': '2px',
        'width': '100%',
        'justifyContent': 'center',
    }),
    html.Div([
        dcc.Graph(id="itr-scorecard", 
                figure=create_itr_scorecard(metrics_raw_data), style={'width': '50%'}),
        dcc.Graph(id="itr-linechart", 
                figure=create_itr_linechart(metrics_raw_data), style={'width': '50%'}),
        dcc.Graph(id="itr-barchart", 
                figure=create_itr_barchart(metrics_raw_data), style={'width': '50%'}),
    ], style={
        'display': 'flex',          
        'alignItems': 'flex-start',  
        'marginBottom': '2px',
        'width': '100%',
        'justifyContent': 'center',      
    }),
    html.Div([
        dcc.Graph(id="overstock-cost-scorecard", 
                figure=create_overstock_cost_scorecard(metrics_raw_data), style={'width': '50%'}),
        dcc.Graph(id="overstock-cost-linechart", 
                figure=create_overstock_cost_linechart(metrics_raw_data), style={'width': '50%'}),
        dcc.Graph(id="overstock-cost-barchart", 
                figure=create_overstock_cost_barchart(metrics_raw_data), style={'width': '50%'}),
    ], style={
        'display': 'flex',          
        'alignItems': 'flex-start',  
        'marginBottom': '2px',
        'width': '100%',
        'justifyContent': 'center',      
    }),
    html.Div([
        dcc.Graph(id='forecast-vs-actual-linechart',
                  figure=create_fct_vs_act_linechart(metrics_raw_data), style={'width':'50%'}),
        create_stock_optim(optim_df),
        ], style={
        'display': 'flex',          
        'alignItems': 'center',  
        'marginBottom': '2px',
        'width': '100%',
        'justifyContent': 'center',
        }),
    create_table(stock_pivot),
    html.Div(chatbox(),style={'display': 'none'}),
])

# Main app layout
app.layout = html.Div([
    html.Div([
        html.Button("Dashboard", id="dashboard-button", n_clicks=0, 
                    style={"position": "sticky", "display": "block", "marginBottom": "10px", "marginLeft": "10px", "width": "100px", "align": "center"}),
        html.Button("Chatbot", id="chatbot-button", n_clicks=0, 
                    style={"position": "sticky", "display": "block", "marginBottom": "10px", "marginLeft": "10px", "width": "100px", "align": "center"}),
    ], style={"float": "left", "marginRight": "20px", 'border': '1px solid #ddd', 'height': '900px', 'width': '120px', 'backgroundColor': '#f9f9f9',  "position": "fixed"}),
    html.Div(id="page-content", children = dashboard_layout, style={"marginLeft": "150px"}),
])

@app.callback(
    Output('stock_pivot','data'),
    Output('stock_optimization', 'data'),
    Input('product_filter_dropdown', 'value'),
    Input('from_filter_dropdown', 'value'),
    Input('to_filter_dropdown', 'value'),
)
def update_tables(selected_product_ids, 
                  selected_from_warehouse, 
                  selected_to_warehouse):
    
    global stock_pivot, optim_df
    filtered_pivot = stock_pivot.copy()
    filtered_optim = optim_df.copy()

    selected_products = selected_product_ids or filtered_pivot['Product_ID'].unique()
    selected_from = selected_from_warehouse or filtered_optim['From'].unique()
    selected_to = selected_to_warehouse or filtered_optim['To'].unique()
    selected_warehouse = list(set(selected_from).union(set(selected_to))) \
                            if selected_from_warehouse and selected_to_warehouse \
                            else selected_from_warehouse or selected_to_warehouse or filtered_optim['From'].unique()

    # Filter pivot table
    pivot_filter = filtered_pivot['Product_ID'].isin(selected_products)
    filtered_pivot = filtered_pivot[pivot_filter]

    selected_warehouse = [item for item in selected_warehouse if item != 'Supplier']
    columns = ['Product_ID', 'Category', 'Brand', 'Color']
    columns.extend(selected_warehouse or [])
    filtered_pivot = filtered_pivot[columns]
    
    # Filter filtered_optim 
    optim_filter = (filtered_optim['Product_ID'].isin(selected_products)) & \
                    (filtered_optim['From'].isin(selected_from)) & \
                    (filtered_optim['To'].isin(selected_to))
    filtered_optim = filtered_optim[optim_filter]

    return filtered_pivot.to_dict('records'), filtered_optim.to_dict('records')

@app.callback(
    Output('stockout-ratio-scorecard', 'figure'), 
    Output('itr-scorecard', 'figure'), 
    Output('overstock-cost-scorecard', 'figure'), 
    Output('stockout-ratio-linechart', 'figure'), 
    Output('itr-linechart', 'figure'), 
    Output('overstock-cost-linechart', 'figure'), 
    Output('stockout-ratio-barchart', 'figure'), 
    Output('itr-barchart', 'figure'), 
    Output('overstock-cost-barchart', 'figure'), 
    Output('forecast-vs-actual-linechart', 'figure'),
    Input('product_filter_dropdown', 'value'),
    Input('from_filter_dropdown', 'value'),
    Input('to_filter_dropdown', 'value')
)
def update_charts(selected_product_ids, 
                  selected_from_warehouse, 
                  selected_to_warehouse):
    
    global metrics_raw_data
    filtered_metrics = metrics_raw_data.copy()
    if selected_product_ids or selected_from_warehouse or selected_to_warehouse:
        selected_products = selected_product_ids or filtered_metrics['Product_ID'].unique()
        filtered_metrics = filtered_metrics[filtered_metrics['Product_ID'].isin(selected_products)]

        selected_from = selected_from_warehouse or filtered_metrics['Warehouse_Loc_ID'].unique()
        selected_to = selected_to_warehouse or filtered_metrics['Warehouse_Loc_ID'].unique()
        selected_warehouse = list(set(selected_from).union(set(selected_to))) \
                                if selected_from_warehouse and selected_to_warehouse \
                                else selected_from_warehouse or selected_to_warehouse or filtered_metrics['Warehouse_Loc_ID'].unique()
        filtered_metrics = filtered_metrics[filtered_metrics['Warehouse_Loc_ID'].isin(selected_warehouse)]
        
    return [
        create_stockout_scorecard(filtered_metrics),
        create_itr_scorecard(filtered_metrics),
        create_overstock_cost_scorecard(filtered_metrics),
        create_stockout_linechart(filtered_metrics),
        create_itr_linechart(filtered_metrics),
        create_overstock_cost_linechart(filtered_metrics),
        create_stockout_barchart(filtered_metrics),
        create_itr_barchart(filtered_metrics),
        create_overstock_cost_barchart(filtered_metrics),
        create_fct_vs_act_linechart(filtered_metrics)       
    ]

# Callback to switch between pages
@app.callback(
    [Output("page-content", "children"),
     Output("dashboard-button", "style"),
     Output("chatbot-button", "style")],
    [Input("dashboard-button", "n_clicks"), Input("chatbot-button", "n_clicks")]
)
def render_page_content(dashboard_clicks, chatbot_clicks):
    default_style = {"display": "block", "marginBottom": "10px", "marginLeft": "10px", "width": "100px"}
    active_style = {"display": "block", "marginBottom": "10px", "marginLeft": "10px", "width": "100px", "backgroundColor": "#007BFF", "color": "white"}
    if chatbot_clicks > dashboard_clicks:
        return chatbox(), default_style, active_style
    else:
        return dashboard_layout, active_style, default_style 

# Callback to refresh the pages
@app.callback(
    Output('status-message', 'children'),
    Input('refresh-button', 'n_clicks'),
    prevent_initial_call=True
)
def run_script_and_refresh(n_clicks):
    if n_clicks is None:
        return ""

    try:
        # Run the Python script
        subprocess.run(
            ["python", "-m", "project.data.hourly_pipeline"], 
            capture_output=True, text=True, check=True
        )
        # Return success message
        return "Complete! Please refresh page"
    
    except subprocess.CalledProcessError as e:
        # Return error message and trigger refresh
        return f"Error executing script:\n{e.stderr}"
    except Exception as ex:
        # Return unexpected error message and trigger refresh
        return f"Unexpected error: {ex}", 0

if __name__ == "__main__":
    app.run_server(debug=False)