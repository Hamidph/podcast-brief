#!/usr/bin/env python3
"""
Search a YouTube channel for videos matching a podcast episode title.
Returns top candidates; the agent picks the best match.

Usage:
  python -m podcast_brief.find_youtube_video <channel_url> <query> [max_results=5]

Output (stdout): JSON array of candidates, each with:
  - video_id
  - title
  - description (truncated)
  - duration_seconds
  - upload_date (YYYYMMDD string)
  - url
"""

import json
import subprocess
import sys


def find_videos(channel_url: str, query: str, max_results: int = 5) -> list[dict]:
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--playlist-end", "20",
        channel_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        return [{"error": result.stderr[-500:]}]

    candidates = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            video = json.loads(line)
        except json.JSONDecodeError:
            continue
        candidates.append({
            "video_id": video.get("id"),
            "title": video.get("title", ""),
            "description": (video.get("description") or "")[:500],
            "duration_seconds": video.get("duration"),
            "upload_date": video.get("upload_date"),
            "url": f"https://youtube.com/watch?v={video.get('id')}",
        })

    return candidates[:max_results * 2]


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m podcast_brief.find_youtube_video <channel_url> <query> [max_results]", file=sys.stderr)
        sys.exit(1)

    channel_url = sys.argv[1]
    query = sys.argv[2]
    max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    candidates = find_videos(channel_url, query, max_results)
    print(json.dumps(candidates, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
