#!/usr/bin/env python3
"""
Fetch the auto-caption transcript for a given YouTube video.

Usage:
  python -m podcast_brief.fetch_transcript <video_id>

Output (stdout): JSON with:
  - video_id
  - language
  - is_generated: bool (true if auto-caption, false if manual)
  - segments: list of {start, duration, text}
  - full_text: joined transcript text
"""

import json
import sys

from youtube_transcript_api import YouTubeTranscriptApi


def fetch_transcript(video_id: str) -> dict:
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=["en", "en-US", "en-GB"])
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

    segments = [
        {
            "start": snippet.start,
            "duration": snippet.duration,
            "text": snippet.text,
        }
        for snippet in transcript.snippets
    ]
    full_text = " ".join(s["text"] for s in segments)

    return {
        "video_id": video_id,
        "language": "en",
        "is_generated": True,
        "segments": segments,
        "full_text": full_text,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m podcast_brief.fetch_transcript <video_id>", file=sys.stderr)
        sys.exit(1)

    video_id = sys.argv[1]
    result = fetch_transcript(video_id)

    if "error" in result:
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(2)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
