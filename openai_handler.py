# openai_handler.py

import os
import logging
import re

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

load_dotenv()

# Load config from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.7))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", 280))  # 280 chars for tweet

# Prompt template for tweet generation
TWEET_PROMPT_TEMPLATE = (
    "You are a social media expert. Given the following YouTube video transcript, "
    "write a concise, engaging tweet (max 270 characters) summarizing the main idea. "
    "Use clear language, add relevant hashtags if appropriate, and make it suitable for X (Twitter). Strictly "
    "forbidden to use emoji and hashtag.\n\n "
    "Transcript:\n{transcript}\n\nTweet:"
)

# Create OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


def get_chat_completion(messages, model, temperature, max_tokens):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip(), getattr(response, 'usage', None)
    except Exception as e:
        error_type = type(e).__name__
        if "AuthenticationError" in error_type:
            raise RuntimeError("Invalid API key")
        elif "RateLimitError" in error_type:
            raise RuntimeError("Rate limit exceeded")
        elif "APIError" in error_type:
            raise RuntimeError(f"OpenAI API Error: {e}")
        else:
            raise RuntimeError(f"Unexpected error: {e}")


def clean_response(text):
    # Remove code blocks, markdown, and excess whitespace
    text = re.sub(r"```(?:\w+)?\n(.*?)```", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return text.strip()


def generate_tweet(transcript):
    """
    Generate a tweet from a YouTube video transcript using OpenAI.
    Uses a prompt template for scalability and consistency.
    """
    logger.info(f"Generating tweet from transcript (length: {len(transcript)})")
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set in environment.")
        return None
    prompt = TWEET_PROMPT_TEMPLATE.format(transcript=transcript)
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
    try:
        raw_response, _ = get_chat_completion(
            messages=messages,
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        )
        tweet = clean_response(raw_response)
        # Ensure tweet is within 280 characters
        if len(tweet) > 280:
            tweet = tweet[:275] + "..."
        return tweet
    except RuntimeError as e:
        logger.error(f"Error generating tweet: {e}")
        return f"[Error] {str(e)}"
