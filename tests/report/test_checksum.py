"""Tests for file checksum utilities."""

from __future__ import annotations

import hashlib

import pytest

from scribpy.report.checksum import file_checksum


class TestFileChecksum:
    def test_sha256_default(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_bytes(b"hello")
        result = file_checksum(f)
        expected = hashlib.sha256(b"hello").hexdigest()
        assert result == expected

    def test_md5(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_bytes(b"test")
        result = file_checksum(f, algorithm="md5")
        expected = hashlib.md5(b"test").hexdigest()
        assert result == expected

    def test_sha1(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_bytes(b"abc")
        result = file_checksum(f, algorithm="sha1")
        expected = hashlib.sha1(b"abc").hexdigest()
        assert result == expected

    def test_sha512(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_bytes(b"xyz")
        result = file_checksum(f, algorithm="sha512")
        expected = hashlib.sha512(b"xyz").hexdigest()
        assert result == expected

    def test_accepts_string_path(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_bytes(b"hi")
        result = file_checksum(str(f))
        assert len(result) == 64

    def test_returns_hex_string(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(bytes(range(256)))
        result = file_checksum(f)
        assert all(c in "0123456789abcdef" for c in result)

    def test_invalid_algorithm_raises(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_bytes(b"x")
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            file_checksum(f, algorithm="crc32")  # type: ignore[arg-type]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            file_checksum(tmp_path / "nonexistent.txt")
