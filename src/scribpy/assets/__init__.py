"""Static assets and diagram handling for scribpy."""

from scribpy.assets.copy import (
    collect_asset_paths,
    copy_assets,
    copy_css_files_single_page,
    rewrite_asset_links_single_page,
)

__all__ = [
    "collect_asset_paths",
    "copy_assets",
    "copy_css_files_single_page",
    "rewrite_asset_links_single_page",
]
