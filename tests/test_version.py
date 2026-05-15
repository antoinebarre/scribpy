"""Tests for package version resolution."""

from __future__ import annotations

import importlib
import importlib.metadata

import scribpy._version as version_module


def test_version_falls_back_when_package_metadata_is_unavailable(monkeypatch) -> None:
    def missing_version(distribution_name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(distribution_name)

    monkeypatch.setattr(importlib.metadata, "version", missing_version)

    reloaded = importlib.reload(version_module)

    assert reloaded.__version__ == "0.0.0.dev0"
