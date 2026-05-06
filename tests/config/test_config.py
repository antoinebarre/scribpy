"""Tests for minimal scribpy.toml configuration loading."""

from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest

import scribpy.config.loader as config_loader
from scribpy.config.loader import (
    ConfigParseError,
    find_config,
    load_config,
    load_toml_config,
    parse_config,
    validate_config,
)
from scribpy.config.types import Config, IndexConfig, PathConfig, ProjectConfig


def test_config_objects_are_frozen_dataclasses() -> None:
    config_types = (ProjectConfig, PathConfig, IndexConfig, Config)

    for config_type in config_types:
        assert is_dataclass(config_type)
        assert config_type.__dataclass_params__.frozen is True


def test_default_config_matches_phase_2_conventions() -> None:
    config = parse_config({})

    assert config.project.name is None
    assert config.paths.source == Path("doc")
    assert config.index.mode == "filesystem"
    assert config.index.files == ()

    with pytest.raises(FrozenInstanceError):
        config.paths.source = Path("docs")


def test_parse_config_reads_minimal_toml_shape() -> None:
    config = parse_config(
        {
            "project": {"name": "scribpy-docs"},
            "paths": {"source": "docs"},
            "index": {"mode": "explicit", "files": ["intro.md", "guide/setup.md"]},
        }
    )

    assert config.project.name == "scribpy-docs"
    assert config.paths.source == Path("docs")
    assert config.index.mode == "explicit"
    assert config.index.files == (Path("intro.md"), Path("guide/setup.md"))


def test_parse_config_accepts_hybrid_index_mode_for_later_diagnostics() -> None:
    config = parse_config({"index": {"mode": "hybrid"}})

    assert config.index.mode == "hybrid"


def test_find_config_walks_up_from_nested_directory(tmp_path: Path) -> None:
    config_path = tmp_path / "scribpy.toml"
    nested = tmp_path / "doc" / "guide"
    nested.mkdir(parents=True)
    config_path.write_text('[project]\nname = "docs"\n', encoding="utf-8")

    assert find_config(nested) == config_path


def test_load_toml_config_reads_raw_data(tmp_path: Path) -> None:
    config_path = tmp_path / "scribpy.toml"
    config_path.write_text(
        '[project]\nname = "docs"\n\n[paths]\nsource = "doc"\n',
        encoding="utf-8",
    )

    assert load_toml_config(config_path) == {
        "project": {"name": "docs"},
        "paths": {"source": "doc"},
    }


def test_validate_config_rejects_absolute_source_path() -> None:
    diagnostics = validate_config(Config(paths=PathConfig(source=Path("/docs"))))

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CFG004"
    assert diagnostics[0].severity == "error"


def test_validate_config_rejects_parent_segments_in_index_files() -> None:
    diagnostics = validate_config(
        Config(index=IndexConfig(mode="explicit", files=(Path("../secret.md"),)))
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CFG004"
    assert diagnostics[0].path == Path("../secret.md")


def test_load_config_returns_cfg001_when_missing(tmp_path: Path) -> None:
    config, diagnostics = load_config(tmp_path)

    assert config is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CFG001"


def test_load_config_returns_cfg002_for_invalid_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "scribpy.toml"
    config_path.write_text('[project\nname = "broken"\n', encoding="utf-8")

    config, diagnostics = load_config(tmp_path)

    assert config is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CFG002"
    assert diagnostics[0].path == config_path


def test_load_config_returns_cfg003_for_invalid_value_type(tmp_path: Path) -> None:
    config_path = tmp_path / "scribpy.toml"
    config_path.write_text("[paths]\nsource = 42\n", encoding="utf-8")

    config, diagnostics = load_config(config_path)

    assert config is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CFG003"
    assert diagnostics[0].path == config_path


def test_load_config_returns_cfg001_when_file_read_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "scribpy.toml"
    config_path.write_text("[project]\n", encoding="utf-8")

    def fail_to_load_toml(_path: Path) -> dict[str, object]:
        raise OSError("permission denied")

    monkeypatch.setattr(config_loader, "load_toml_config", fail_to_load_toml)

    config, diagnostics = load_config(config_path)

    assert config is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CFG001"
    assert diagnostics[0].path == config_path


def test_load_config_returns_config_and_no_diagnostics_for_valid_file(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "scribpy.toml"
    config_path.write_text(
        '[project]\nname = "docs"\n\n'
        '[paths]\nsource = "doc"\n\n'
        '[index]\nmode = "explicit"\nfiles = ["index.md"]\n',
        encoding="utf-8",
    )

    config, diagnostics = load_config(config_path)

    assert diagnostics == ()
    assert config == Config(
        project=ProjectConfig(name="docs"),
        paths=PathConfig(source=Path("doc")),
        index=IndexConfig(mode="explicit", files=(Path("index.md"),)),
    )


def test_load_config_returns_cfg004_for_unsafe_but_parseable_path(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "scribpy.toml"
    config_path.write_text('[paths]\nsource = "../doc"\n', encoding="utf-8")

    config, diagnostics = load_config(config_path)

    assert config is not None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CFG004"


@pytest.mark.parametrize(
    ("raw", "message"),
    (
        ({"project": "docs"}, "Configuration section [project] must be a table."),
        (
            {"project": {"name": 42}},
            "Configuration value project.name must be a string.",
        ),
        (
            {"index": {"mode": 42}},
            "Configuration value index.mode must be a string.",
        ),
        (
            {"index": {"mode": "unknown"}},
            "Configuration value index.mode must be 'filesystem', 'explicit', "
            "or 'hybrid'.",
        ),
        (
            {"index": {"files": "index.md"}},
            "Configuration value index.files must be a list.",
        ),
        (
            {"index": {"files": [42]}},
            "Every index.files entry must be a string.",
        ),
    ),
)
def test_parse_config_rejects_invalid_shapes(
    raw: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ConfigParseError) as exc_info:
        parse_config(raw)
    assert str(exc_info.value) == message
