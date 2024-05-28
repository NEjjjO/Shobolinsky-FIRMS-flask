import pymongo
from pymongo import MongoClient
import ssl

# MongoDB connection setup
client = MongoClient("mongodb+srv://NEjjjO:fuckyou69@shoby0.bcrmqu3.mongodb.net/?retryWrites=true&w=majority", ssl_cert_reqs=ssl.CERT_NONE)
db = client['FIRMS-recent']
collection = db['NASA']

# Test insert
test_data = {
    "latitude": -16.80931,
    "longitude": 144.67908,
    "brightness": 344.67,
    "scan": 1.03,
    "track": 1.01,
    "acq_date": "2024-05-27T00:00:00.000+00:00",
    "acq_time": "00:03",
    "satellite": "T",
    "confidence": 93,
    "version": "6.1NRT",
    "bright_t31": 289.37,
    "frp": 47.66,
    "daynight": "D"
}

try:
    collection.insert_one(test_data)
    print("Data inserted successfully")
except Exception as e:
    print(f"An error occurred while inserting data: {e}")

# Test fetch
try:
    data = list(collection.find())
    print(f"Fetched {len(data)} records from the database")
except Exception as e:
    print(f"An error occurred while fetching data: {e}")
