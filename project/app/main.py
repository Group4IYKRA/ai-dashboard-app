# Entry point for the application
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from .dashboard import *
import os
from flask_caching import Cache
from .chatbot import *
from project.data.query import *
from project.models.pulp_solver import pulp_solver
import os
from flask_socketio import SocketIO
from sklearn.preprocessing import MinMaxScaler
import threading

# Get all necessary dfs
current_dir = os.getcwd()
processed_dir = 'project/data/processed/'
file_path1 = os.path.join(current_dir, processed_dir, 'stock_pivot_data.csv')
file_path2 = os.path.join(current_dir, processed_dir, 'pulp_result_data.csv')
file_path3 = os.path.join(current_dir, processed_dir, 'metrics_raw_data.csv')

# Store the original data globally
if not os.path.exists(file_path1):
    get_stock_pivot_table()

if not os.path.exists(file_path2):
    get_pulp_raw()
    get_cost_table()  
    pulp_solver()

if not os.path.exists(file_path3):
    get_metrics_raw()

optim_df = pd.read_csv(os.path.join(processed_dir, 'pulp_result_data.csv'))
optim_df = optim_df.drop(columns=['Unnamed: 0'])
stock_pivot = pd.read_csv(os.path.join(processed_dir, 'stock_pivot_data.csv'))
stock_pivot = stock_pivot.drop(columns=['Unnamed: 0', 'Category', 'Brand', 'Color'])
metrics_raw_data = pd.read_csv(os.path.join(processed_dir, 'metrics_raw_data.csv'))

# ----------------------Cache intermediate dataframe----------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.LUMEN, "/assets/styles2.css"])
server = app.server
cache = Cache(app.server, config={'CACHE_TYPE': 'simple'})
socketio = SocketIO(app.server)

# Preprocessing for Overstock Cost
@cache.memoize(timeout=600)
def preprocess_overstock(metrics_raw_data):
    overstock_cost = (
        metrics_raw_data.groupby(['Year_Quarter', 'Product_ID', 'Date'], as_index=False)
        .agg({
            'Daily_Sales': 'sum',
            'Stock_Level': 'sum',
            'Inventory_Holding_Cost': 'mean'
        })
    )
    overstock_cost = (
        overstock_cost.sort_values('Date')
        .groupby(['Year_Quarter'], as_index=False)
        .agg({
            'Date': 'max',
            'Daily_Sales': 'mean',
            'Stock_Level': 'last',
            'Inventory_Holding_Cost': 'last'
        })
    )
    overstock_cost['Inventory_Holding_Cost'] = overstock_cost['Inventory_Holding_Cost'].round(2)
    overstock_cost['Daily_Sales'] = overstock_cost['Daily_Sales'].round(2)
    overstock_cost['Overstock_Cost'] = (overstock_cost['Stock_Level'] - overstock_cost['Daily_Sales']) * overstock_cost['Inventory_Holding_Cost']
    overstock_cost['Overstock_Cost'] = overstock_cost['Overstock_Cost'].round(2)
    overstock_cost.drop(columns=['Daily_Sales', 'Stock_Level', 'Date', 'Inventory_Holding_Cost'], inplace=True)

    return overstock_cost

# Preprocessing for Stockout Ratio
@cache.memoize(timeout=600)
def preprocess_stockout(metrics_raw_data):
    stockout_ratio = metrics_raw_data.groupby('Year_Quarter', as_index=False).agg({'Daily_Sales':'sum', 'Lost_Sales':'sum'})
    stockout_ratio['stockout_ratio'] = (stockout_ratio['Lost_Sales'] / (stockout_ratio['Lost_Sales'] + stockout_ratio['Daily_Sales'])) * 100
    stockout_ratio.drop(columns=['Daily_Sales', 'Lost_Sales'], inplace=True)

    return stockout_ratio
    
