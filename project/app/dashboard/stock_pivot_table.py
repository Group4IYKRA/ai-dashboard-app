import pandas as pd
import dash_ag_grid as dag
from datetime import datetime

def create_current_stock_table(stock_pivot=None):
    columnDefs = [{'field': col, 'pinned': 'left', 'width':100} if col == 'Product_ID' else {'field': col, 'width':150} for col in stock_pivot.columns]

    grid = dag.AgGrid(
        id='stock_pivot',
        rowData=stock_pivot.to_dict('records'),
        columnDefs=columnDefs,
        columnSize=None,
        className="ag-theme-quartz-dark",
        defaultColDef={"filter": "agTextColumnFilter", "tooltipComponent": "CustomTooltipSimple"},     
        dashGridOptions={'animateRows': False, 
                        'pagination':True, 
                        'paginationPageSize': 20, 
                        'tooltipShowDelay': 0,
                        'tooltipHideDelay': 2000
                        },
        csvExportParams={
            'fileName': f'current_stock{datetime.now()}.csv',
        },

    )
    return grid
