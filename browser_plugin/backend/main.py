import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException, Request

import os
import math
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

import torch
from torch import nn
from transformers import BertTokenizer, BertModel, pipeline, AutoTokenizer, AutoModelForTokenClassification
from datetime import datetime

app = FastAPI()

load_dotenv()

# Load the NER pipeline
model_name = "dbmdz/bert-large-cased-finetuned-conll03-english"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

USER = os.environ.get("DB_USER")
USER_PASSWORD = os.environ.get("DB_USER_KEY")

MONGO_URI = (f"mongodb+srv://{USER}:{USER_PASSWORD}@cluster0.mkddwv8.mongodb.net"
             "/vrpDB?retryWrites=true&w=majority")

client = MongoClient(MONGO_URI)

db = client["tweetDB"]
tweet_collection = db["tweets"]

class BERTClassifier(nn.Module):
    def __init__(self, bert_model_name, num_classes, hidden_size1=64, hidden_size2=128, hidden_size3=256):
        super(BERTClassifier, self).__init__()
        self.bert = BertModel.from_pretrained(bert_model_name)
        self.dropout = nn.Dropout(0.1)

        self.linear1 = nn.Linear(self.bert.config.hidden_size, hidden_size1)
  
        self.fc = nn.Linear(hidden_size1, num_classes)

        self.relu = nn.ReLU()

        self.softmax = nn.Softmax(dim=1)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output

        x = self.dropout(pooled_output)
        x = self.linear1(x)
        x = self.relu(x)

        logits = self.fc(x)

        probs = self.softmax(logits)
        return probs

# Load the model
def load_model(path, bert_model_name, num_classes):
    device = torch.device("cpu")
    model = BERTClassifier(bert_model_name, num_classes).to(device)
    model.load_state_dict(torch.load(f"{path}/model.pth", map_location=device))
    return model


model_path = "saved_model"
bert_model_name = "bert-base-uncased"
num_classes = 9 
tokenizer = BertTokenizer.from_pretrained(model_path)
model = load_model(model_path, bert_model_name, num_classes)
model.eval()


class DataPayload(BaseModel):
    data: dict

class TextRequest(BaseModel):
    text: str
    city: str = None
    tweetLink: str
    request_type: str
    latitude: float = None
    longitude: float = None

possible_mentions = [
            "WaterProblem",
            "RoadProblem",
            "CleanlinessProblem",
            "Police",
            "BridgeProblem",
            "TrafficPolice",
            "PostOffice",
            "BusProblem",
            "Railway",
        ]

def extract_location_from_ner(tweet):
    entities = ner_pipeline(tweet)
    locations = [entity['word'] for entity in entities if entity['entity_group'] == 'LOC']
    if locations:
        return locations
    else:
        return []

def get_nearest_location_index(lat, lon, ambiguous_locations):
    """
    Finds the index of the nearest location from ambiguous_locations
    based on the user's current latitude and longitude.

    Parameters:
    - lat (float): User's current latitude.
    - lon (float): User's current longitude.
    - ambiguous_locations (dict): Dictionary where keys are indices
      and values are dictionaries containing 'lat' and 'lon' keys for each location.

    Returns:
    - int: Index of the nearest location.
    """

    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        r = 6371 
        return c * r

    nearest_index = None
    min_distance = float('inf')

    for index, location_info in ambiguous_locations.items():
        location_lat = location_info['lat']
        location_lon = location_info['lon']
        distance = haversine_distance(lat, lon, location_lat, location_lon)
        if distance < min_distance:
            min_distance = distance
            nearest_index = index

    return nearest_index

def coordinates_details(lat, lon):
      key = os.environ.get("GOOGLE_MAP_API")
      url = "https://maps.googleapis.com/maps/api/geocode/json?latlng="+str(lat)+","+str(lon)+"&key="+key
      headers = {"Content-Type": "application/json"}

      response = requests.get(url, headers=headers)
      response = response.json()

      area = ""
      for location in response["results"][0]["address_components"]:
        if "locality" in location["types"]:
          area = area[:-2]
          break
        area += location["long_name"]+", "

      payload = {
          "address_components": response["results"][0]["address_components"],
          "formatted_address": response["results"][0]["formatted_address"],
          "location_coordinates": response["results"][0]["geometry"]["location"],
          "area": area,
          "city": [location["long_name"] for location in response["results"][0]["address_components"] if "locality" in location["types"]][0],
          "country": [location["long_name"] for location in response["results"][0]["address_components"] if "country" in location["types"]][0],

      }
      return payload