# Preprocessing for ITR
@cache.memoize(timeout=600)
def preprocess_itr(metrics_raw_data):
    metrics_raw_data['Date'] = pd.to_datetime(metrics_raw_data['Date'])
    itr = metrics_raw_data.groupby('Year_Quarter', as_index=False).agg({'Date':['min','max'], 'Daily_Sales':'sum'})
    itr.columns = ['_'.join(col).strip() if col[1] else col[0] for col in itr.columns.values]

    earliest_stock_sum = [(metrics_raw_data[metrics_raw_data['Date']==i]['Stock_Level'].sum()) for i in itr['Date_min']]
    latest_stock_sum = [(metrics_raw_data[metrics_raw_data['Date']==i]['Stock_Level'].sum()) for i in itr['Date_max']]

    itr['Earliest_Stock_Sum'] = earliest_stock_sum
    itr['Latest_Stock_Sum'] = latest_stock_sum

    itr['ITR'] = (itr['Daily_Sales_sum']/((itr['Latest_Stock_Sum']+itr['Earliest_Stock_Sum'])/2)).round(2)
    itr.drop(columns=['Date_min','Date_max', 'Daily_Sales_sum', 'Earliest_Stock_Sum', 'Latest_Stock_Sum'], inplace=True)

    return itr

# Preprocessing for barpolar
@cache.memoize(timeout=600)
def preprocess_barpolar(metrics_raw_data):
    def calculate_inventory_turnover_ratio(metrics_raw_data: pd.DataFrame, target_quarter: str):
        # Group by quarter and product to get sales and date ranges
        inventory_metrics = metrics_raw_data.groupby(
            ['Year_Quarter', 'Product_ID'], 
            as_index=False
        ).agg({
            'Date': ['min', 'max'],
            'Daily_Sales': 'sum'
        })
        
        # Clean up column names
        inventory_metrics.columns = ['_'.join(col).strip() if col[1] else col[0] 
                                for col in inventory_metrics.columns.values]
        
        # Filter for target quarter
        inventory_metrics = inventory_metrics[inventory_metrics['Year_Quarter'] == target_quarter]
        
        # Calculate stock levels for start and end dates
        stock_levels = {}
        for date_type in ['min', 'max']:
            stock_levels[date_type] = {
                prod: metrics_raw_data[
                    (metrics_raw_data['Product_ID'] == prod) & 
                    (metrics_raw_data['Date'].isin(inventory_metrics[f'Date_{date_type}']))
                ]['Stock_Level'].sum()
                for prod in inventory_metrics['Product_ID'].unique()
            }
        
        # Add stock levels to dataframe
        inventory_metrics['Earliest_Stock_Sum'] = inventory_metrics['Product_ID'].map(stock_levels['min'])
        inventory_metrics['Latest_Stock_Sum'] = inventory_metrics['Product_ID'].map(stock_levels['max'])
        
        # Calculate ITR
        inventory_metrics['ITR'] = (
            inventory_metrics['Daily_Sales_sum'] / 
            ((inventory_metrics['Latest_Stock_Sum'] + inventory_metrics['Earliest_Stock_Sum']) / 2)
        ).round(2)
        
        return inventory_metrics[['Year_Quarter', 'Product_ID', 'ITR']]

    def calculate_stockout_ratio(metrics_raw_data: pd.DataFrame, target_quarter: str):
        stockout_metrics = metrics_raw_data.groupby(
            ['Year_Quarter', 'Product_ID'], 
            as_index=False
        ).agg({
            'Daily_Sales': 'sum',
            'Lost_Sales': 'sum'
        })
        
        stockout_metrics = stockout_metrics[stockout_metrics['Year_Quarter'] == target_quarter]
        
        stockout_metrics['stockout_ratio'] = (
            (stockout_metrics['Lost_Sales'] / 
            (stockout_metrics['Lost_Sales'] + stockout_metrics['Daily_Sales'])) * 100
        ).round(2)
        
        return stockout_metrics[['Year_Quarter', 'Product_ID', 'stockout_ratio']]

    def calculate_overstock_cost(metrics_raw_data: pd.DataFrame, target_quarter: str):
        quarterly_data = metrics_raw_data[metrics_raw_data['Year_Quarter'] == target_quarter]
        
        # Calculate daily metrics
        daily_metrics = quarterly_data.groupby(
            ['Year_Quarter', 'Product_ID', 'Date'], 
            as_index=False
        ).agg({
            'Daily_Sales': 'sum',
            'Stock_Level': 'sum',
            'Inventory_Holding_Cost': 'mean'
        })
        
        # Calculate final metrics
        overstock_metrics = (
            daily_metrics.sort_values('Date')
            .groupby(['Year_Quarter', 'Product_ID'], as_index=False)
            .agg({
                'Daily_Sales': 'mean',
                'Stock_Level': 'last',
                'Inventory_Holding_Cost': 'last'
            })
        )
        
        # Calculate overstock cost
        overstock_metrics['overstock_cost'] = (
            (overstock_metrics['Stock_Level'] - overstock_metrics['Daily_Sales']) * 
            overstock_metrics['Inventory_Holding_Cost']
        ).round(2)
        
        return overstock_metrics[['Year_Quarter', 'Product_ID', 'overstock_cost']]
    
    target_quarter = '2024-Q4'
    itr_df = calculate_inventory_turnover_ratio(metrics_raw_data, target_quarter)
    stockout_df = calculate_stockout_ratio(metrics_raw_data, target_quarter)
    overstock_df = calculate_overstock_cost(metrics_raw_data, target_quarter)
    
    # Combine all metrics
    combined_metrics = (
        itr_df
        .merge(stockout_df, on=['Product_ID', 'Year_Quarter'])
        .merge(overstock_df, on=['Product_ID', 'Year_Quarter'])
    )
    
    combined_metrics.rename(columns={'stockout_ratio':'Stockout Ratio', 'overstock_cost':'Overstock Cost'}, inplace=True)
    
    return combined_metrics

