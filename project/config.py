# Configuration for the app
from google.cloud import bigquery, secretmanager

def access_secret(secret_name):
    project_id = 'b-508911'
    client = secretmanager.SecretManagerServiceClient()
    secret_path = f'projects/{project_id}/secrets/{secret_name}/versions/latest'
    response = client.access_secret_version(request={'name':secret_path})

    return response.payload.data.decode('UTF-8')

# Retrieve values from the environment variables
dataset_id = access_secret('DATASET_ID')
test_table_name = access_secret('TEST_TABLE_NAME')
cost_table_name = access_secret('COST_TABLE_NAME')
view_name = access_secret('VIEW_NAME')
bucket_name = access_secret('BUCKET_NAME')
open_ai_key = access_secret('OPEN_AI_API_KEY')

test_table_path = f'b-508911.{dataset_id}.{test_table_name}'
cost_table_path = f'b-508911.{dataset_id}.{cost_table_name}'

# Initialize the BigQuery client
client = bigquery.Client()