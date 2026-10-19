"""
# CREATE THIS PIPELINE BECAUSE THE COPY_TO FUNCTION IS DISABLED FOR IMPOSSIBLE CLOUD
# 
# THIS IS AN ALTERNATIVE APPROACH TO LOAD JSON FILE TO SNOWFLAKE AS THE FILE SIZES ARE SMALLER
# 
"""

import boto3, os, json, datetime
from snowflake.snowpark import Session, functions as F
from dotenv import load_dotenv

load_dotenv()

s3_client = boto3.client(
    's3',
    aws_access_key_id = os.getenv("IMPOSSIBLE_CLOUD_ACCESS_KEY"),
    aws_secret_access_key = os.getenv("IMPOSSIBLE_CLOUD_SECRET_KEY"),
    endpoint_url = 'https://eu-central-2.storage.impossibleapi.net'
)

files = []

bucket_key = 'weather-api-dump'
paginator = s3_client.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket = bucket_key)

for page in pages:
    if 'Contents' in page:
        for obj in page['Contents']:
            file_key = obj['Key']

            if file_key.endswith('.json'):
                files.append(file_key)

print(f"Found {len(files)} JSON files in the bucket")


#Loading Data to Snowflake

connection_params = {
    "account": os.getenv("SF_ACCT_ID"),
    "user": os.getenv("SF_USER_NAME"),
    "password": os.getenv("SF_PAT"),
    "role":      "ACCOUNTADMIN",
    "warehouse": "WEATHERDATA_WH",
    "database":  "WEATHER_API_DATA",
    "schema":    "BRONZE"
}

session = Session.builder.configs(connection_params).getOrCreate()
print("Connected to Snowflake")

curr_time = datetime.datetime.now().isoformat()

session.sql("""
    CREATE TABLE IF NOT EXISTS WEATHER_API_DATA.BRONZE.RAW_JSON_DATA (
        JSON_DUMP VARIANT,
        FILE_NAME VARCHAR(16777216),
        LOADED_AT TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP()
    );
""").collect()

already_loaded_rows = session.table("WEATHER_API_DATA.BRONZE.RAW_JSON_DATA").select(F.col('FILE_NAME')).distinct()
already_loaded_files = [row['FILE_NAME'] for row in already_loaded_rows]

files_to_process = list(set(files) - set(already_loaded_files))

if len(files_to_process)==0:
    print("No new files to be ingested!")

else:
    for file_key in files_to_process:
        file = s3_client.get_object(Bucket=bucket_key, Key=file_key)
        raw_json_string = file['Body'].read().decode('utf-8')
        json_data = json.loads(raw_json_string)

        if isinstance(json_data, dict):
            json_data = [json_data]

        rows_to_insert = [
            {
                "JSON_DUMP": json.dumps(json_data),
                "FILE_NAME": file_key,
                "LOADED_AT": curr_time
            } for item in json_data
        ]

        df = session.create_dataframe(rows_to_insert)

        df_final = df.select(
            F.parse_json(F.col('JSON_DUMP')).alias('JSON_DUMP'),
            F.col('FILE_NAME'),
            F.col('LOADED_AT')
        )

        df_final.write.mode('append').save_as_table("raw_json_data")

    print(f"Loaded {len(files_to_process)} JSON files to Snowflake!")