# Preprocessing forecast vs actual
def preprocess_fct_vs_act(metrics_raw_data):
    d_min30 = sorted(metrics_raw_data['Date'].unique().tolist())[-30:]
    fct_vs_act = metrics_raw_data[metrics_raw_data['Date'].isin(d_min30)]
    fct_vs_act = fct_vs_act.groupby('Date', as_index=False).agg({'Daily_Sales':'sum', 'Forecasted_Demand':'sum'})
    fct_vs_act = fct_vs_act.sort_values(by=['Date'])

    return fct_vs_act

overstock_cost = preprocess_overstock(metrics_raw_data)
stockout_ratio = preprocess_stockout(metrics_raw_data)
itr = preprocess_itr(metrics_raw_data)
barpolar = preprocess_barpolar(metrics_raw_data)
fct_vs_act = preprocess_fct_vs_act(metrics_raw_data)

# Normalize barpolar metric for better visualization
ITR_scaler = MinMaxScaler().fit(barpolar[['ITR']])
stockout_scaler = MinMaxScaler().fit(barpolar[['Stockout Ratio']])
overstock_scaler = MinMaxScaler().fit(barpolar[['Overstock Cost']])

def normalize_barpolar(barpolar):
    barpolar['ITR_norm'] = ITR_scaler.transform(barpolar[['ITR']])
    barpolar['stockout_ratio_norm'] = stockout_scaler.transform(barpolar[['Stockout Ratio']])
    barpolar['overstock_cost_norm'] = overstock_scaler.transform(barpolar[['Overstock Cost']])

    return barpolar

barpolar = normalize_barpolar(barpolar)

