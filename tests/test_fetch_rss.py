"""Tests for the RSS feed fetcher."""

from unittest.mock import MagicMock, patch

from podcast_brief.fetch_rss import fetch_episodes

MOCK_FEED_ENTRIES = [
    {
        "id": "guid-001",
        "title": "Episode 1: AI Investing",
        "published": "2026-05-20T12:00:00Z",
        "summary": "Discussion about AI investing trends",
        "enclosures": [{"type": "audio/mpeg", "href": "https://example.com/ep1.mp3"}],
        "itunes_duration": "01:30:00",
    },
    {
        "id": "guid-002",
        "title": "Episode 2: Old Episode",
        "published": "2026-01-01T12:00:00Z",
        "summary": "An old episode that should be filtered out",
        "enclosures": [{"type": "audio/mpeg", "href": "https://example.com/ep2.mp3"}],
        "itunes_duration": "45:00",
    },
]


def _make_mock_feed(entries):
    feed = MagicMock()
    mock_entries = []
    for e in entries:
        entry = MagicMock()
        entry.get = lambda k, default="", _e=e: _e.get(k, default)
        entry.__getitem__ = lambda self, k, _e=e: _e[k]
        entry.__contains__ = lambda self, k, _e=e: k in _e
        mock_entries.append(entry)
    feed.entries = mock_entries
    return feed


def test_fetch_episodes_filters_by_date():
    with patch("podcast_brief.fetch_rss.feedparser.parse") as mock_parse:
        mock_parse.return_value = _make_mock_feed(MOCK_FEED_ENTRIES)
        episodes = fetch_episodes("https://example.com/feed.xml", "2026-05-01T00:00:00Z")

    assert len(episodes) == 1
    assert episodes[0]["guid"] == "guid-001"
    assert episodes[0]["title"] == "Episode 1: AI Investing"
    assert episodes[0]["duration_seconds"] == 5400


def test_fetch_episodes_empty_feed():
    with patch("podcast_brief.fetch_rss.feedparser.parse") as mock_parse:
        mock_parse.return_value = _make_mock_feed([])
        episodes = fetch_episodes("https://example.com/feed.xml", "2026-01-01T00:00:00Z")

    assert episodes == []


def test_duration_parsing_seconds_format():
    entry = {
        "id": "guid-003",
        "title": "Short Episode",
        "published": "2026-05-20T12:00:00Z",
        "summary": "Short one",
        "enclosures": [],
        "itunes_duration": "1800",
    }
    with patch("podcast_brief.fetch_rss.feedparser.parse") as mock_parse:
        mock_parse.return_value = _make_mock_feed([entry])
        episodes = fetch_episodes("https://example.com/feed.xml", "2026-05-01T00:00:00Z")

    assert len(episodes) == 1
    assert episodes[0]["duration_seconds"] == 1800