def area_details(location, lat, lon):
      key = os.environ.get("GOOGLE_MAP_API")

      city = coordinates_details(lat, lon)["city"]

      location = location.replace(' ','+') + "+" + city

      url = "https://maps.googleapis.com/maps/api/geocode/json?address="+location+"&key="+key
      headers = {"Content-Type": "application/json"}

      response = requests.get(url, headers=headers)
      response = response.json()

      nearest_index = 0
      if len(response["results"]) > 1:
        ambigous_location = [result["geometry"]["location"] for result in response["results"]]
        ambigous_location = dict(enumerate(ambigous_location))
        nearest_index = get_nearest_location_index(lat, lon, ambigous_location)

      area = ""
      for location in response["results"][nearest_index]["address_components"]:
        if "locality" in location["types"]:
          area = area[:-2]
          break
        area += location["long_name"]+", "

      payload = {
          "address_components": response["results"][nearest_index]["address_components"],
          "formatted_address": response["results"][nearest_index]["formatted_address"],
          "location_coordinates": response["results"][nearest_index]["geometry"]["location"],
          "area": area,
          "city": [location["long_name"] for location in response["results"][nearest_index]["address_components"] if "locality" in location["types"]][0],
          "country": [location["long_name"] for location in response["results"][nearest_index]["address_components"] if "country" in location["types"]][0],
      }
      return payload

def get_location_details(tweet, lat, lon):
    locations = extract_location_from_ner(tweet)
    if len(locations) == 0:
      return coordinates_details(lat,lon)
    else:
      return area_details(locations[0], lat, lon)


@app.post("/predict")
async def predict(request: TextRequest):
    final_mentions = {
        "Mumbai": {
                "WaterProblem": "@mybmcHydEngg",
                "RoadProblem": "@mybmcRoads",
                "CleanlinessProblem": "@mybmcSWM",
                "Police": "@MumbaiPolice",
                "BridgeProblem": "@mybmcBridges",
                "TrafficPolice": "@MTPHereToHelp",
                "PostOffice": "@fpomumbai",
                "BusProblem": "@myBESTBus",
                "Railway": "@grpmumbai"
            },
        "New Delhi": {
                "WaterProblem": "@DJBOfficial",
                "RoadProblem": "@dtptraffic",
                "CleanlinessProblem": "@NorthDMC",
                "Police": "@DelhiPolice",
                "BridgeProblem": "@PWDDelhi",
                "TrafficPolice": "@dtptraffic",
                "PostOffice": "@IndiaPostOffice",
                "BusProblem": "@OfficialDTC",
                "Railway": "@RailMinIndia"
            },
        "Pune": {
                "WaterProblem": "@PMCPune",
                "RoadProblem": "@PMCPune",
                "CleanlinessProblem": "@PMCPune",
                "Police": "@PuneCityPolice",
                "BridgeProblem": "@PMCPune",
                "TrafficPolice": "@PuneCityTraffic",
                "PostOffice": "@IndiaPostOffice",
                "BusProblem": "@PMPMLPune",
                "Railway": "@drmpune"
            }
    }
    
    departments = {
            'WaterProblem': 'water',
            'CleanlinessProblem': 'cleanliness',
            'RoadProblem': 'road',
            'BridgeProblem': 'bridge',
            'Police': 'police',
            'TrafficPolice': 'traffic police',
            'Railway': 'railway',
            'BusProblem': 'best',
            'PostOffice': 'post office',
        }
    
    tweet = request.text
    city = request.city
    tweetLink = request.tweetLink
    print(f"City: {city}")
    print(f"Tweet Link: {tweetLink}")
    inputs = tokenizer(request.text, return_tensors="pt", truncation=True, padding=True)
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    with torch.no_grad():
        logits = model(input_ids, attention_mask)
        predictions = torch.nn.functional.softmax(logits, dim=-1)

    print("Tweet:", tweet)
    print("Predictions:", predictions)
    predicted_class = torch.argmax(predictions, dim=1).item()
    print("Predicted Class:", predicted_class)
    confidence = predictions[0][predicted_class].item()

    suggestion = ""
    if request.request_type == "suggest":
      locations = extract_location_from_ner(tweet)
      if len(locations) == 0:
        suggestion = "Please mention specific location information in the tweet."
      elif city == "":
        q = '%20'.join(locations)
        url = "https://api.geoapify.com/v1/geocode/search?text="+q+f"&format=json&apiKey={os.environ.get('GEOAPIFY_API')}"

        response = requests.get(url)
        response = response.json()
        city = response['results'][0]['city']
        if final_mentions[city][possible_mentions[predicted_class]] not in tweet:
           suggestion = "Mention the recommendation in the tweet. Recommending the mention based on location mentioned in the tweet."
        else:
           suggestion = "The tweet looks great, you can post it! Recommending the mention based on location mentioned in the tweet."
      elif city != "" and len(locations) == 0 and final_mentions[city][possible_mentions[predicted_class]] not in tweet:
        suggestion = "Mention the recommendation in the tweet."
      elif city != "" and len(locations) != 0 and final_mentions[city][possible_mentions[predicted_class]] not in tweet:
        q = '%20'.join(locations)
        url = "https://api.geoapify.com/v1/geocode/search?text="+q+f"&format=json&apiKey={os.environ.get('GEOAPIFY_API')}"

        response = requests.get(url)
        response = response.json()
        city = response['results'][0]['city']
        if final_mentions[city][possible_mentions[predicted_class]] not in tweet:
           suggestion = "Mention the recommendation in the tweet. Recommending the mention based on location mentioned in the tweet."
        else:
           suggestion = "The tweet looks great, you can post it! Recommending the mention based on location mentioned in the tweet."
      else:
        suggestion = "The tweet looks great, you can post it! Recommending the mention based on location mentioned in the tweet."

      return {"predicted_class": possible_mentions[predicted_class], "confidence": confidence, "suggestion": suggestion, "city": city}
    elif request.request_type == "post":
      suggestion = "The Authority has been notified!"
      if(city!=""):
        url = "https://api.geoapify.com/v1/geocode/search?text="+city+f"&format=json&apiKey={os.environ.get('GEOAPIFY_API')}"

        response = requests.get(url)
        response = response.json()
        latitude = response["results"][0]["lat"]
        longitude = response["results"][0]["lon"]
      else:
        latitude = request.latitude
        longitude = request.longitude
        
      payload = {
          "tweet": tweet,
          "predicted_class": possible_mentions[predicted_class],
          "confidence": confidence,
          "suggestion": suggestion,
          # "location_details": get_location_details(tweet, request.latitude,request.longitude)
      }
      # print(payload)
      result = tweet_collection.insert_one({
          "tweet": tweet,
          "category": departments[possible_mentions[predicted_class]],
          "time": str(datetime.now()),
          # "location": payload["location_details"]["formatted_address"],
          "city": city,
          "link": tweetLink,
          "confidence": confidence,
          # "detailedLocation": payload["location_details"]
      })
      print("Tweet Inserted", result.acknowledged)
      return payload
    

