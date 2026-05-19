import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

CHANNEL_HANDLES = [
    "SmoshPit",
    "TwoHotTakes",
    "RedditOnWiki",
    "TheJudgiesPodcast",
    "RufusReadit",
    "SirReddit",
    "comfortlevelpodcast",
    "Sarbyy",
    "RedditStorytime",
    "MrRedderYT",
    "KarmaStoriesPodcast",
    "MarkNarrations",
    "CharlotteDobre",
    "Markee",
    "OKOPShow",
    "dustythunder",
]

def get_channel_by_handle(handle):
    try:
        request = youtube.channels().list(
            part="snippet,statistics",
            forHandle=handle
        )
        response = request.execute()
        if not response["items"]:
            return {"Channel Name": handle, "Channel ID": "NOT FOUND",
                    "Subscriber Count": "N/A", "Country": "N/A", "Date Joined": "N/A"}
        item = response["items"][0]
        return {
            "Channel Name": item["snippet"]["title"],
            "Channel ID": item["id"],
            "Subscriber Count": item["statistics"].get("subscriberCount", "N/A"),
            "Country": item["snippet"].get("country", "N/A"),
            "Date Joined": item["snippet"]["publishedAt"][:10]
        }
    except Exception as e:
        return {"Channel Name": handle, "Channel ID": f"ERROR: {e}",
                "Subscriber Count": "N/A", "Country": "N/A", "Date Joined": "N/A"}

data = []
for handle in CHANNEL_HANDLES:
    print(f"Fetching: {handle}")
    data.append(get_channel_by_handle(handle))

df = pd.DataFrame(data)
df.to_csv("channels.csv", index=False)
print("\nDone! channels.csv has been created.")
print(df)