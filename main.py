# main.py
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from dotenv import load_dotenv
import logging

from database import init_db, get_all_channels, add_video, get_videos_by_status, update_video_transcript, \
    update_video_status, get_video_info_by_url, add_channels_from_list, add_channel, get_video_urls_by_channel_id
from youtube import extract_transcript
from openai_handler import generate_tweet
from x_handler import post_tweet
from youtube_channel_video_extractor import YouTubePlaylistExtractor

load_dotenv()

# Config
SYSTEM_AUTH_TOKEN = os.getenv("SYSTEM_AUTH_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
security = HTTPBearer()

youtube_extractor = YouTubePlaylistExtractor(YOUTUBE_API_KEY)


# Auth
def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != SYSTEM_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials


# FastAPI app
app = FastAPI(title="YouTube-to-X Auto-Posting")


@app.on_event("startup")
async def startup():
    init_db()


"""
fetches channel video URLs and saves to database
"""


@app.post("/fetch-channel-videos")
async def add_channel_videos(credentials=Depends(authenticate)):
    channel_list = [
        # {"x_handle": "relationship", "channel_url": "https://www.youtube.com/@CaseyZander"},
        # {"x_handle": "ai_videos", "channel_url": "https://www.youtube.com/@biz-tech"},
        {"x_handle": "idea", "channel_url": "https://www.youtube.com/@davejeltema3"},
    ]

    total_videos = 0
    for channel_data in channel_list:
        try:
            # Add channel to DB
            channel_id = add_channel(channel_data["x_handle"], channel_data["channel_url"])

            # Get all video URLs from channel using YouTubePlaylistExtractor
            video_urls = youtube_extractor.get_all_video_URLs(channel_data["channel_url"])

            # Save each video URL to DB
            for video_url in video_urls:
                if not get_video_info_by_url(video_url):
                    add_video(channel_id, video_url)
                    total_videos += 1

        except Exception as e:
            logger.error(f"Error processing channel {channel_data['x_handle']}: {e}")
            continue

    return {"status": "success", "channels_processed": len(channel_list), "videos_added": total_videos}


@app.post("/scan-new-channel-videos")
async def scan_new_videos(credentials=Depends(authenticate)):
    """
    Scan all channels in the database, fetch live video URLs from YouTube, compare with existing URLs in the DB,
    add any new videos to the videos table, and log the process. Returns the number of new videos added.
    """
    channels = get_all_channels()
    new_videos = 0

    for channel in channels:
        channel_id = channel[0]
        channel_url = channel[2]

        # print(f"\n--- Processing channel: {channel}")
        # print(f"channel_id={channel_id}")
        # Get live video URLs from YouTube
        channel_video_urls = youtube_extractor.get_all_video_URLs(channel_url)
        # print(f"Live video URLs from YouTube for channel_id={channel_id}: {channel_video_urls}")
        # Get existing video URLs from DB
        db_video_urls = set(get_video_urls_by_channel_id(channel_id))
        # print(f"Existing video URLs in DB for channel_id={channel_id}: {db_video_urls}")
        # Find new video URLs
        new_urls = [url for url in channel_video_urls if url not in db_video_urls]
        # print(f"New video URLs to add for channel_id={channel_id}: {new_urls}")
        for video_url in new_urls:
            # print(f"  Adding new video: channel_id={channel_id}, video_url={video_url}")
            add_video(channel_id, video_url)
            new_videos += 1

    # print(f"Total new videos added: {new_videos}")
    return {"status": "success", "new_videos": new_videos}


@app.post("/generate-tweets")
async def generate_tweets(credentials=Depends(authenticate)):
    """
    Generate a tweet for the (first) pending video only. If first row has status pending, it won't generate another
    tweet, until this is one gets published
    """
    videos = get_videos_by_status('pending')
    if not videos:
        return {"status": "success", "processed": 0, "message": "No pending videos found."}

    # Find the first pending video (lowest id)
    first_video = min(videos, key=lambda v: v['id'])
    processed = 0
    if not first_video['transcript']:
        transcript = extract_transcript(first_video['video_url'])
        if transcript:
            tweet_text = generate_tweet(transcript)
            update_video_transcript(first_video['id'], transcript, tweet_text)
            processed = 1

    return {"status": "success", "processed": processed, "video_id": first_video['id']}


@app.post("/post-to-x")
async def post_to_x(credentials=Depends(authenticate)):
    videos = get_videos_by_status('pending')
    posted = 0

    for video in videos:
        if video['tweet_text']:
            success = post_tweet(video['tweet_text'])
            if success:
                update_video_status(video['id'], 'published')
                posted += 1
            else:
                update_video_status(video['id'], 'error')

    return {"status": "success", "posted": posted}


@app.get("/status")
async def get_status(credentials=Depends(authenticate)):
    return {"status": "healthy", "message": "Service running"}


@app.get("/")
async def get_home():
    return {"app": "Youtube to X posting", "status": "OK", "message": "Youtube to X service is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8006, reload=False)
