from google.cloud import bigquery
from project.data.config import *

# Check if query returns warehouse IDs
def test_query():
    query = f"""
    SELECT *
    FROM `{test_table_path}`
    LIMIT 1
    """
    result = client.query(query).result().to_dataframe()
    print("Query Result:", result.head())  # Check if any results are returned

test_query()
