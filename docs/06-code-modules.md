# Code Modules

The agent's bash tool runs these Python helpers. They're intentionally thin — most logic lives in the agent's reasoning, not in Python. The helpers exist only for I/O steps that benefit from being deterministic: parsing RSS, calling YouTube APIs, sending email.

The builder should write these as standalone scripts that the agent invokes via the bash tool, with all parameters passed via stdin (JSON) or argv.

---

## `fetch_rss.py`

Fetch a podcast RSS feed and return episodes since a given date.

```python
#!/usr/bin/env python3
"""
Fetch RSS feed and return episodes published since a cutoff date.

Usage:
  python fetch_rss.py <rss_url> <cutoff_iso_date>

Output (stdout): JSON array of episodes, each with:
  - guid: stable identifier
  - title: episode title
  - published: ISO 8601 datetime
  - description: HTML or plain text description
  - audio_url: direct mp3/audio link (from enclosure)
  - duration_seconds: integer, if available
"""

import sys
import json
import feedparser
from dateutil import parser as dateparser
from datetime import datetime, timezone


def main():
    rss_url = sys.argv[1]
    cutoff_iso = sys.argv[2]
    cutoff = dateparser.parse(cutoff_iso)
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)

    feed = feedparser.parse(rss_url)
    episodes = []

    for entry in feed.entries:
        # GUID handling: some feeds use 'id', some 'guid', some only link
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
            # itunes_duration can be "HH:MM:SS" or seconds as a string
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

    print(json.dumps(episodes, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

---

## `find_youtube_video.py`

Search a YouTube channel for a video matching a podcast episode title. Returns top candidates; the agent picks the best.

```python
#!/usr/bin/env python3
"""
Search a YouTube channel for videos matching a query string.
Returns up to N candidates, sorted by relevance.

Usage:
  python find_youtube_video.py <channel_url> <query> [max_results=5]

Output (stdout): JSON array of candidates, each with:
  - video_id
  - title
  - description (truncated)
  - duration_seconds
  - upload_date (YYYYMMDD string)
  - url

Strategy: use yt-dlp to list channel videos. yt-dlp's --flat-playlist mode
is fast and avoids fetching full metadata. We list the latest ~20 videos
from the channel and let the agent reason over them.
"""

import sys
import json
import subprocess


def main():
    channel_url = sys.argv[1]
    query = sys.argv[2]
    max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    # Get the latest N videos from the channel (newest first)
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--playlist-end", "20",
        channel_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        print(json.dumps({"error": result.stderr[-500:]}))
        sys.exit(1)

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

    # Return the latest 20 unfiltered. The agent decides which match.
    # We could pre-filter by string similarity but that's exactly the brittle
    # logic we want to avoid — let Claude pick.
    print(json.dumps(candidates[:max_results * 2], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

---

## `fetch_transcript.py`

Fetch the auto-caption transcript for a given YouTube video.

```python
#!/usr/bin/env python3
"""
Fetch the transcript for a YouTube video.

Usage:
  python fetch_transcript.py <video_id>

Output (stdout): JSON with:
  - video_id
  - language
  - is_generated: bool (true if auto-caption, false if manual)
  - segments: list of {start, duration, text}
  - full_text: joined transcript text

Errors are returned as JSON {"error": "...message..."} with non-zero exit.
"""

import sys
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


def main():
    video_id = sys.argv[1]

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except (TranscriptsDisabled, VideoUnavailable) as e:
        print(json.dumps({"error": f"unavailable: {type(e).__name__}"}))
        sys.exit(2)
    except Exception as e:
        print(json.dumps({"error": f"unknown: {type(e).__name__}: {e}"}))
        sys.exit(3)

    # Prefer English, prefer manual, fall back to auto-generated
    transcript = None
    try:
        transcript = transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
        is_generated = False
    except NoTranscriptFound:
        try:
            transcript = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
            is_generated = True
        except NoTranscriptFound:
            # Try any language, will work for multilingual transcripts
            for t in transcript_list:
                transcript = t
                is_generated = t.is_generated
                break

    if transcript is None:
        print(json.dumps({"error": "no_transcript_available"}))
        sys.exit(4)

    segments = transcript.fetch()
    full_text = " ".join(s["text"] for s in segments)

    output = {
        "video_id": video_id,
        "language": transcript.language_code,
        "is_generated": is_generated,
        "segments": segments,
        "full_text": full_text,
    }

    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

---

## `send_email.py`

Send the daily briefing email via Resend.

```python
#!/usr/bin/env python3
"""
Send an email via Resend.

Usage:
  python send_email.py
  (reads JSON from stdin: {"subject": "...", "html": "...", "to": "...", "from": "..."})

Output (stdout): JSON with delivery status.
"""

import sys
import json
import os
import resend


def main():
    payload = json.load(sys.stdin)
    resend.api_key = os.environ["RESEND_API_KEY"]

    try:
        result = resend.Emails.send({
            "from": payload["from"],
            "to": [payload["to"]],
            "subject": payload["subject"],
            "html": payload["html"],
        })
        print(json.dumps({"status": "ok", "id": result.get("id")}))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## How the agent uses these

The agent doesn't write Python — it invokes these scripts via the bash tool. Example sequence:

```
1. Agent's bash call:
   python fetch_rss.py "https://feeds.megaphone.fm/investlikethebest" "2026-05-20T07:00:00Z"
   → returns JSON of new episodes

2. For each new episode, agent's bash call:
   python find_youtube_video.py "https://youtube.com/@InvestLikeTheBest" "Gavin Baker" 5
   → returns candidate videos

3. Agent reasons over the candidates, picks one. Then bash call:
   python fetch_transcript.py <video_id>
   → returns transcript

4. Agent summarizes in its own context (no Python needed).

5. Agent calls Notion MCP to create the briefing page.

6. Agent calls Slack MCP to post the message.

7. Agent bash call:
   echo '{"subject":"...","html":"...","to":"hamid@lendhub.co.uk","from":"..."}' | python send_email.py
   → email sent
```

The scripts are pure-function I/O. The agent owns all the decision-making.

---

## Where to deploy these scripts

The Managed Agents sandbox supports preinstalled files. The builder should:

1. Place `fetch_rss.py`, `find_youtube_video.py`, `fetch_transcript.py`, `send_email.py` in the agent's sandbox at a known path (e.g., `/sandbox/helpers/`).
2. Add that path to the agent's startup setup OR have the agent reference them by absolute path.
3. Confirm pip-installed packages (`feedparser`, `youtube-transcript-api`, `yt-dlp`, `resend`, `requests`, `python-dateutil`) are listed in `sandbox.preinstalled_packages` in the agent definition.

If the Managed Agents sandbox doesn't support preinstalled files (only preinstalled packages), an alternative: store the scripts in a small public GitHub repo and have the agent's first bash step `git clone` it. Or paste the script content into the agent's system prompt as a `<helpers>` block and have it write the files at run-start. The cleanest path depends on the current Managed Agents file-deployment story — builder, check the docs and pick the simplest working option.
