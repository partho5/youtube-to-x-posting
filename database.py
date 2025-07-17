# database.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DATABASE_PATH", "youtube_to_x.db")


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY,
                x_handle TEXT UNIQUE,
                channel_url TEXT UNIQUE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                video_url TEXT UNIQUE,
                title TEXT,
                transcript TEXT,
                tweet_text TEXT,
                tweet_media TEXT,
                posted_status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_channel(x_handle, channel_url):
    """Add channel and return channel ID"""
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO channels (x_handle, channel_url) VALUES (?, ?)",
            (x_handle, channel_url)
        )
        return conn.execute(
            "SELECT id FROM channels WHERE channel_url = ?", (channel_url,)
        ).fetchone()[0]


def add_channels_from_list(channel_list):
    """Add hardcoded channels to DB"""
    # placeholder


def get_all_channels():
    with get_db() as conn:
        return conn.execute("SELECT * FROM channels").fetchall()


def add_video(channel_id, video_url, title=None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO videos (channel_id, video_url, title) VALUES (?, ?, ?)",
            (channel_id, video_url, title)
        )


def get_videos_by_status(status):
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM videos WHERE posted_status = ?", (status,)
        ).fetchall()


def update_video_transcript(video_id, transcript, tweet_text):
    with get_db() as conn:
        conn.execute(
            "UPDATE videos SET transcript = ?, tweet_text = ? WHERE id = ?",
            (transcript, tweet_text, video_id)
        )


def update_video_status(video_id, status):
    with get_db() as conn:
        conn.execute(
            "UPDATE videos SET posted_status = ? WHERE id = ?",
            (status, video_id)
        )


def get_video_info_by_url(video_url):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM videos WHERE video_url = ?", (video_url,)
        ).fetchone()


def get_video_urls_by_channel_id(channel_id):
    """Return a list of video URLs for the given channel_id."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT video_url FROM videos WHERE channel_id = ?",
            (channel_id,)
        ).fetchall()
        return [row[0] for row in rows]
