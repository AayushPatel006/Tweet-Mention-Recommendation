import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

USER = os.environ.get("DB_USER")
USER_PASSWORD = os.environ.get("DB_USER_KEY")

MONGO_URI = (f"mongodb+srv://{USER}:{USER_PASSWORD}@cluster0.mkddwv8.mongodb.net"
             "/vrpDB?retryWrites=true&w=majority")

client = MongoClient(MONGO_URI)
