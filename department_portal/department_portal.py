import time
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime

from config.db import client

db = client["tweetDB"]
tweet_collection = db["tweets"]

def fetch_tweets(dept):
    print("Fetching tweets for:", dept)
    tweets = list(tweet_collection.find({"category": dept.lower()}))
    print("Tweets count:", len(tweets))
    return tweets

department_colors = {
    'Water': '#ADD8E6', 
    'Road': '#FFD700',   
    'Cleanliness': '#ADD8E6', 
    'Police': '#FF6347', 
    'Traffic Police': '#FF4500', 
    'Bridge': '#FFD700', 
    'Post Office': '#20B2AA',
    'Railway': '#FFA07A', 
    'BEST': '#FFA07A',
}

st.title('Tweets related to:')

current_location = streamlit_geolocation()

departments = {
    'Water': '@mybmcHydEngg',
    'Cleanliness': '@mybmcSWM',
    'Road': '@mybmcRoads',
    'Bridge': '@mybmcBridges',
    'Police': '@MumbaiPolice',
    'Traffic Police': '@MTPHereToHelp',
    'Railway': '@grpmumbai',
    'BEST': '@myBESTBus',
    'Post Office': '@fpomumbai',
}

tabs = st.tabs(list(departments.keys()))

if current_location['latitude'] is None or current_location['longitude'] is None:
    st.warning("Location access is required to show tweets.")
else:
    for i, (dept, query) in enumerate(departments.items()):
        with tabs[i]:
            st.header(dept)
            tweets = fetch_tweets(dept)
            if tweets:
                for tweet in tweets:
                    username = tweet.get("username", "")
                    action_text = tweet.get("tweet", "")
                    tweet_datetime = datetime.strptime(tweet["time"], '%Y-%m-%d %H:%M:%S.%f')
                    tweet_date = tweet_datetime.strftime('%Y-%m-%d')
                    tweet_time = tweet_datetime.strftime('%H:%M')
                    tweet_location = tweet.get("location", "")
                    tweet_link = tweet.get("link", "")

                    color = department_colors[dept]
                    st.markdown(
                        f"""
                        <div style="background-color: {color}; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <p style="font-size: 20px; font-weight: bold; color: #686D76;">@{username}</p>
                                <p style="font-size: 15px; color: #F5F7F8;">{tweet_date} {tweet_time}</p>
                            </div>
                            <p style="font-size: 20px; font-weight: bold; color: #373A40; margin-top: 8px;">{action_text}</p>
                            <hr style="border-top: 1px solid #F5F7F8; margin: 10px 0;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <p style="font-size: 16px; color: #FBF9F1; font-weight: bold;">Location: {tweet_location}</p>
                                <p><a href="{tweet_link}" target="_blank" style="font-size: 15px; color: #373A40;">Tweet <span style="font-size: 12px;">&rarr;</span></a></p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.write("No tweets found.")

# Add a delay and refresh the page
time.sleep(10)
st.experimental_rerun()

# Run the app with: streamlit run department_portal.py
