"""
Tests for CyberEdu client module-level helpers (pure functions).
"""

from cyberedu_client.cyberedu_client import (
    _build_challenge_sort_key,
    _extract_deployment_state_from_status,
    _filter_challenges_by_tags,
    _is_deployment_failed,
    _is_deployment_ready,
)


class TestFilterChallengesByTags:
    """_filter_challenges_by_tags."""

    def test_filters_by_single_tag(self):
        challenges = [
            {"id": "1", "tags": ["web", "easy"]},
            {"id": "2", "tags": ["pwn"]},
            {"id": "3", "tags": ["web"]},
        ]
        result = _filter_challenges_by_tags(challenges, "web")
        assert len(result) == 2
        assert all(c["id"] in ("1", "3") for c in result)

    def test_filters_by_multiple_tags(self):
        challenges = [
            {"id": "1", "tags": ["web"]},
            {"id": "2", "tags": ["pwn"]},
            {"id": "3", "tags": ["crypto"]},
        ]
        result = _filter_challenges_by_tags(challenges, ["web", "pwn"])
        assert len(result) == 2
        assert all(c["id"] in ("1", "2") for c in result)

    def test_case_insensitive(self):
        challenges = [{"id": "1", "tags": ["Web"]}]
        result = _filter_challenges_by_tags(challenges, "web")
        assert len(result) == 1

    def test_returns_empty_when_no_match(self):
        challenges = [{"id": "1", "tags": ["web"]}]
        result = _filter_challenges_by_tags(challenges, "pwn")
        assert result == []


class TestBuildChallengeSortKey:
    """_build_challenge_sort_key."""

    def test_solves_sort_key(self):
        key_fn = _build_challenge_sort_key("solves")
        c = {"counts": {"owned": 10}, "points": 100}
        assert key_fn(c) == 10

    def test_attempts_sort_key(self):
        key_fn = _build_challenge_sort_key("attempts")
        c = {"counts": {"attempts": 5}, "points": 50}
        assert key_fn(c) == 5

    def test_points_sort_key(self):
        key_fn = _build_challenge_sort_key("points")
        c = {"counts": {}, "points": 200}
        assert key_fn(c) == 200


class TestDeploymentStateHelpers:
    """Deployment state extraction and checks."""

    def test_extract_deployment_state(self):
        status = {"data": {"status": "Running"}}
        assert _extract_deployment_state_from_status(status) == "running"

    def test_extract_deployment_state_empty(self):
        assert _extract_deployment_state_from_status({}) == ""

    def test_is_deployment_ready(self):
        assert _is_deployment_ready("running") is True
        assert _is_deployment_ready("ready") is True
        assert _is_deployment_ready("pending") is False

    def test_is_deployment_failed(self):
        assert _is_deployment_failed("error") is True
        assert _is_deployment_failed("failed") is True
        assert _is_deployment_failed("running") is False