# ----------------------Dashboard Layout----------------------
app.layout = dbc.Container(
    class_name='body-container',
    fluid=True,
    children=[
        
    dbc.Row(
    class_name='header-container',
    children=[                         
        dbc.Col(
        class_name='title-and-logo',
        align='end',
        width=7,
        children=dbc.Stack(
            direction='horizontal',
            children=[                            
                html.Img(className='logo-iykra', src='assets/logo - white.png'),
                html.Img(className='logo-ai', src='assets/logo AI Engineer Fellowship-horizontal-white.png'), 
                html.H1('Stock Optimization Hub'),
            ]),
        ),
        dbc.Col(
        class_name='filter product-filter',
        align='center',
        width=dict(size=1, offset=1),
        children=product_filter(stock_pivot),
        ),
        dbc.Col(
            class_name='filter from-filter',
            align='center',
            width=1,
            children=from_filter(optim_df),
        ),
        dbc.Col(
            class_name='filter to-filter',
            align='center',
            width=1,
            children=to_filter(optim_df),
        ),
        ]
    ),
    html.Br(),
    dbc.Row([
        dbc.Col(
        width=5,
        children=[
            dbc.Row(
            class_name='metrics g-4',
            justify='start',
            children=[
                dbc.Col(
                class_name='overstock-cost-metric',
                width=4,
                children=dbc.Card(
                    class_name='card overstock-cost-card',
                    children=[
                        dbc.CardHeader('Overstock Cost'),
                        dbc.CardBody(
                        class_name='metric-card-body',
                        children=[
                            dbc.Row(
                            class_name='overstock-cost-card-body card-body g-0',
                            children=[
                                dbc.Col(
                                class_name='metric-column1',
                                children=dcc.Graph(
                                    id='overstock-cost-scorecard',
                                    config={'displayModeBar': False},
                                    figure=create_overstock_cost_scorecard(overstock_cost), 
                                    ),
                                    width=6,
                                ),
                                dbc.Col(
                                class_name='metric-column2',
                                children=dcc.Graph(
                                    id='overstock-cost-sparkline',
                                    figure=create_overstock_cost_sparkline(overstock_cost),
                                    config={'displayModeBar': False, 'staticPlot':True},
                                    ),
                                    width=6,
                                ),
                            ],
                            ),
                        ],
                        ),
                    ],
                ),
                ),
                dbc.Col(
                class_name='stockout-metric',
                width=4,
                children=dbc.Card(
                    class_name='card stockout-card',
                    children=[
                        dbc.CardHeader('Stockout Ratio'),
                        dbc.CardBody(
                        class_name='metric-card-body',
                        children=[
                            dbc.Row(
                            class_name='stockout-card-body card-body g-0',
                            children=[
                                dbc.Col(
                                class_name='metric-column1',
                                children=dcc.Graph(
                                    id='stockout-ratio-scorecard',
                                    config={'displayModeBar': False},
                                    figure=create_stockout_scorecard(stockout_ratio), 
                                    ),
                                    width=6,
                                ),
                                dbc.Col(
                                class_name='metric-column2',
                                children=dcc.Graph(
                                    id='stockout-ratio-sparkline',
                                    figure=create_stockout_sparkline(stockout_ratio),
                                    config={'displayModeBar': False, 'staticPlot':True},
                                    ),
                                    width=6,
                                ),
                            ],
                            ),
                        ],
                        ),
                    ],
                ),
                ),
                dbc.Col(
                class_name='itr-metric',
                width=4,
                children=dbc.Card(
                    class_name='card itr-card',
                    children=[
                        dbc.CardHeader('ITR'),
                        dbc.CardBody(
                        class_name='metric-card-body',
                        children=[
                            dbc.Row(
                            class_name='itr-card-body card-body g-0',
                            children=[
                                dbc.Col(
                                class_name='metric-column1',
                                children=dcc.Graph(
                                    id='itr-scorecard',
                                    config={'displayModeBar': False},
                                    figure=create_itr_scorecard(itr), 
                                    ),
                                    width=6,
                                ),
                                dbc.Col(
                                class_name='metric-column2',
                                children=dcc.Graph(
                                    id='itr-sparkline',
                                    figure=create_itr_sparkline(itr),
                                    config={'displayModeBar': False, 'staticPlot':True},
                                    ),
                                    width=6,
                                ),
                            ],
                            ),
                        ],
                        ),
                    ],
                ),
                ),
            ]
            ),
            html.Br(),
            dbc.Card(
            class_name='barpolar-card card',
            children=[
                dbc.CardHeader(
                    dbc.Row(
                    id='barpolar-sort',
                    class_name='barpolar g-0',
                    children=[
                        dbc.Col('Sort by:', width=2),
                        dbc.Col(dcc.Dropdown(
                        id='sort-dropdown',
                        options=[
                        {'label': html.Span(['Top 10 Highest Overstock Cost Product'], style={'color': '#000000', 'font-size': 20}), 'value': 'Overstock Cost'},
                        {'label': html.Span(['Top 10 Highest Stockout Ratio Product'], style={'color': '#000000', 'font-size': 20}), 'value': 'Stockout Ratio'},
                        {'label': html.Span(['Top 10 Slowest Inventory Turnover Product'], style={'color': '#000000', 'font-size': 20}), 'value': 'ITR'}
                        ],
                        style={'height':'10px', 'fontsize':'10px'},
                        ), width=10),
                    ],
                    ),
                ),
                dbc.CardBody(
                    dcc.Graph(
                    id='barpolar-chart',
                    style={'height':'470px','margin':'0'},
                    figure=create_barpolar_top_10(barpolar),
                    config={'displayModeBar': False}
                    ),
                ),
            ],
            ),
        ]),
        dbc.Col(
        class_name='line-group',
        width=7,
        children=[
            dbc.Row(
            class_name='line-group1',
            children=[
                dbc.Col(
                width=6,
                children=[
                    dbc.Card(
                    class_name='overstock-cost-line-card card',
                    children=[
                        dbc.CardHeader('Overstock Cost Quarterly'),
                        dbc.CardBody(
                        class_name='overstock-cost-line-card-body card-body',
                        children=[
                            dcc.Graph(
                            id='overstock-cost-linechart',
                            figure=create_overstock_cost_linechart(overstock_cost),
                            config={'displayModeBar': False},
                            ),
                        ])
                    ]),
                ]),
                dbc.Col(
                width=6,
                children=[
                    dbc.Card(
                    class_name='stockout-ratio-line-card card',
                    children=[
                        dbc.CardHeader('Stockout Ratio Quarterly'),
                        dbc.CardBody(
                        class_name='stockout-ratio-line-card-body card-body',
                        children=[
                            dcc.Graph(
                            id='stockout-ratio-linechart',
                            figure=create_stockout_linechart(stockout_ratio),
                            config={'displayModeBar': False},
                            ),
                        ])
                    ]),
                ]),
            ]),
            html.Br(),
            dbc.Row(
            class_name='line-group2',
            children=[
                dbc.Col(
                width=6,
                children=[
                    dbc.Card(
                    class_name='itr-line-card card',
                    children=[
                        dbc.CardHeader('Inventory Turnover Rate Quarterly'),
                        dbc.CardBody(
                        class_name='itr-line-card-body card-body',
                        children=[
                            dcc.Graph(
                            id='itr-linechart',
                            figure=create_itr_linechart(itr),
                            config={'displayModeBar': False},
                            ),
                        ])
                    ]),
                ]),
                dbc.Col(
                width=6,
                children=[
                    dbc.Card(
                    class_name='forecast-vs-actual-card card',
                    children=[
                        dbc.CardHeader('Historical Stock Forecast vs. Actual'),
                        dbc.CardBody(
                        class_name='forecast-vs-actual-line-card-body card-body',
                        children=[
                            dcc.Graph(
                            id='forecast-vs-actual-linechart',
                            figure=create_fct_vs_act_linechart(fct_vs_act),
                            config={'displayModeBar': False},
                            ),
                        ])
                    ]),
                ]),
            ]),
            html.Br(),
            dbc.Row(
                class_name='g-0',
                children=[
                dbc.Col(html.H4('Open table:'), width=3),
                dbc.Col(
                    dbc.Button(
                    "Current Stock Monitor",
                    id="open_stock",
                    className="button bottom-button",
                    n_clicks=0,
                    style={"margin": "0"}
                    ), width=4,  
                ),
                dbc.Col(
                    dbc.Button(
                    "Stock Optimization Plan",
                    id="open_optim",
                    className="button bottom-button",
                    n_clicks=0,
                    style={"margin": "0"}
                    ), width=4,  
                ),
            ]),
            
        ])
    ]),
    html.Div([
    # Tombol untuk membuka/meminimalkan chatbot
        html.Div(
            html.Button("💬 Chat", id="toggle-chat", style={"borderRadius": "10px", "width": "60px", "height": "60px", "backgroundColor": "#007BFF", "color": "white"}),
            style={"position": "fixed", "bottom": "35px", "right": "105px", "zIndex": "1000"}
        ),
        html.Div(id="chat-window", children = chatbox(),style={'display': 'none',"bottom": "105px", "right": "20px", "position": "fixed", "zIndex": "1000", "fontsize" : "14", "width":"400px"}),
    ]),
    dbc.Collapse(
        id='stock-pivot-collapse',
        is_open=False,
        children=[
            html.Br(),
            dbc.Button(
            "Save as Excel",
            id="save-button-stock-pivot",
            className="button save-button",
            n_clicks=0,
            style={"margin": "0"}
            ),
            create_current_stock_table(stock_pivot)
        ]
    ),
    dbc.Collapse(
        id='stock-optim-collapse',
        is_open=False,
        children=[
            html.Br(),
            dbc.Button(
            "Save as Excel",
            id="save-button-stock-optim",
            className="button save-button",
            n_clicks=0,
            style={"margin": "0"}
            ),
            create_stock_optim(optim_df)
        ]
    ),
])

