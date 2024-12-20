# Query BigQuery and store raw data
import pandas as pd
from config import *

# Query to get pivot of latest stock
# Step 1: Collect distinct warehouse_loc_ids (concatenation of warehouse_loc and warehouse_id) into an array
def get_warehouse_ids():
    query_warehouse_ids = f"""
    SELECT ARRAY_AGG(DISTINCT CONCAT(Warehouse_Location, '-', Warehouse_ID) ORDER BY CONCAT(Warehouse_Location, '-', Warehouse_ID) ASC) AS warehouse_loc_ids
    FROM `{test_table_path}`
    """
    warehouse_loc_ids = client.query(query_warehouse_ids).result().to_dataframe().iloc[0, 0]
    return warehouse_loc_ids

# Step 2: Get the max date
def get_max_date():
    query_max_date = f"""
    SELECT MAX(Date) AS max_date
    FROM `{test_table_path}`
    """
    max_date = client.query(query_max_date).result().to_dataframe().iloc[0, 0]
    return max_date

# Step 3: Get list of warehouse_loc_ids
def get_warehouse_loc_ids_str():
    warehouse_loc_ids = get_warehouse_ids()
    warehouse_loc_ids_str = ', '.join([f"'{item}'" for item in warehouse_loc_ids])
    return warehouse_loc_ids_str

# Step 4: Build dynamic PIVOT query
def get_stock_pivot_table():
    max_date = get_max_date()
    warehouse_loc_ids_str = get_warehouse_loc_ids_str()

    stock_pivot_table_query = f"""
    SELECT * FROM (
        SELECT Product_ID, Category, Brand, Color,
        CONCAT(Warehouse_Location, '-', Warehouse_ID) AS Warehouse_Loc_ID, IFNULL(Stock_Level, 0) AS Stock_Level
        FROM `{test_table_path}`
        WHERE Date = '{max_date}'
    ) PIVOT (
        SUM(IFNULL(Stock_Level, 0)) FOR Warehouse_Loc_ID IN ({warehouse_loc_ids_str})
    )
    """
    stock_pivot_table = client.query(stock_pivot_table_query).result().to_dataframe()
    return stock_pivot_table

# Query Item_transfer cost data
def get_cost_table():
    cost_table_query = f"""
    SELECT * FROM `{cost_table_path}`
    """
    cost_table = client.query(cost_table_query).result().to_dataframe()
    return cost_table

# Query the raw data for pulp
def get_pulp_raw():
    pulp_raw_query = f"""
    SELECT 
        Product_ID, 
        CONCAT(Warehouse_Location, '-', Warehouse_ID) as Warehouse_Loc_ID,
        Stock_Level, 
        Forecasted_Demand, 
        Supply_Cost_Per_Unit
    FROM `{test_table_path}`
    WHERE Date = (SELECT MAX(Date) FROM `{test_table_path}`)
    """
    pulp_raw_table = client.query(pulp_raw_query).result().to_dataframe()
    return pulp_raw_table