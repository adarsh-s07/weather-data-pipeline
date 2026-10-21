
from dotenv import load_dotenv
import os

load_dotenv()

# Connection Parameters for Snowflake

SF_CONN_PARAM = {
    "account": os.getenv("SF_ACCT_ID"),
    "user": os.getenv("SF_USER_NAME"),
    "password": os.getenv("SF_PAT"),
    "role":      "ACCOUNTADMIN",
    "warehouse": "WEATHERDATA_WH",
    "database":  "WEATHER_API_DATA",
}