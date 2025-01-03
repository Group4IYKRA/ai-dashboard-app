# Query BigQuery and store raw data
import pandas as pd
from project import *

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
    df = client.query(stock_pivot_table_query).result().to_dataframe()
    upload_to_gcs(df, 'query_result/stock_pivot_data.csv')

# Query Item_transfer cost data
def get_cost_table():
    cost_table_query = f"""
    SELECT * FROM `{cost_table_path}`
    """
    df = client.query(cost_table_query).result().to_dataframe()
    upload_to_gcs(df, 'query_result/cost_table_data.csv')

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
    df = client.query(pulp_raw_query).result().to_dataframe()
    upload_to_gcs(df, 'query_result/pulp_raw_data.csv')

def get_metrics_raw():
    metrics_raw_query = f"""
    SELECT 
        Date, 
        EXTRACT(YEAR FROM Date) as Year, 
        EXTRACT(QUARTER FROM Date) as Q,
        EXTRACT(MONTH FROM Date) as Month,
        EXTRACT(WEEK FROM Date) as Week,
        CONCAT(EXTRACT(YEAR FROM Date), '-Q', EXTRACT(QUARTER FROM Date)) as Year_Quarter,
        Product_ID, 
        CONCAT(Warehouse_Location, '-', Warehouse_ID) as Warehouse_Loc_ID, 
        Daily_Sales, 
        Stock_Level,
        Inventory_Holding_Cost,
        Lost_Sales
    FROM `{test_table_path}`
    WHERE EXTRACT(YEAR FROM Date) BETWEEN 2023 AND 2024
    """
    df = client.query(metrics_raw_query).result().to_dataframe()
    upload_to_gcs(df, 'query_result/metrics_raw_data.csv')

# # Query raw data for stockout ratio
# def get_stockout_ratio_raw():
#     stockout_ratio_raw_query = f"""
#     SELECT 
#         Date, 
#         EXTRACT(YEAR FROM Date) as Year, 
#         EXTRACT(QUARTER FROM Date) as Q, 
#         CONCAT(EXTRACT(YEAR FROM Date), '-Q', EXTRACT(QUARTER FROM Date)) as Year_Quarter,
#         Product_ID, 
#         CONCAT(Warehouse_Location, '-', Warehouse_ID) as Warehouse_Loc_ID, 
#         Daily_Sales, 
#         Lost_Sales
#     FROM `{test_table_path}`
#     WHERE EXTRACT(YEAR FROM Date) BETWEEN 2023 AND 2024
#     """
#     df = client.query(stockout_ratio_raw_query).result().to_dataframe()
#     upload_to_gcs(df, 'query_result/stockout_ratio_raw_data.csv')

# def get_itr_raw():
#     itr_raw_query = f"""
#     SELECT 
#         Date, 
#         EXTRACT(YEAR FROM Date) as Year, 
#         EXTRACT(QUARTER FROM Date) as Q, 
#         CONCAT(EXTRACT(YEAR FROM Date), '-Q', EXTRACT(QUARTER FROM Date)) as Year_Quarter,
#         Product_ID, 
#         CONCAT(Warehouse_Location, '-', Warehouse_ID) as Warehouse_Loc_ID, 
#         Daily_Sales, 
#         Stock_Level
#     FROM `{test_table_path}`
#     WHERE EXTRACT(YEAR FROM Date) BETWEEN 2023 AND 2024
#     """
#     df = client.query(itr_raw_query).result().to_dataframe()
#     upload_to_gcs(df, 'query_result/itr_raw_data.csv')

# def get_itr_raw():
#     itr_raw_query = f"""
#     WITH Quarterly_Data AS (
#       SELECT
#         FORMAT_TIMESTAMP('%Y-Q%Q', Date) AS Year_Quarter,
#         MIN(Date) AS Earliest_Date,
#         MAX(Date) AS Latest_Date
#       FROM
#         `{test_table_path}`
#       WHERE
#         EXTRACT(YEAR FROM Date) BETWEEN 2023 AND 2024
#       GROUP BY
#         Year_Quarter
#     ),
#     Stock_Summary AS (
#       SELECT
#         q.Year_Quarter,
#         q.Earliest_Date,
#         q.Latest_Date,
#         SUM(CASE WHEN t.Date = q.Earliest_Date THEN Stock_Level ELSE 0 END) AS Stock_Level_Earliest,
#         SUM(CASE WHEN t.Date = q.Latest_Date THEN Stock_Level ELSE 0 END) AS Stock_Level_Latest,
#         SUM(t.Daily_Sales) AS Total_Sales
#       FROM
#         Quarterly_Data q
#       JOIN
#         `{test_table_path}` t
#       ON
#         FORMAT_TIMESTAMP('%Y-Q%Q', t.Date) = q.Year_Quarter
#       GROUP BY
#         q.Year_Quarter, q.Earliest_Date, q.Latest_Date
#     )
#     SELECT
#       Year_Quarter,
#       ROUND(Total_Sales/((Stock_Level_Earliest+Stock_Level_Latest)/2),2) as ITR
#     FROM
#       Stock_Summary
#     ORDER BY
#       Year_Quarter;
#         """
#     df = client.query(itr_raw_query).result().to_dataframe()
#     upload_to_gcs(df, 'query_result/itr_raw_data.csv')

# def get_overstock_cost_raw():
#     overstock_cost_raw_query = f"""
#     SELECT
#       FORMAT_TIMESTAMP('%Y-Q%Q', Date) AS Year_Quarter,
#       (SUM(Stock_Level) - SUM(Daily_Sales)) * SUM(Inventory_Holding_Cost) AS Overstock_Cost
#     FROM
#       `{test_table_path}`
#     WHERE
#       EXTRACT(YEAR FROM Date) BETWEEN 2023 AND 2024
#     GROUP BY
#       Year_Quarter
#     ORDER BY
#       Year_Quarter;

#     """
#     df = client.query(overstock_cost_raw_query).result().to_dataframe()
#     upload_to_gcs(df, 'query_result/overstock_cost_raw_data.csv')

# Run the query and save in GCS
get_stock_pivot_table()
get_cost_table()
get_pulp_raw()
get_metrics_raw()
# get_stockout_ratio_raw()
# get_itr_raw()
# get_overstock_cost_raw()
