"""
Tests for CyberEduClient - API client with mocked HTTP.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cyberedu_client import CyberEduClient


class TestBuildRequestHeaders:
    """_build_request_headers."""

    def test_includes_cookie_when_set(self):
        client = CyberEduClient(tenant="cyberedu", session_cookie="abc123")
        headers = client._build_request_headers()
        assert headers.get("Cookie") == "cyberedu_session=abc123"

    def test_no_cookie_when_empty(self):
        client = CyberEduClient(tenant="cyberedu")
        headers = client._build_request_headers()
        assert "Cookie" not in headers or headers.get("Cookie") is None

    def test_merges_extra_headers(self):
        client = CyberEduClient(tenant="cyberedu", session_cookie="x")
        headers = client._build_request_headers({"X-Custom": "value"})
        assert headers["X-Custom"] == "value"
        assert headers["Cookie"] == "cyberedu_session=x"


class TestParseDownloadUuidFromResponse:
    """_parse_download_uuid_from_response."""

    def test_extracts_from_data_uuid(self):
        client = CyberEduClient(tenant="cyberedu")
        body = {"data": {"uuid": "abc-123"}}
        assert client._parse_download_uuid_from_response(body) == "abc-123"

    def test_extracts_from_data_string(self):
        client = CyberEduClient(tenant="cyberedu")
        body = {"data": "uuid-as-string"}
        assert client._parse_download_uuid_from_response(body) == "uuid-as-string"

    def test_extracts_from_top_level_uuid(self):
        client = CyberEduClient(tenant="cyberedu")
        body = {"uuid": "top-level-uuid"}
        assert client._parse_download_uuid_from_response(body) == "top-level-uuid"

    def test_raises_when_uuid_missing(self):
        client = CyberEduClient(tenant="cyberedu")
        with pytest.raises(ValueError, match="Could not extract"):
            client._parse_download_uuid_from_response({"data": {}})


class TestExtractFilenameFromContentDisposition:
    """_extract_filename_from_content_disposition."""

    def test_extracts_quoted_filename(self):
        client = CyberEduClient(tenant="cyberedu")
        header = 'attachment; filename="example.txt"'
        assert client._extract_filename_from_content_disposition(header) == "example.txt"

    def test_extracts_unquoted_filename(self):
        client = CyberEduClient(tenant="cyberedu")
        header = "attachment; filename=report.pdf"
        assert client._extract_filename_from_content_disposition(header) == "report.pdf"

    def test_returns_default_when_no_filename(self):
        client = CyberEduClient(tenant="cyberedu")
        assert client._extract_filename_from_content_disposition("inline") == "downloaded_file"


class TestListChallengesWithMockedHttp:
    """list_challenges with mocked _make_request."""

    def test_returns_challenges_from_api(self):
        client = CyberEduClient(tenant="cyberedu")
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": "1", "title": "Challenge 1"},
            {"id": "2", "title": "Challenge 2"},
        ]
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_make_request", return_value=mock_response):
            result = client.list_challenges()
        assert len(result) == 2
        assert result[0]["id"] == "1"

    def test_applies_tag_filter(self):
        client = CyberEduClient(tenant="cyberedu")
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": "1", "tags": ["web"]},
            {"id": "2", "tags": ["pwn"]},
        ]
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_make_request", return_value=mock_response):
            result = client.list_challenges(tag_filter="web")
        assert len(result) == 1
        assert result[0]["id"] == "1"


class TestListTopChallengesWithMockedHttp:
    """list_top_challenges with mocked list_challenges."""

    def test_sorts_and_limits(self):
        client = CyberEduClient(tenant="cyberedu")
        challenges = [
            {"id": "1", "counts": {"owned": 5}, "points": 100},
            {"id": "2", "counts": {"owned": 20}, "points": 200},
            {"id": "3", "counts": {"owned": 10}, "points": 150},
        ]
        with patch.object(client, "list_challenges", return_value=challenges):
            result = client.list_top_challenges(limit=2, sort_by="solves")
        assert len(result) == 2
        assert result[0]["id"] == "2"  # Most solves first
        assert result[1]["id"] == "3"


class TestSaveDownloadedFile:
    """_save_downloaded_file - file writing."""

    def test_writes_file_and_returns_result(self):
        """Use explicit file path (with suffix) to avoid directory creation in temp."""
        client = CyberEduClient(tenant="cyberedu")
        mock_response = MagicMock()
        mock_response.headers = {"content-disposition": 'filename="test.txt"'}

        # Use a path with .txt suffix so it's treated as explicit file path
        save_path = Path(__file__).parent / "test_output_download.txt"
        try:
            result = client._save_downloaded_file(
                content=b"file content",
                save_path=save_path,
                response=mock_response,
            )
            assert result["success"] is True
            assert result["size"] == 12
            assert Path(result["path"]).exists()
            assert Path(result["path"]).read_bytes() == b"file content"
        finally:
            try:
                if save_path.exists():
                    save_path.unlink(missing_ok=True)
            except OSError:
                pass  # Cleanup best-effort; test already passed
