"""Public Python API facade for Scribpy."""

from scribpy.core.index_check import run_index_check

check_index = run_index_check

__all__ = ["check_index", "run_index_check"]
