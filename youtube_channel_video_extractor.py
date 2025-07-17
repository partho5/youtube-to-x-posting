# youtube_channel_video_extractor.py
import requests
import time
from typing import List, Dict, Optional


class YouTubePlaylistExtractor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def get_playlist_videos(self, playlist_id: str, max_results: int = 50) -> List[str]:
        """
        Extract all video URLs from a single playlist

        Args:
            playlist_id: YouTube playlist ID
            max_results: Maximum results per API call (max 50)

        Returns:
            List of video URLs
        """
        video_urls = []
        next_page_token = None

        while True:
            url = f"{self.base_url}/playlistItems"
            params = {
                "part": "snippet",
                "maxResults": min(max_results, 50),
                "playlistId": playlist_id,
                "key": self.api_key
            }

            if next_page_token:
                params["pageToken"] = next_page_token

            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Extract video URLs from current page
                for item in data.get('items', []):
                    video_id = item['snippet']['resourceId']['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    video_urls.append(video_url)

                # Check if there are more pages
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break

                # Add small delay to respect API rate limits
                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching playlist {playlist_id}: {e}")
                break
            except KeyError as e:
                print(f"Unexpected response format for playlist {playlist_id}: {e}")
                break

        return video_urls

    def get_channel_playlists(self, channel_id: str) -> List[Dict[str, str]]:
        """
        Get all playlists from a channel

        Args:
            channel_id: YouTube channel ID

        Returns:
            List of dictionaries containing playlist info (id, title)
        """
        playlists = []
        next_page_token = None

        while True:
            url = f"{self.base_url}/playlists"
            params = {
                "part": "snippet",
                "channelId": channel_id,
                "maxResults": 50,
                "key": self.api_key
            }

            if next_page_token:
                params["pageToken"] = next_page_token

            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                for item in data.get('items', []):
                    playlist_info = {
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'video_count': item['snippet'].get('videoCount', 0)
                    }
                    playlists.append(playlist_info)

                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break

                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching playlists for channel {channel_id}: {e}")
                break

        return playlists

    def get_all_videos_from_channel_playlists(self, channel_id: str) -> Dict[str, List[str]]:
        """
        Get all video URLs from all playlists in a channel

        Args:
            channel_id: YouTube channel ID

        Returns:
            Dictionary with playlist titles as keys and lists of video URLs as values
        """
        all_videos = {}

        # Get all playlists from the channel
        playlists = self.get_channel_playlists(channel_id)

        if not playlists:
            print(f"No playlists found for channel {channel_id}")
            return all_videos

        print(f"Found {len(playlists)} playlists in channel")

        # Get videos from each playlist
        for playlist in playlists:
            playlist_id = playlist['id']
            playlist_title = playlist['title']

            print(f"Processing playlist: {playlist_title}")

            videos = self.get_playlist_videos(playlist_id)
            all_videos[playlist_title] = videos

            print(f"Found {len(videos)} videos in '{playlist_title}'")

            # Add delay between playlists to respect rate limits
            time.sleep(0.2)

        return all_videos

    def get_channel_id_from_url(self, channel_url: str) -> Optional[str]:
        """
        Extract channel ID from various YouTube channel URL formats

        Args:
            channel_url: YouTube channel URL (e.g., https://www.youtube.com/@username)

        Returns:
            Channel ID or None if not found
        """
        import re

        # Handle different URL formats
        if '@' in channel_url:
            # Format: https://www.youtube.com/@username
            username = channel_url.split('@')[-1].strip('/')
            return self.get_channel_id_from_username(username)
        elif '/channel/' in channel_url:
            # Format: https://www.youtube.com/channel/UCxxxxx
            return channel_url.split('/channel/')[-1].split('/')[0]
        elif '/c/' in channel_url:
            # Format: https://www.youtube.com/c/channelname
            custom_name = channel_url.split('/c/')[-1].split('/')[0]
            return self.get_channel_id_from_custom_name(custom_name)
        elif '/user/' in channel_url:
            # Format: https://www.youtube.com/user/username
            username = channel_url.split('/user/')[-1].split('/')[0]
            return self.get_channel_id_from_username(username)
        else:
            print(f"Unsupported URL format: {channel_url}")
            return None

    def get_channel_id_from_username(self, username: str) -> Optional[str]:
        """Get channel ID from @username handle"""
        url = f"{self.base_url}/channels"
        params = {
            "part": "id",
            "forHandle": username,
            "key": self.api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('items'):
                return data['items'][0]['id']
            else:
                print(f"Channel not found for username: {username}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching channel ID for username {username}: {e}")
            return None

    def get_channel_id_from_custom_name(self, custom_name: str) -> Optional[str]:
        """Get channel ID from custom channel name"""
        url = f"{self.base_url}/channels"
        params = {
            "part": "id",
            "forUsername": custom_name,
            "key": self.api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('items'):
                return data['items'][0]['id']
            else:
                print(f"Channel not found for custom name: {custom_name}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching channel ID for custom name {custom_name}: {e}")
            return None

    def get_all_videos_from_channel(self, channel_id: str) -> List[str]:
        """
        Get all video URLs from a channel's uploads playlist

        Args:
            channel_id: YouTube channel ID

        Returns:
            List of all video URLs from the channel
        """
        # Get channel details to find uploads playlist
        url = f"{self.base_url}/channels"
        params = {
            "part": "contentDetails",
            "id": channel_id,
            "key": self.api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get('items'):
                print(f"Channel not found: {channel_id}")
                return []

            # Get uploads playlist ID
            uploads_playlist_id = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # Get all videos from uploads playlist
            print(f"Getting all videos from uploads playlist: {uploads_playlist_id}")
            return self.get_playlist_videos(uploads_playlist_id)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching channel details for {channel_id}: {e}")
            return []
        except KeyError as e:
            print(f"Unexpected response format for channel {channel_id}: {e}")
            return []

    def get_all_video_URLs(self, channel_url: str) -> List[str]:
        """
        Get all video URLs from a YouTube channel URL

        Args:
            channel_url: YouTube channel URL (e.g., https://www.youtube.com/@CaseyZander)

        Returns:
            List of all video URLs from the channel
        """
        print(f"Processing channel URL: {channel_url}")

        # Extract channel ID from URL
        channel_id = self.get_channel_id_from_url(channel_url)

        if not channel_id:
            print("Could not extract channel ID from URL")
            return []

        print(f"Found channel ID: {channel_id}")

        # Get all videos from the channel
        videos = self.get_all_videos_from_channel(channel_id)

        print(f"Found {len(videos)} total videos in channel")

        return videos

    def save_urls_to_file(self, urls: List[str], filename: str):
        """Save video URLs to a text file"""
        with open(filename, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
        print(f"Saved {len(urls)} URLs to {filename}")


# Example usage
def main():
    # Replace with your YouTube Data API key
    API_KEY = "AIzaSyBjWLMdNgs0jKEr_Gg49Dq9hm1dmhsfRfQ"
    PLAYLIST_ID = "PLxJiu4hQthmNwBX0l_LEn67S4RVvIPV5X" # one playlist for example
    CHANNEL_URL = "https://www.youtube.com/@CaseyZander" # channel id UC0fDV9ojOuKTrntPRlgKkcQ for @CaseyZander


    # Initialize the extractor
    extractor = YouTubePlaylistExtractor(API_KEY)

    channel_id = extractor.get_channel_id_from_url(CHANNEL_URL)

    # Example 1: Get all videos from a channel URL (NEW FUNCTION)
    print("=== Get All Videos from Channel URL ===")
    channel_url = "https://www.youtube.com/@CaseyZander"
    all_videos = extractor.get_all_video_URLs(channel_url)

    print(f"Found {len(all_videos)} total videos:")
    for i, url in enumerate(all_videos[:10], 1):  # Show first 10 URLs
        print(f"{i}. {url}")

    if len(all_videos) > 10:
        print(f"... and {len(all_videos) - 10} more videos")

    # Save to file
    extractor.save_urls_to_file(all_videos, "channel_all_videos.txt")

    print("\n" + "=" * 50 + "\n")

    # Example 2: Get videos from a single playlist
    print("=== Single Playlist Example ===")

    video_urls = extractor.get_playlist_videos(PLAYLIST_ID)

    print(f"Found {len(video_urls)} videos in playlist:")
    for i, url in enumerate(video_urls[:5], 1):  # Show first 5 URLs
        print(f"{i}. {url}")

    if len(video_urls) > 5:
        print(f"... and {len(video_urls) - 5} more videos")

    # Save to file
    extractor.save_urls_to_file(video_urls, "playlist_videos.txt")

    print("\n" + "=" * 50 + "\n")

    # Example 3: Get videos from all playlists in a channel
    print("=== All Channel Playlists Example ===")

    all_playlist_videos = extractor.get_all_videos_from_channel_playlists(channel_id)

    # Display results
    total_videos = 0
    for playlist_title, urls in all_playlist_videos.items():
        print(f"\nPlaylist: {playlist_title}")
        print(f"Videos: {len(urls)}")
        total_videos += len(urls)

        # Show first few URLs from each playlist
        for i, url in enumerate(urls[:3], 1):
            print(f"  {i}. {url}")

        if len(urls) > 3:
            print(f"  ... and {len(urls) - 3} more videos")

    print(f"\nTotal videos found: {total_videos}")

    # Save all URLs to a single file
    all_urls = []
    for urls in all_playlist_videos.values():
        all_urls.extend(urls)

    extractor.save_urls_to_file(all_urls, "all_channel_playlists_videos.txt")


if __name__ == "__main__":
    main()