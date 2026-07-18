"""Compatibility alias for local Mermaid CLI rendering."""

from scribpy.core.mermaid.cli import MermaidCliRenderer

LocalRenderer = MermaidCliRenderer

__all__ = ["LocalRenderer"]
