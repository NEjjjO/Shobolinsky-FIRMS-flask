from pymongo import MongoClient, server_api, errors

# Connection URI
uri = "mongodb+srv://NEjjjO:fuckyou69@shoby0.bcrmqu3.mongodb.net/?retryWrites=true&w=majority&appName=Shoby0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=server_api.ServerApi('1'), tls=True, tlsAllowInvalidCertificates=True)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except errors.ConnectionFailure as e:
    print(f"Connection Failure: {e}")
except errors.ConfigurationError as e:
    print(f"Configuration Error: {e}")
except errors.ServerSelectionTimeoutError as e:
    print(f"Server Selection Timeout Error: {e}")
except Exception as e:
    print(f"General Error: {e}")