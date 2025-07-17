# YouTube-to-X Auto-Posting App

A robust Python application that automatically pulls new videos from YouTube channels, extracts transcripts using Supadata, generates tweets with OpenAI, and posts to X (Twitter).

## Features

- **YouTube Integration**: Automatically scan channels for new videos
- **Transcript Extraction**: Extract video transcripts using Supadata API
- **AI-Powered Tweet Generation**: Convert transcripts to engaging tweets using OpenAI
- **X (Twitter) Posting**: Automatically post generated tweets
- **SQLite Database**: Local database for tracking videos and posts
- **FastAPI REST API**: Secure endpoints for manual triggering and monitoring
- **Bearer Token Authentication**: Secure API access
- **Clear Workflow Instructions**: See below for endpoint usage and workflow, inspired by `instructions.txt` for clarity

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd Youtube_to_X_posting

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your API keys
nano .env
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `SUPADATA_API_KEY`: Your Supadata YouTube transcript API key
- `YOUTUBE_API_KEY`: Your YouTube Data API key (for channel/playlist extraction)
- `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`: X (Twitter) API credentials
- `X_BEARER_TOKEN`: X Bearer token
- `SYSTEM_AUTH_TOKEN`: Your secure authentication token for API access

### 3. Run the Application

```bash
# Start the FastAPI server
uvicorn main:app --host 127.0.0.1 --port 8006

# Server will be available at http://localhost:8006
```

## API Workflow & Endpoint Usage

The following workflow is recommended for using the API endpoints. This is based on the logic and intent described in `instructions.txt` and matches the actual code behavior:

### 1. `POST /fetch-channel-videos`
**Purpose:** Fetches videos from a hardcoded list of YouTube channel URLs and saves all video URLs into the `videos` table, regardless of whether they already exist. Use this to initially populate the database.

**Example response:**
```json
{
  "status": "success",
  "channels_processed": 2,
  "videos_added": 4395
}
```

### 2. `POST /scan-new-channel-videos`
**Purpose:** Checks the same YouTube channels and inserts only new videos (i.e., not already in the `videos` table). Use this to update the database regularly without duplicating entries.

**Example response:**
```json
{
  "status": "success",
  "new_videos": 9
}
```

### 3. `POST /generate-tweets`
**Purpose:** Generates a tweet from the transcript of the oldest (first) video in the `videos` table with status `pending`. Only one video is processed per call. If the first row is already pending and has a transcript, it won’t generate another tweet until the current pending video is published.

**Example response:**
```json
{
  "status": "success",
  "processed": 1,
  "video_id": 42
}
```

### 4. `POST /post-to-x`
**Purpose:** Posts the first video that has status `pending` and a non-empty `tweet_text` field. Skips any videos with status `published` or with an empty `tweet_text`. If no such video is found, nothing is posted.

**Example response:**
```json
{
  "status": "success",
  "posted": 2
}
```

### 5. `GET /status`
Returns application health status and basic statistics.

**Example response:**
```json
{
  "status": "healthy",
  "message": "Service running"
}
```

### `/`
Returns a simple status message for the root endpoint.

## Database Schema

### `channels` Table
- `id`: Primary key
- `x_handle`: X (Twitter) handle (unique)
- `channel_url`: YouTube channel URL (unique)

### `videos` Table
- `id`: Primary key
- `channel_id`: Foreign key to channels
- `video_url`: YouTube video URL (unique)
- `title`: Video title
- `transcript`: Extracted transcript
- `tweet_text`: Generated tweet text
- `tweet_media`: Optional media attachment
- `posted_status`: Status (`pending`, `done`, `error`, `published`)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Usage Examples

### Manual API Calls

```bash
# Add channels and their videos
curl -X POST "http://localhost:8006/fetch-channel-videos" \
  -H "Authorization: Bearer your_auth_token"

# Scan for new videos
curl -X POST "http://localhost:8006/scan-new-channel-videos" \
  -H "Authorization: Bearer your_auth_token"

# Generate tweet for the oldest pending video
curl -X POST "http://localhost:8006/generate-tweets" \
  -H "Authorization: Bearer your_auth_token"

# Post to X
curl -X POST "http://localhost:8006/post-to-x" \
  -H "Authorization: Bearer your_auth_token"

# Check status
curl -X GET "http://localhost:8006/status" \
  -H "Authorization: Bearer your_auth_token"
```

### Automation with Cron

Add to your crontab for automated posting:

```bash
# Edit crontab
crontab -e

# Add these lines for automated execution
# Scan for new videos every 30 minutes
*/30 * * * * curl -X POST "http://localhost:8006/scan-new-channel-videos" -H "Authorization: Bearer your_token"

# Generate tweet for the oldest pending video every hour
0 * * * * curl -X POST "http://localhost:8006/generate-tweets" -H "Authorization: Bearer your_token"

# Post to X every 4 hours
0 */4 * * * curl -X POST "http://localhost:8006/post-to-x" -H "Authorization: Bearer your_token"
```

## Implementation Status

**✅ Completed Structure:**
- FastAPI application with authentication
- SQLite database schema and manager
- All API endpoints with proper error handling
- Configuration management
- Logging setup
- Supadata API integration for transcript extraction
- OpenAI integration for tweet generation

**🔄 Extensible/Pluggable:**
- Prompt template for tweet generation is easily customizable
- Add/remove channels as needed
- Extend endpoints for more features

## Security Considerations

- Never commit your `.env` file
- Use strong, unique tokens for `SYSTEM_AUTH_TOKEN`
- Regularly rotate your API keys
- Run the application behind a reverse proxy in production
- Monitor API usage and rate limits

## Support

The application includes comprehensive logging and error handling. Check the logs for debugging information and monitor the `/status` endpoint for health checks.