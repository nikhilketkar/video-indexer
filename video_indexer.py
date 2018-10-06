from pymongo import MongoClient

def test_connection():
    client = MongoClient('mongodb://root:ACDRCbAEh8PJ@35.197.46.213:27017/')
    return client.server_info()




