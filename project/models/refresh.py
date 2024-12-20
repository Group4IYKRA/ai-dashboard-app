import os
import pandas as pd
import pickle as pkl
from pulp_solver import *

# Define the path to query_result directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
models_result_dir = os.path.join(project_root, 'models', 'models_result')

# Ensure the directory exists
if not os.path.exists(models_result_dir):
    os.makedirs(models_result_dir)

# Save dataframe into pickle
# pulp result
def save_pulp_result():
    pulp_result_df = pulp_solver()

    pulp_result_file = os.path.join(models_result_dir, 'pulp_result_data.pkl')

    with open(pulp_result_file, 'wb') as f:
        pkl.dump(pulp_result_df, f)

    return

# Run pulp solver and save
save_pulp_result()