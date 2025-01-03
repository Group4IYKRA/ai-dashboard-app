# Configuration for the app
import os
from google.cloud import bigquery, storage
from dotenv import load_dotenv
from io import StringIO, BytesIO
import gc

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Retrieve values from the environment variables
project_id = os.getenv("PROJECT_ID")
dataset_id = os.getenv("DATASET_ID")
test_table_name = os.getenv("TEST_TABLE_NAME")
cost_table_name = os.getenv("COST_TABLE_NAME")
view_name = os.getenv("VIEW_NAME")
bucket_name = os.getenv("BUCKET_NAME")

test_table_path = f"{project_id}.{dataset_id}.{test_table_name}"
cost_table_path = f"{project_id}.{dataset_id}.{cost_table_name}"

# Initialize the BigQuery client
client = bigquery.Client()

# Initialize Cloud Storage Client
storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)

# Define function to upload to GCS
def upload_to_gcs(df, blob_name):
    """
    Upload dataframe given in argument into Google Cloud Storage
    Args:
        df: pd.DataFrame
        blob_name: destination file name in GCS
    """
    # Define the bucket and blob (file) name
    blob = bucket.blob(blob_name)

    # Save the DataFrame to a CSV file in Google Cloud Storage using a buffer
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    # Upload the buffer to Google Cloud Storage with a timeout
    blob.upload_from_file(buffer, content_type='text/csv', timeout=600)

    # Explicitly delete the DataFrame and call the garbage collector
    del df
    gc.collect()

def download_from_gcs(blob_name):
    """
    Download a file from Google Cloud Storage and return its content.
    Args:
        blob_name: destination file name in GCS
    Return:
        content: BytesIO(content)
    """
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    content = blob.download_as_bytes()
    return BytesIO(content)