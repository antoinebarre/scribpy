"""Markdown file domain object."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

import mkforge


@dataclass(frozen=True, slots=True)
class MarkdownFile:
    """Represent one Markdown file and its source text.

    Attributes:
        path: Filesystem path associated with the Markdown source.
        content: Markdown source text.
        encoding: Text encoding used when reading or writing the file.
    """

    path: Path
    content: str
    encoding: str = "utf-8"

    @classmethod
    def from_path(
        cls,
        path: str | Path,
        *,
        encoding: str = "utf-8",
    ) -> MarkdownFile:
        """Load a Markdown file from disk.

        Args:
            path: Markdown file path to read.
            encoding: Text encoding used to read the file.

        Returns:
            Loaded Markdown file object.

        Raises:
            OSError: If the file cannot be read.
            UnicodeDecodeError: If the file content cannot be decoded.
        """
        markdown_path = Path(path)
        return cls(
            path=markdown_path,
            content=markdown_path.read_text(encoding=encoding),
            encoding=encoding,
        )

    @property
    def name(self) -> str:
        """Return the Markdown file name.

        Returns:
            File name including suffix.
        """
        return self.path.name

    @property
    def suffix(self) -> str:
        """Return the Markdown file suffix.

        Returns:
            File suffix including the leading dot.
        """
        return self.path.suffix

    def with_content(self, content: str) -> MarkdownFile:
        """Return a copy with replaced Markdown source text.

        Args:
            content: Replacement Markdown source text.

        Returns:
            Markdown file object with updated content.
        """
        return MarkdownFile(
            path=self.path,
            content=content,
            encoding=self.encoding,
        )

    def replace_text(self, old: str, new: str) -> MarkdownFile:
        """Return a copy with text occurrences replaced.

        Args:
            old: Existing text to replace.
            new: Replacement text.

        Returns:
            Markdown file object with updated content.
        """
        return self.with_content(self.content.replace(old, new))

    def write(self, path: str | Path | None = None) -> Path:
        """Write the Markdown source to disk.

        Args:
            path: Optional destination path. When omitted, the object's path is
                used.

        Returns:
            Destination path written.

        Raises:
            OSError: If the file cannot be written.
            UnicodeEncodeError: If the file content cannot be encoded.
        """
        destination = self.path if path is None else Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.content, encoding=self.encoding)
        return destination

    def verify(
        self,
        *,
        settings: mkforge.VerificationSettings | None = None,
        custom_rules: Iterable[mkforge.MarkdownRule] = (),
    ) -> mkforge.VerificationReport:
        """Verify Markdown conformance with mkforge.

        Args:
            settings: Optional mkforge verification settings.
            custom_rules: Extra mkforge rules used for this verification.

        Returns:
            Mkforge verification report.
        """
        return mkforge.verify_markdown(
            self.content,
            source_path=self.path,
            settings=settings,
            custom_rules=custom_rules,
        )

    def has_valid_images(self, *, timeout: float = 5.0) -> bool:
        """Return whether Markdown image references are valid.

        Args:
            timeout: HTTP timeout used by mkforge for remote images.

        Returns:
            True when mkforge validates all image references.
        """
        return mkforge.validate_markdown_images(
            self.content,
            base_path=self.path,
            timeout=timeout,
        )

    def has_expected_headings(
        self,
        expected: Iterable[tuple[int, str]],
        *,
        strict: bool = False,
    ) -> bool:
        """Return whether Markdown headings match expected headings.

        Args:
            expected: Expected heading level and title pairs.
            strict: Whether mkforge must require an exact heading sequence.

        Returns:
            True when mkforge validates the expected headings.
        """
        return mkforge.validate_markdown_headings(
            self.content,
            expected,
            strict=strict,
        )

    def has_expected_yaml(
        self,
        expected: Mapping[str, object],
        *,
        strict: bool = False,
    ) -> bool:
        """Return whether YAML front matter matches expected values.

        Args:
            expected: Expected YAML front matter values.
            strict: Whether mkforge must require an exact YAML key set.

        Returns:
            True when mkforge validates the expected YAML front matter.
        """
        return mkforge.validate_markdown_yaml(
            self.content,
            expected,
            strict=strict,
        )
