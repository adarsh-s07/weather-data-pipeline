from snowflake.snowpark import Session
from snowflake.snowpark import functions as F
from snowflake.snowpark import exceptions as E
from dotenv import load_dotenv
import os, logging

load_dotenv()

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('snowflake/logs/preload.log')
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

connection_params = {
    "account": os.getenv("SF_ACCT_ID"),
    "user": os.getenv("SF_USER_NAME"),
    "password": os.getenv("SF_PAT"),
    "role":      "ACCOUNTADMIN",
    "warehouse": "WEATHERDATA_WH",
    "database":  "WEATHER_API_DATA",
    "schema":    "BRONZE"
}

session = Session.builder.configs(connection_params).create()

logger.info("Connected to Snowflake!")
print("Connected to SNowflake")

#Loading Data

# try: 
session.sql("""
CREATE OR REPLACE TABLE raw_json_data(
    json_dump VARIANT,
    file_name STRING,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    );""").collect()

session.sql("""
    CREATE OR REPLACE FILE FORMAT impossible_json_format
        TYPE = 'JSON'
        STRIP_OUTER_ARRAY = TRUE;
""").collect()

session.sql(f"""
CREATE OR REPLACE STAGE impossible_cloud_storage
    URL = 's3compat://weather-api-dump'
    ENDPOINT = 'eu-central-2.storage.impossibleapi.net'
    CREDENTIALS = (
        AWS_KEY_ID = '{os.getenv("IMPOSSIBLE_CLOUD_ACCESS_KEY")}', 
        AWS_SECRET_KEY = '{os.getenv("IMPOSSIBLE_CLOUD_SECRET_KEY")}'
    )
    FILE_FORMAT = impossible_json_format

""").collect()

session.sql("""
    COPY INTO raw_json_data (json_dump, file_name)
    FROM (
        SELECT $1, METADATA$FILENAME
        FROM @impossible_cloud_storage
    )
    ON_ERROR = 'SKIP_FILE'
""").collect()
# except:
#     logger.error("Unable to create Table!")




