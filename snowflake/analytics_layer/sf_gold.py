from snowflake.snowpark import Session, functions as F
from dotenv import load_dotenv
import os

load_dotenv()

SF_CONN_PARAM = {
    "account": os.getenv("SF_ACCT_ID"),
    "user": os.getenv("SF_USER_NAME"),
    "password": os.getenv("SF_PAT"),
    "role":      "ACCOUNTADMIN",
    "warehouse": "WEATHERDATA_WH",
    "database":  "WEATHER_API_DATA",
    "schema": "GOLD"
}

session = Session.builder.configs(SF_CONN_PARAM).getOrCreate()

silver_table = session.read.table("WEATHER_API_DATA.SILVER.WEATHER_DATA_CLEANED")

dim_location = silver_table.select(
    F.concat(F.col('country'), F.lit(' - '), F.col('city')).alias('location_key'),
    'country', 'city',
    'timezone', 'longitude', 'latitude'
)

dim_location.write.mode("overwrite").saveAsTable("WEATHER_API_DATA.GOLD.DIM_LOCATION")

print("Saved Locations Table")

fact_weather_data = silver_table.select(
    F.concat(F.col('country'), F.lit(' - '), F.col('city')).alias('location_key'),
    'chance_of_rain', 'weather_condition',
    'feels_like', 'humidity',
    F.col('temperature').alias('temperature_c'),
    'wind_speed', 'recorded_timestamp'
)

fact_weather_data.write.mode("overwrite").saveAsTable("WEATHER_API_DATA.GOLD.FACT_WEATHER_DATA")

print("Saved Fact Table")