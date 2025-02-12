import pandas as pd
from dash import html, dash_table
import dash_ag_grid as dag

def create_stock_optim(optim_df=None):
    columnDefs = [{'field':col} for col in optim_df.columns]

    grid = dag.AgGrid(
        id='stock_optimization',
        rowData=optim_df.to_dict('records'),
        columnDefs=columnDefs,
        columnSize="responsiveSizeToFit",
        className="ag-theme-quartz-dark",
        defaultColDef={
            "filter": "agTextColumnFilter",
            "tooltipComponent": "CustomTooltipSimple",
            "cellStyle": {
                "whiteSpace": "normal",      
                "wordBreak": "break-word",   
                "lineHeight": "1.1",                
        }},     
        dashGridOptions={
            'animateRows': False, 
            'pagination':True, 
            'paginationPageSize': 20, 
            'tooltipShowDelay': 0,
            'tooltipHideDelay': 2000
        },
        style={'width':'50%', 'justify':'center'},
        csvExportParams={
            'fileName': 'stock-optimization-plan.csv',
        },

    )
    return grid