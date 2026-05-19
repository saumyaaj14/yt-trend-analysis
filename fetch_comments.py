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

# Load videos
df = pd.read_csv("videos.csv")
df["Publish Date"] = pd.to_datetime(df["Publish Date"])
df["View Count"] = pd.to_numeric(df["View Count"], errors="coerce")
df["Quarter"] = df["Publish Date"].dt.to_period("Q")

# Sample — top 5 most viewed videos per channel per quarter
sampled = (
    df.sort_values("View Count", ascending=False)
    .groupby(["Channel Name", "Quarter"])
    .head(5)
    .reset_index(drop=True)
)

print(f"Total sampled videos: {len(sampled)}")

def fetch_comments(video_id, max_comments=100):
    comments = []
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            order="relevance",
            textFormat="plainText"
        )
        response = request.execute()

        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "Video ID": video_id,
                "Comment": comment["textDisplay"],
                "Likes": comment["likeCount"],
                "Published At": comment["publishedAt"][:10]
            })

    except Exception as e:
        print(f"  Error fetching comments for {video_id}: {e}")

    return comments

all_comments = []
total = len(sampled)

for i, row in sampled.iterrows():
    video_id = row["Video ID"]
    channel = row["Channel Name"]
    quarter = str(row["Quarter"])

    print(f"[{i+1}/{total}] Fetching comments: {channel} — {quarter} — {video_id}")
    comments = fetch_comments(video_id)

    # Tag each comment with channel and quarter for later analysis
    for c in comments:
        c["Channel Name"] = channel
        c["Quarter"] = quarter

    all_comments.extend(comments)
    time.sleep(0.3)

comments_df = pd.DataFrame(all_comments)
comments_df.to_csv("comments.csv", index=False)
print(f"\nDone! comments.csv created with {len(all_comments)} total comments.")