from snowflake.snowpark import Session, functions as F
from snowflake.snowpark.types import StringType, FloatType, IntegerType, TimestampType
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
    "schema": "SILVER"
}

session = Session.builder.configs(SF_CONN_PARAM).getOrCreate()

bronze_table = session.read.table("WEATHER_API_DATA.BRONZE.RAW_JSON_DATA")

silver_table = bronze_table.select(
    F.col('JSON_DUMP')[0]['current']['chance_of_rain'].cast(IntegerType()).alias('chance_of_rain'),
    F.col('JSON_DUMP')[0]['current']['condition']['text'].cast(StringType()).alias('weather_condition'),
    F.col('JSON_DUMP')[0]['current']['feelslike_c'].cast(FloatType()).alias('feels_like'),
    F.col('JSON_DUMP')[0]['current']['humidity'].cast(IntegerType()).alias('humidity'),
    F.col('JSON_DUMP')[0]['current']['temp_c'].cast(IntegerType()).alias('temperature'),
    F.col('JSON_DUMP')[0]['current']['wind_kph'].cast(IntegerType()).alias('wind_speed'),
    F.col('JSON_DUMP')[0]['ingested_at'].cast(TimestampType()).alias('recorded_timestamp'),

    F.col('JSON_DUMP')[0]['location']['country'].cast(StringType()).alias('country'),
    F.col('JSON_DUMP')[0]['location']['name'].cast(StringType()).alias('city'),
    F.col('JSON_DUMP')[0]['location']['tz_id'].cast(StringType()).alias('timezone'),
    F.col('JSON_DUMP')[0]['location']['lon'].cast(FloatType()).alias('longitude'),
    F.col('JSON_DUMP')[0]['location']['lat'].cast(FloatType()).alias('latitude'),
).drop_duplicates()

silver_table.write.saveAsTable("WEATHER_API_DATA.SILVER.WEATHER_DATA_CLEANED")

print("Data Written Successfully!")