@app.post("/test")
def test_route(data_payload: DataPayload, request: Request):
    print("connection established")

    possible_mentions = {
        "Mumbai": {
                "WaterProblem": "@mybmcHydEngg",
                "RoadProblem": "@mybmcRoads",
                "CleanlinessProblem": "@mybmcSWM",
                "Police": "@MumbaiPolice",
                "BridgeProblem": "@mybmcBridges",
                "TrafficPolice": "@MTPHereToHelp",
                "PostOffice": "@fpomumbai",
                "BusProblem": "@myBESTBus",
                "Railway": "@grpmumbai"
            },
        "New Delhi": {
                "WaterProblem": "@DJBOfficial",
                "RoadProblem": "@dtptraffic",
                "CleanlinessProblem": "@NorthDMC",
                "Police": "@DelhiPolice",
                "BridgeProblem": "@PWDDelhi",
                "TrafficPolice": "@dtptraffic",
                "PostOffice": "@IndiaPostOffice",
                "BusProblem": "@OfficialDTC",
                "Railway": "@RailMinIndia"
            },
        "Pune": {
                "WaterProblem": "@PMCPune",
                "RoadProblem": "@PMCPune",
                "CleanlinessProblem": "@PMCPune",
                "Police": "@PuneCityPolice",
                "BridgeProblem": "@PMCPune",
                "TrafficPolice": "@PuneCityTraffic",
                "PostOffice": "@IndiaPostOffice",
                "BusProblem": "@PMPMLPune",
                "Railway": "@drmpune"
            }
    }
    
    try:
        coordinates = data_payload.data.get('coordinates')
        tweet = data_payload.data.get('tweet')
        request_type = data_payload.data.get('request_type')
        tweetLink = data_payload.data.get('tweet_link')

        print("Data Payload", data_payload)

        if coordinates:
            latitude = coordinates.get('latitude')
            longitude = coordinates.get('longitude')

            #implementing location based recommendation
            city = ""
            if(latitude == "" or longitude == ""):
              latitude = "0"
              longitude = "0"
              print("Coordinates not found")
              
            else:
              url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={latitude}&lon={longitude}&limit=5&appid={os.environ.get("OPEN_WEATHER_API")}"
              
              response = requests.get(url)
              response = response.json()
              city = response[0]["name"]

            url = "http://127.0.0.1:8000/predict"
            headers = {"Content-Type": "application/json"}
            data = {"text": tweet, "latitude": latitude, "longitude": longitude, "request_type": request_type, "city": city, "tweetLink": tweetLink}

            print("Data to be sent", data)
            response = requests.post(url, headers=headers, json=data)
            response = response.json()
            recommendation = response['predicted_class']
            suggestion = response['suggestion']
            city = response['city']
            print(f'"{tweet}" Coordinates received: Latitude {latitude}, Longitude {longitude}    suggestion {suggestion}')
            if city == "":
              return {'message': "", "suggestion": "We cannot recommend as no location information mentioned in the tweet."}
            return {'message': "Mention Problem to: " + possible_mentions[city][recommendation], "suggestion": suggestion}
        else:
            raise HTTPException(status_code=400, detail='Coordinates not found in data payload')
    except Exception as e:
        print(e)
        return {'error': str(e)}


    return {'message': 'Data received successfully'}



if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, log_level="info", reload=True)