# Callback to update_charts
@app.callback(
    Output('stockout-ratio-scorecard', 'figure'), 
    Output('stockout-ratio-sparkline', 'figure'), 
    Output('itr-scorecard', 'figure'),
    Output('itr-sparkline', 'figure'),
    Output('overstock-cost-scorecard', 'figure'),
    Output('overstock-cost-sparkline', 'figure'), 
    Output('stockout-ratio-linechart', 'figure'), 
    Output('itr-linechart', 'figure'), 
    Output('overstock-cost-linechart', 'figure'), 
    Output('barpolar-chart', 'figure'),
    Output('forecast-vs-actual-linechart', 'figure'),
    Input('product_filter_dropdown', 'value'),
    Input('from_filter_dropdown', 'value'),
    Input('to_filter_dropdown', 'value'),
    Input('sort-dropdown', 'value'),
    prevent_initial_call=True
)
def update_charts(selected_product_ids, 
                  selected_from_warehouse, 
                  selected_to_warehouse,
                  selected_sort_option):
    
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
        
    stockout_data = preprocess_stockout(filtered_metrics)
    itr_data = preprocess_itr(filtered_metrics)
    overstock_data = preprocess_overstock(filtered_metrics)
    barpolar_data = normalize_barpolar(preprocess_barpolar(filtered_metrics))
    forecast_data = preprocess_fct_vs_act(filtered_metrics)

    return [
        create_stockout_scorecard(stockout_data),
        create_stockout_sparkline(stockout_data),
        create_itr_scorecard(itr_data),
        create_itr_sparkline(itr_data),
        create_overstock_cost_scorecard(overstock_data),
        create_overstock_cost_sparkline(overstock_data),
        create_stockout_linechart(stockout_data),
        create_itr_linechart(itr_data),
        create_overstock_cost_linechart(overstock_data),
        create_barpolar_top_10(barpolar_data, sort_by=selected_sort_option),
        create_fct_vs_act_linechart(forecast_data),
    ]

