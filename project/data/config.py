# Configuration for the app
import os
from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

# Retrieve values from the environment variables
project_id = os.getenv("PROJECT_ID")
dataset_id = os.getenv("DATASET_ID")
test_table_name = os.getenv("TEST_TABLE_NAME")
cost_table_name = os.getenv("COST_TABLE_NAME")
view_name = os.getenv("VIEW_NAME")

test_table_path = f"{project_id}.{dataset_id}.{test_table_name}"
cost_table_path = f"{project_id}.{dataset_id}.{cost_table_name}"

# Initialize the BigQuery client
client = bigquery.Client()