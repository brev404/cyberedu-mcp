"""
Tool Registry for Dynamic Method Discovery

This module provides a registry system that can be extended with new methods
without modifying the core MCP server code.
"""

import inspect
from typing import Any, Dict, List, Optional, Callable, get_type_hints
from dataclasses import dataclass


@dataclass
class MethodMetadata:
    """Metadata for a method that will be exposed as an MCP tool."""

    name: str
    method: Callable
    description: str
    parameters: Dict[str, Any]
    category: Optional[str] = None  # e.g., 'auth', 'challenges', 'contests', 'services'


class ToolRegistry:
    """
    Registry for managing tools dynamically.

    This allows adding new methods to CyberEduClient without modifying
    the MCP server code. Methods are automatically discovered and registered.
    """

    def __init__(self):
        self._methods: Dict[str, MethodMetadata] = {}
        self._excluded_methods = {
            "_build_request_headers",
            "_make_request",
            "_parse_download_uuid_from_response",
            "_parse_flag_submission_response",
            "_extract_filename_from_content_disposition",
            "_resolve_save_path",
            "_write_file_to_disk",
            "_save_downloaded_file",
            "set_session_cookie",
            "close",
            "__enter__",
            "__exit__",
        }

    def discover_from_class(self, cls: type, prefix: str = "") -> List[MethodMetadata]:
        """
        Discover all public methods from a class.

        Args:
            cls: The class to discover methods from
            prefix: Optional prefix to add to method names

        Returns:
            List of MethodMetadata objects
        """
        methods = []

        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            # Skip excluded methods
            if name in self._excluded_methods or name.startswith("_"):
                continue

            # Get method signature
            sig = inspect.signature(method)

            # Get type hints
            try:
                hints = get_type_hints(method)
            except Exception:
                hints = {}

            # Extract parameter descriptions from docstring
            param_descriptions = self._extract_param_descriptions(method.__doc__)

            # Build parameter schema with docstring descriptions
            parameters = self._build_parameter_schema(sig, hints, param_descriptions)

            # Get description from docstring
            description = self._extract_description(method.__doc__)

            # Determine category from method name
            category = self._determine_category(name)

            full_name = f"{prefix}{name}" if prefix else name

            metadata = MethodMetadata(
                name=full_name,
                method=method,
                description=description,
                parameters=parameters,
                category=category,
            )

            methods.append(metadata)
            self._methods[full_name] = metadata

        return methods

    def _build_parameter_schema(
        self,
        sig: inspect.Signature,
        hints: Dict[str, type],
        param_descriptions: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Build JSON schema for method parameters."""
        schema = {"type": "object", "properties": {}, "required": []}

        if param_descriptions is None:
            param_descriptions = {}

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_info = self._get_parameter_info(param, hints.get(param_name))

            # Use docstring description if available, otherwise keep the generic one
            if param_name in param_descriptions:
                param_info["description"] = param_descriptions[param_name]

            schema["properties"][param_name] = param_info

            # Add to required if no default value
            if param.default == inspect.Parameter.empty:
                schema["required"].append(param_name)

        return schema

    def _get_parameter_info(
        self, param: inspect.Parameter, type_hint: Optional[type]
    ) -> Dict[str, Any]:
        """Get parameter information for JSON schema."""
        param_info: Dict[str, Any] = {"description": f"Parameter: {param.name}"}

        # Determine type
        param_type = type_hint or param.annotation

        # Handle Optional types and Union types
        if hasattr(param_type, "__origin__"):
            origin = param_type.__origin__
            # Check for Union or Optional (which is Union[T, None])
            if hasattr(origin, "__name__") and origin.__name__ in ("Union", "_UnionGenericAlias"):
                # This is Optional[Something] or Union, get the actual type
                args = getattr(param_type, "__args__", [])
                # Filter out NoneType
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    param_type = non_none_args[0]

        # Map Python types to JSON schema types
        param_type_str = str(param_type)

        if param_type is str or "str" in param_type_str:
            param_info["type"] = "string"
        elif param_type is int or "int" in param_type_str:
            param_info["type"] = "integer"
        elif param_type is float or "float" in param_type_str:
            param_info["type"] = "number"
        elif param_type is bool or "bool" in param_type_str:
            param_info["type"] = "boolean"
        elif hasattr(param_type, "__origin__") and param_type.__origin__ in (list, List):
            param_info["type"] = "array"
            param_info["items"] = {}
        elif hasattr(param_type, "__origin__") and param_type.__origin__ in (dict, Dict):
            param_info["type"] = "object"
        elif param_type is list or param_type is List:
            param_info["type"] = "array"
            param_info["items"] = {}
        elif param_type is dict or param_type is Dict:
            param_info["type"] = "object"
        else:
            # Default to string for unknown types
            param_info["type"] = "string"

        return param_info

    def _extract_description(self, docstring: Optional[str]) -> str:
        """Extract description from docstring, including more context."""
        if not docstring:
            return ""

        # Parse docstring to get main description (everything before Args/Returns/etc.)
        lines = docstring.split("\n")
        description_lines = []

        for line in lines:
            stripped = line.strip()
            # Stop at Args:, Returns:, Raises:, Example:, Note:, etc.
            if stripped.startswith(
                ("Args:", "Returns:", "Raises:", "Example:", "Note:", "Parameters:")
            ):
                break
            if stripped:
                description_lines.append(stripped)

        # Join lines and clean up
        description = " ".join(description_lines)

        # Limit length but keep meaningful content
        if len(description) > 300:
            description = description[:297] + "..."

        return description if description else ""

    def _extract_param_descriptions(self, docstring: Optional[str]) -> Dict[str, str]:
        """Extract parameter descriptions from docstring Args section."""
        if not docstring:
            return {}

        param_descriptions = {}
        in_args = False
        current_param = None
        current_desc = []

        for line in docstring.split("\n"):
            stripped = line.strip()

            if stripped.startswith("Args:"):
                in_args = True
                continue
            elif stripped.startswith(("Returns:", "Raises:", "Example:", "Note:")):
                in_args = False
                # Save last param
                if current_param and current_desc:
                    param_descriptions[current_param] = " ".join(current_desc)
                break

            if in_args:
                # Check for new parameter (format: "param_name: description" or "param_name (type): description")
                if ":" in stripped and not stripped.startswith(" "):
                    # Save previous param
                    if current_param and current_desc:
                        param_descriptions[current_param] = " ".join(current_desc)

                    # Parse new param
                    parts = stripped.split(":", 1)
                    param_part = parts[0].strip()
                    # Remove type hints like "(str)" or "(Optional[str])"
                    if "(" in param_part:
                        param_part = param_part.split("(")[0].strip()
                    current_param = param_part
                    current_desc = [parts[1].strip()] if len(parts) > 1 and parts[1].strip() else []
                elif current_param and stripped:
                    # Continuation of previous param description
                    current_desc.append(stripped)

        # Save last param
        if current_param and current_desc:
            param_descriptions[current_param] = " ".join(current_desc)

        return param_descriptions

    def _determine_category(self, method_name: str) -> str:
        """Determine category based on method name."""
        if "auth" in method_name or "user" in method_name or "tenant" in method_name:
            return "authentication"
        elif "training" in method_name:
            return "trainings"
        elif "contest" in method_name:
            return "contests"
        elif "challenge" in method_name:
            return "challenges"
        elif "service" in method_name or "deployment" in method_name:
            return "services"
        elif "flag" in method_name or "submit" in method_name:
            return "flags"
        elif "file" in method_name or "download" in method_name:
            return "files"
        else:
            return "general"

    def get_method(self, name: str) -> Optional[MethodMetadata]:
        """Get method metadata by name."""
        return self._methods.get(name)

    def list_methods(self) -> List[MethodMetadata]:
        """List all registered methods."""
        return list(self._methods.values())

    def register_method(
        self,
        name: str,
        method: Callable,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
    ):
        """
        Manually register a method (for custom extensions).

        Args:
            name: Method name
            method: Callable method
            description: Method description
            parameters: Parameter schema (optional, will be auto-generated)
            category: Method category (optional)
        """
        if parameters is None:
            # Auto-generate from signature
            sig = inspect.signature(method)
            hints = get_type_hints(method) if hasattr(method, "__annotations__") else {}
            parameters = self._build_parameter_schema(sig, hints)

        metadata = MethodMetadata(
            name=name,
            method=method,
            description=description,
            parameters=parameters,
            category=category,
        )

        self._methods[name] = metadata
