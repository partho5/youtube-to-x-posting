# x_handler.py
import os
import logging
import tweepy
import time

logger = logging.getLogger(__name__)

X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")


def post_tweet(text, media_path=None):
    """
    Post a tweet to X (Twitter) using Tweepy (v1.1 for media, v2 for text-only).
    Handles rate limits and prints all possible error reasons clearly.
    Returns True if successful, False otherwise.
    """
    logger.info(f"Posting tweet: {text[:50]}...")
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
        logger.error("Missing X (Twitter) API credentials in environment variables.")
        print("Missing X (Twitter) API credentials in environment variables.")
        return False

    try:
        # Auth for v1.1 (media upload)
        auth = tweepy.OAuth1UserHandler(
            X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
        )
        api_v1 = tweepy.API(auth, wait_on_rate_limit=True)

        # Auth for v2 (tweet posting)
        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )

        media_ids = []
        if media_path:
            try:
                media = api_v1.media_upload(media_path)
                media_ids.append(media.media_id_string)
                logger.info(f"Uploaded media: {media_path}")
            except tweepy.TweepyException as e:
                logger.error(f"Media upload failed: {e}")
                print(f"Media upload failed: {e}")
                return False

        # Post tweet
        try:
            if media_ids:
                response = client.create_tweet(text=text, media_ids=media_ids)
            else:
                response = client.create_tweet(text=text)
        except tweepy.TooManyRequests as e:
            logger.error(f"Rate limit exceeded: {e}")
            print("Rate limit exceeded. Please wait and try again.")
            return False
        except tweepy.Unauthorized as e:
            logger.error(f"Authentication failed: {e}")
            print("Authentication failed. Check your X API credentials.")
            return False
        except tweepy.Forbidden as e:
            logger.error(f"Forbidden: {e}")
            print(f"Forbidden: {e}")
            return False
        except tweepy.BadRequest as e:
            logger.error(f"Bad request: {e}")
            print(f"Bad request: {e}")
            return False
        except tweepy.TweepyException as e:
            logger.error(f"Tweepy error: {e}")
            print(f"Tweepy error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unknown error posting tweet: {e}")
            print(f"Unknown error posting tweet: {e}")
            return False

        # Success check
        if hasattr(response, 'data') and response.data and 'id' in response.data:
            logger.info(f"Successfully posted tweet: {response.data['id']}")
            print(f"Successfully posted tweet: {response.data['id']}")
            return True
        else:
            logger.error("Failed to post tweet - no response data")
            print("Failed to post tweet - no response data")
            return False

    except tweepy.TooManyRequests as e:
        logger.error(f"Rate limit exceeded: {e}")
        print("Rate limit exceeded. Please wait and try again.")
        return False
    except tweepy.Unauthorized as e:
        logger.error(f"Authentication failed: {e}")
        print("Authentication failed. Check your X API credentials.")
        return False
    except tweepy.Forbidden as e:
        logger.error(f"Forbidden: {e}")
        print(f"Forbidden: {e}")
        return False
    except tweepy.BadRequest as e:
        logger.error(f"Bad request: {e}")
        print(f"Bad request: {e}")
        return False
    except tweepy.TweepyException as e:
        logger.error(f"Tweepy error: {e}")
        print(f"Tweepy error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unknown error posting tweet: {e}")
        print(f"Unknown error posting tweet: {e}")
        return False