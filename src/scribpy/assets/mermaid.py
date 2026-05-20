"""Mermaid rendering public facade."""

from __future__ import annotations

from scribpy.assets.mermaid_blocks import render_mermaid_blocks
from scribpy.assets.mermaid_documents import render_mermaid_documents
from scribpy.assets.mermaid_encoding import encode_mermaid_payload
from scribpy.assets.mermaid_renderer import WebMermaidRenderer
from scribpy.assets.mermaid_types import (
    MermaidRenderError,
    MermaidRenderResult,
)

_encode_mermaid_payload = encode_mermaid_payload

__all__ = [
    "MermaidRenderError",
    "MermaidRenderResult",
    "WebMermaidRenderer",
    "_encode_mermaid_payload",
    "render_mermaid_blocks",
    "render_mermaid_documents",
]
