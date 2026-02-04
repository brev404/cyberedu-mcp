"""
CyberEdu MCP Server

A dynamic Model Context Protocol (MCP) server for the CyberEdu CTF platform.
Automatically discovers and exposes all CyberEduClient methods as MCP tools.
"""

__version__ = "0.1.0"

from .server import main, server
from .tool_registry import ToolRegistry, MethodMetadata

__all__ = [
    "server",
    "ToolRegistry",
    "MethodMetadata",
    "main",
]