@app.callback(
    Output('stock-pivot-collapse', 'is_open'),
    Input('open_stock', 'n_clicks'),
    State('stock-pivot-collapse', 'is_open'),
)
def toggle_stock_collapse(n, is_open):
    if n:
        return not is_open

@app.callback(
    Output('stock-optim-collapse', 'is_open'),
    Input('open_optim', 'n_clicks'),
    State('stock-optim-collapse', 'is_open'),
)
def toggle_optim_collapse(n, is_open):
    if n:
        return not is_open

@app.callback(
    Output('stock_pivot','rowData'),
    Output('stock_pivot', 'columnDefs'),
    Output('stock_optimization', 'rowData'),
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
    filtered_pivot= filtered_pivot[pivot_filter]

    selected_warehouse = [item for item in selected_warehouse if item != 'Supplier']
    columns = ['Product_ID']
    columns.extend(selected_warehouse or [])
    filtered_pivot = filtered_pivot[columns]
    filtered_pivot_col = [{'field': col, 'pinned': 'left'} if col == 'Product_ID' else {'field': col} for col in filtered_pivot.columns]
    
    # Filter filtered_optim 
    optim_filter = (filtered_optim['Product_ID'].isin(selected_products)) & \
                    (filtered_optim['From'].isin(selected_from)) & \
                    (filtered_optim['To'].isin(selected_to))
    filtered_optim = filtered_optim[optim_filter]

    return filtered_pivot.to_dict('records'), filtered_pivot_col, filtered_optim.to_dict('records')

# Save as csv
@callback(
    Output("stock_pivot", "exportDataAsCsv"),
    Input("save-button-stock-pivot", "n_clicks"),
)
def export_stock_pivot_as_csv(n_clicks):
    if n_clicks:
        return True
    return False

@callback(
    Output("stock_optimization", "exportDataAsCsv"),
    Input("save-button-stock-optim", "n_clicks"),
)
def export_stock_optim_as_csv(n_clicks):
    if n_clicks:
        return True
    return False

# Callback to show chatbot window
# Callback untuk menampilkan/menyembunyikan chatbot
@app.callback(
    Output("chat-window", "style"),
    Input("toggle-chat", "n_clicks"),
    State("chat-window", "style"),
    prevent_initial_call=True
)
def toggle_chat(n_clicks, current_style):
    if current_style["display"] == "none":
        return {**current_style, "display": "block"}
    return {**current_style, "display": "none"}

@socketio.on("connect")
def on_connect():
    print("Client connected")

@socketio.on("disconnect")
def on_disconnect():
    print("Client disconnected")

def response_chatbot(user_input, socket_id):
    df = retrieve(user_input, top_k=5)
    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in global_chat_histories])

    # Generate insights
    insights = []

    # Basic DataFrame Information
    insights.append(
        f"The DataFrame contains {len(df)} rows and {len(df.columns)} columns."
    )
    insights.append("Here are the first 5 rows of the DataFrame:\n")
    insights.append(df.head().to_string(index=False))

    # Summary Statistics
    insights.append("\nSummary Statistics:")
    insights.append(df.describe().to_string())

    # Column Information
    insights.append("\nColumn Information:")
    for col in df.columns:
        insights.append(f"- Column '{col}' has {df[col].nunique()} unique values.")

    insights_text = "\n".join(insights)

    prompt = (
        "Role: You are an inventory optimization assistant.You can only answer questions related to inventory optimization.You are not allowed to answer questions outside of inventory optimization."
        "Objective: Provide insights for inventory optimization."
        "Instructions: You will be given a dataset containing inventory information from a company, including product data, stock levels, demand rates, lead times, and other relevant data. Your task is to provide insights that can help optimize the company's inventory management. The insights should be based on the available data and aim to improve efficiency, reduce waste, and ensure optimal stock levels."
        "Possible areas to explore:"
        "1.Identify Overstocked and Understocked Products: Find products that are overstocked or understocked and recommend adjustments in ordering or stock management."
        "2.Demand Forecasting: Use historical data to predict future demand and recommend changes in procurement strategies."
        "3.Inventory Turnover Analysis: Identify products with slow turnover rates and provide suggestions to increase sales or reduce order quantities."
        "4.Lead Time Optimization: Analyze the lead time for specific products and recommend when to reorder to ensure stock availability without overstocking."
        "5.Storage Space Management: Provide suggestions on how to optimize storage space usage based on inventory data."
        "6.Cost Analysis: Identify high-cost products that are not moving or selling well, and suggest ways to reduce storage costs or find alternative suppliers."
        "Provide data-driven insights to improve inventory management, making it more efficient and cost-effective. Ensure that the recommendations align with the goal of optimization and cost savings for the company."
        "The user should be invited to ask another question at the end of the response. You can also respond based on the conversation history. You can also answer in Indonesian, depending on the user's question"
        #"You can also answer in Indonesian, depending on the user's question. The user should be invited to ask another question at the end of the response"
        #"In addition to the insights, generate visualizations that help better understand and communicate the data."
    )
    messages = [{"role": "system", "content": f"{prompt}\n\nContext:\n\n{insights_text}\n\nconversation history: {conversation_history}"}]
    messages.append({"role": "user", "content": user_input})  # Tambahkan pertanyaan baru

    prompt = f"{prompt}\n\nContext:\n\n{insights_text}"
    prompt = f"""{prompt}\n\nUser's Question: {user_input}"""
    prompt = f"{prompt}\n\nconversation history: {conversation_history}"

    response = openai.ChatCompletion.create(
    model="gpt-4o", messages=messages, max_tokens=500, stream=True
    #model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
    )
    bot_response = ""  # Mengembalikan respons dari chatbot
    for chunk in response:
        if len(chunk.choices) > 0:
            text = chunk['choices'][0]['delta'].get('content' ,'')
            if text:
                bot_response += text
                
                socketio.emit("stream", text, namespace="/", to=socket_id)
                time.sleep(0.05)

    bot_message = {
        "role": "bot",
        "content": bot_response,
        "style":{
            'backgroundColor': '#f1f1f1', 'color': 'black', 'padding': '8px', 'borderRadius': '10px', 'marginBottom': '5px',
            'alignSelf': 'flex-start', 'maxWidth': '80%', 'margin-right': 'auto', 'whiteSpace': 'pre-wrap', 'fontFamily': 'Helvetica', 'textAlign': 'left', 'margin-left': '5px'
        }
    }
    # Perbarui chat_history
    global_chat_histories.append(bot_message)

    chat_elements = [
        html.Div(message["content"], style=message["style"])
        for message in global_chat_histories
    ]
    return chat_elements, global_chat_histories, "", []

