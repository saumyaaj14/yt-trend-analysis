import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
import time

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("API key not found! Check your .env file.")

youtube = build("youtube", "v3", developerKey=API_KEY)

channels_df = pd.read_csv("channels.csv")

def is_smosh_reddit_video(title):
    return title.strip().endswith("| Reading Reddit Stories")

def get_uploads_playlist_id(channel_id):
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()
    if not response["items"]:
        return None
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_videos_from_playlist(playlist_id, channel_name):
    videos = []
    next_page_token = None
    is_smosh = channel_name.lower() == "smosh pit"

    while True:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        video_ids = [item["contentDetails"]["videoId"] for item in response["items"]]

        stats_request = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids)
        )
        stats_response = stats_request.execute()

        for item in stats_response["items"]:
            title = item["snippet"]["title"]

            # For Smosh only keep videos ending with | Reading Reddit Stories
            if is_smosh and not is_smosh_reddit_video(title):
                continue

            videos.append({
                "Channel Name": channel_name,
                "Video ID": item["id"],
                "Title": title,
                "Publish Date": item["snippet"]["publishedAt"][:10],
                "View Count": item["statistics"].get("viewCount", 0),
                "Like Count": item["statistics"].get("likeCount", 0),
                "Comment Count": item["statistics"].get("commentCount", 0),
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

        time.sleep(0.5)

    return videos

all_videos = []

for _, row in channels_df.iterrows():
    channel_id = row["Channel ID"]
    channel_name = row["Channel Name"]

    if "ERROR" in str(channel_id) or "NOT FOUND" in str(channel_id):
        print(f"Skipping {channel_name} — no valid channel ID")
        continue

    print(f"Fetching videos for: {channel_name}")
    playlist_id = get_uploads_playlist_id(channel_id)

    if not playlist_id:
        print(f"  Could not find uploads playlist for {channel_name}")
        continue

    videos = get_videos_from_playlist(playlist_id, channel_name)
    print(f"  Found {len(videos)} videos")
    all_videos.extend(videos)

df = pd.DataFrame(all_videos)
df.to_csv("videos.csv", index=False)
print(f"\nDone! videos.csv created with {len(all_videos)} total videos.")