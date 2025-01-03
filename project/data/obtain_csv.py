from project import *
import pandas as pd

# Function to download and save CSV files
def download_and_save_csv(gcs_path, local_path):
    try:
        df = pd.read_csv(download_from_gcs(gcs_path))
        df.to_csv(local_path, index=False)
        print(f"Downloaded and saved {local_path}")
    except Exception as e:
        print(f"Failed to download or save {local_path}: {e}")

# Get all necessary dataframes from Google Cloud Storage
download_and_save_csv('query_result/stock_pivot_data.csv', 'project/data/processed/stock_pivot_data.csv')
download_and_save_csv('models/pulp_result/pulp_result_data.csv', 'project/data/processed/pulp_result_data.csv')
download_and_save_csv('query_result/metrics_raw_data.csv', 'project/data/processed/metrics_raw_data.csv')
# download_and_save_csv('query_result/itr_raw_data.csv', 'project/data/processed/itr_raw_data.csv')
# download_and_save_csv('query_result/overstock_cost_raw_data.csv', 'project/data/processed/overstock_cost_raw_data.csv')
# download_and_save_csv('query_result/stockout_ratio_raw_data.csv', 'project/data/processed/stockout_ratio_raw_data.csv')