# callback untuk chatbot
@callback(
    Output('chat-box', 'children'), 
    Output('chat-history', 'data'), 
    Output('user-input', 'value'),
    Output("notification_wrapper", "children", allow_duplicate=True),
    Input('send-button', 'n_clicks'),
    State('user-input', 'value'), 
    State('chat-history', 'data'), 
    State("socketio", "socketId"),
    running=[[Output("streaming-process", "children"), "", None]],
    prevent_initial_call=True
    )
def update_chatbot_output(n_clicks, user_input, chat_history, socket_id):
    if not user_input or not socket_id:
        return dash.no_update, chat_history, "", []

    # Jika tidak ada, inisialisasi sebagai list kosong
    if chat_history is None:
        chat_history = []
    
        # Pesan dari pengguna
    user_message = {
        "role": "user",
        "content": user_input,
        "style":{
            'backgroundColor': '#007bff', 'color': 'white', 'padding': '8px', 'borderRadius': '10px', 'marginBottom': '5px',
            'alignSelf': 'flex-end', 'maxWidth': '80%', 'margin-left': 'auto', 'fontFamily': 'Helvetica', 'width' : 'fit-content', 'margin-right': '5px'
        }
    }

    chat_history.append(user_message)
    global_chat_histories.append(user_message)

    chat_elements = [
        html.Div(message["content"], style=message["style"])
        for message in global_chat_histories
        ]
    thread = threading.Thread(target=response_chatbot, args=(user_input, socket_id))
    thread.start()
    return chat_elements, chat_history, "", []

if __name__ == "__main__":
    app.run_server(debug=True)