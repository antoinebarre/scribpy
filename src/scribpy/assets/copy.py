"""Asset collection, copy, and rewrite public facade."""

from __future__ import annotations

from scribpy.assets.collection import collect_asset_paths
from scribpy.assets.css_copy import copy_css_files_single_page
from scribpy.assets.file_copy import copy_assets
from scribpy.assets.rewrite import rewrite_asset_links_single_page

__all__ = [
    "collect_asset_paths",
    "copy_assets",
    "copy_css_files_single_page",
    "rewrite_asset_links_single_page",
]
