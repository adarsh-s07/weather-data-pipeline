import requests, boto3
import os, json, datetime, logging
from dotenv import load_dotenv
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

load_dotenv()

#Initializing logging

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('src/logs/ingestion.log')
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def create_request_session():
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[408, 429, 500, 502, 503, 504]
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://",  adapter)
    session.mount("https://", adapter)

    return session

def s3_client_initialize():
    s3_client = boto3.client(
        's3',
        aws_access_key_id = os.getenv("IMPOSSIBLE_CLOUD_ACCESS_KEY"),
        aws_secret_access_key = os.getenv("IMPOSSIBLE_CLOUD_SECRET_KEY"),
        endpoint_url = 'https://eu-central-2.storage.impossibleapi.net'
    )
    return s3_client

def harvest_weather_data():
    city = "Bengaluru"
    weather_api = os.getenv("WEATHER_API_KEY")

    url = f"http://api.weatherapi.com/v1/forecast.json?key={weather_api}&q={city}&days=1&aqi=no&alerts=no"

    session = create_request_session()

    try:
        r = session.get(url)

        if r.status_code == 429 or r.status_code>=500:
            logger.warning(f"Recieved status code {r.status_code}, Retrying...")
            r.raise_for_status()
        
        elif r.status_code == 200:
            logging.info("API Connected Successfully!")
            weather_data = r.json()
            weather_data['ingested_at'] = datetime.datetime.now().isoformat()

            curr_time = datetime.datetime.now()
            object_name = f"weather-data/year={curr_time.strftime("%Y")}/month={curr_time.strftime("%m")}/day={curr_time.strftime("%d")}/weather-data-{curr_time.strftime("%H%M")}.json"

            s3_client = s3_client_initialize()
            s3_client.put_object(
                Bucket = 'weather-api-dump',
                Key = object_name,
                Body = json.dumps(weather_data),
                ContentType = 'application/json'
            )
            logger.info(f"Successfully uploaded the data to {object_name}")
        
        else:
            logger.error(f"Unsuccessful with error code: {r.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        raise

if __name__ == "__main__":
    harvest_weather_data()

