"""Tests for the YouTube transcript fetcher."""

from unittest.mock import MagicMock, patch

from podcast_brief.fetch_transcript import fetch_transcript


def test_fetch_transcript_success():
    mock_snippet_1 = MagicMock()
    mock_snippet_1.start = 0.0
    mock_snippet_1.duration = 5.0
    mock_snippet_1.text = "Hello world"

    mock_snippet_2 = MagicMock()
    mock_snippet_2.start = 5.0
    mock_snippet_2.duration = 5.0
    mock_snippet_2.text = "This is a test"

    mock_transcript = MagicMock()
    mock_transcript.snippets = [mock_snippet_1, mock_snippet_2]

    with patch("podcast_brief.fetch_transcript.YouTubeTranscriptApi") as mock_api_class:
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.fetch.return_value = mock_transcript

        result = fetch_transcript("test_video_id")

    assert result["video_id"] == "test_video_id"
    assert result["full_text"] == "Hello world This is a test"
    assert len(result["segments"]) == 2
    assert "error" not in result


def test_fetch_transcript_error():
    with patch("podcast_brief.fetch_transcript.YouTubeTranscriptApi") as mock_api_class:
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.fetch.side_effect = Exception("Video unavailable")

        result = fetch_transcript("bad_video_id")

    assert "error" in result
