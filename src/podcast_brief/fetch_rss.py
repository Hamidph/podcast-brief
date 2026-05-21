#!/usr/bin/env python3
"""
Fetch RSS feed and return episodes published since a cutoff date.

Usage:
  python -m podcast_brief.fetch_rss <rss_url> <cutoff_iso_date>

Output (stdout): JSON array of episodes, each with:
  - guid: stable identifier
  - title: episode title
  - published: ISO 8601 datetime
  - description: HTML or plain text description
  - audio_url: direct mp3/audio link (from enclosure)
  - duration_seconds: integer, if available
"""

import json
import sys
from datetime import timezone

import feedparser
from dateutil import parser as dateparser


def fetch_episodes(rss_url: str, cutoff_iso: str) -> list[dict]:
    cutoff = dateparser.parse(cutoff_iso)
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)

    feed = feedparser.parse(rss_url)
    episodes = []

    for entry in feed.entries:
        guid = entry.get("id") or entry.get("guid") or entry.get("link")
        if not guid:
            continue

        published_str = entry.get("published") or entry.get("updated")
        if not published_str:
            continue
        try:
            published = dateparser.parse(published_str)
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if published <= cutoff:
            continue

        audio_url = None
        for enclosure in entry.get("enclosures", []):
            if enclosure.get("type", "").startswith("audio"):
                audio_url = enclosure.get("href") or enclosure.get("url")
                break

        duration = None
        if entry.get("itunes_duration"):
            d = entry["itunes_duration"]
            if ":" in d:
                parts = [int(p) for p in d.split(":")]
                duration = sum(p * 60**i for i, p in enumerate(reversed(parts)))
            else:
                try:
                    duration = int(d)
                except ValueError:
                    pass

        episodes.append({
            "guid": guid,
            "title": entry.get("title", "").strip(),
            "published": published.isoformat(),
            "description": entry.get("summary", "")[:2000],
            "audio_url": audio_url,
            "duration_seconds": duration,
        })

    return episodes


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m podcast_brief.fetch_rss <rss_url> <cutoff_iso_date>", file=sys.stderr)
        sys.exit(1)

    rss_url = sys.argv[1]
    cutoff_iso = sys.argv[2]
    episodes = fetch_episodes(rss_url, cutoff_iso)
    print(json.dumps(episodes, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
