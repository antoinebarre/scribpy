"""Public Python API facade for Scribpy."""

from scribpy.core.demo import DemoVariant, create_demo_project
from scribpy.core.index_check import run_index_check

check_index = run_index_check

__all__ = ["DemoVariant", "check_index", "create_demo_project", "run_index_check"]
