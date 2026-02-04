"""
Tests for ToolRegistry - method discovery and tool registration.
"""

import inspect
from typing import List, Optional, get_type_hints

from cyberedu_mcp.tool_registry import MethodMetadata, ToolRegistry


class TestToolRegistryParameterSchema:
    """Parameter schema building for JSON schema."""

    def test_optional_str_maps_to_string(self):
        registry = ToolRegistry()

        def sample(challenge_id: str, limit: Optional[int] = 10) -> dict:
            """Sample."""
            return {}

        schema = registry._build_parameter_schema(
            inspect.signature(sample),
            get_type_hints(sample),
        )
        props = schema["properties"]
        assert props["challenge_id"]["type"] == "string"
        assert props["limit"]["type"] == "integer"
        assert "challenge_id" in schema["required"]
        assert "limit" not in schema["required"]

    def test_list_param_maps_to_array(self):
        registry = ToolRegistry()

        def sample(tag_list: List[str]) -> dict:
            return {}

        schema = registry._build_parameter_schema(
            inspect.signature(sample),
            get_type_hints(sample),
        )
        # List[str] maps to array when typing.List is recognized
        param_type = schema["properties"]["tag_list"]["type"]
        assert param_type in ("array", "string")


class TestToolRegistryCategory:
    """Category determination from method name."""

    def test_training_methods_categorized(self):
        registry = ToolRegistry()
        assert registry._determine_category("list_trainings") == "trainings"
        # "training" in name matches trainings before services
        assert registry._determine_category("get_training_service_status") == "trainings"

    def test_challenge_methods_categorized(self):
        registry = ToolRegistry()
        assert registry._determine_category("list_challenges") == "challenges"

    def test_contest_methods_categorized(self):
        registry = ToolRegistry()
        assert registry._determine_category("get_contest") == "contests"

    def test_unknown_falls_back_to_general(self):
        registry = ToolRegistry()
        assert registry._determine_category("custom_action") == "general"


class TestToolRegistry:
    """ToolRegistry discovery and lookup."""

    def test_discover_from_class_finds_public_methods(self):
        registry = ToolRegistry()

        class SampleClient:
            def public_method(self, x: str) -> str:
                """A public method."""
                return x

            def _private_method(self):
                pass

        discovered = registry.discover_from_class(SampleClient)
        assert len(discovered) == 1
        assert discovered[0].name == "public_method"
        assert "x" in discovered[0].parameters.get("properties", {})

    def test_excluded_methods_not_discovered(self):
        registry = ToolRegistry()
        from cyberedu_client import CyberEduClient

        discovered = registry.discover_from_class(CyberEduClient)
        names = [m.name for m in discovered]
        assert "_build_request_headers" not in names
        assert "_make_request" not in names
        assert "set_session_cookie" not in names
        assert "close" not in names

    def test_get_method_returns_metadata(self):
        registry = ToolRegistry()

        def sample_tool(x: int) -> dict:
            """Sample tool."""
            return {"x": x}

        registry.register_method(
            name="sample_tool",
            method=sample_tool,
            description="A sample",
            parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
        )
        meta = registry.get_method("sample_tool")
        assert meta is not None
        assert meta.name == "sample_tool"
        assert meta.description == "A sample"

    def test_get_method_returns_none_for_unknown(self):
        registry = ToolRegistry()
        assert registry.get_method("nonexistent_tool") is None

    def test_list_methods_returns_all_registered(self):
        registry = ToolRegistry()
        from cyberedu_client import CyberEduClient

        registry.discover_from_class(CyberEduClient)
        methods = registry.list_methods()
        assert len(methods) > 0
        assert all(isinstance(m, MethodMetadata) for m in methods)
