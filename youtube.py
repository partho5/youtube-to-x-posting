# youtube.py
import logging
import os
import requests
import re

from dotenv import load_dotenv

from youtube_channel_video_extractor import YouTubePlaylistExtractor

logger = logging.getLogger(__name__)

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY")

youtube_extractor = YouTubePlaylistExtractor(YOUTUBE_API_KEY)


def extract_transcript(video_url):
    """
    Extract transcript from YouTube video using Supadata API.
    API key is read from SUPADATA_API_KEY in .env.
    """
    logger.info(f"Extracting transcript from: {video_url}")
    if not SUPADATA_API_KEY:
        logger.error("SUPADATA_API_KEY not set in environment.")
        return None
    # Extract videoId from URL
    match = re.search(r"[?&]v=([\w-]+)", video_url)
    if not match:
        logger.error(f"Could not extract videoId from URL: {video_url}")
        return None
    video_id = match.group(1)
    url = f"https://api.supadata.ai/v1/youtube/transcript?videoId={video_id}"
    headers = {"x-api-key": SUPADATA_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        print(f"response data={data}")
        transcript = extract_transcript_from_supadata_response(data)
        if not transcript:
            logger.error(f"No transcript found in response for videoId {video_id}")
            return None
        return transcript
    except Exception as e:
        logger.error(f"Error fetching transcript for videoId {video_id}: {e}")
        return None


def extract_transcript_from_supadata_response(response_json):
    """
    Given a Supadata API response (parsed JSON), return the full transcript as a single string.
    Joins all 'text' fields from the 'content' list in order.
    """
    content = response_json.get('content', [])
    transcript = ' '.join([item.get('text', '') for item in content if 'text' in item])
    return transcript.strip()