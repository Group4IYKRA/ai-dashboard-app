import os
import pandas as pd
import pickle as pkl
from query import *
from config import *

# Define the path to query_result directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
query_result_dir = os.path.join(project_root, 'data', 'query_result')

# Ensure the directory exists
if not os.path.exists(query_result_dir):
    os.makedirs(query_result_dir)

# Save dataframe into pickle
# stock_pivot_table
def save_stock_pivot_table():
    stock_pivot_df = get_stock_pivot_table()

    stock_pivot_file = os.path.join(query_result_dir, 'stock_pivot_data.pkl')

    with open(stock_pivot_file, 'wb') as f:
        pkl.dump(stock_pivot_df, f)

    return

# cost_table
def save_cost_table():
    cost_table_df = get_cost_table()

    cost_table_file = os.path.join(query_result_dir, 'cost_table_data.pkl')

    with open(cost_table_file, 'wb') as f:
        pkl.dump(cost_table_df, f)

    return

# cost_table
def save_pulp_raw():
    pulp_raw_df = get_pulp_raw()

    pulp_raw_file = os.path.join(query_result_dir, 'pulp_raw_data.pkl')

    with open(pulp_raw_file, 'wb') as f:
        pkl.dump(pulp_raw_df, f)

    return

# Run the jobs
save_stock_pivot_table()
save_cost_table()
save_pulp_raw()