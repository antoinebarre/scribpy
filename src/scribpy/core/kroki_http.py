"""Shared HTTP transport for Kroki diagram rendering."""

from __future__ import annotations

import logging
from http.client import HTTPSConnection
from urllib.error import HTTPError, URLError

from scribpy.core.diagram_encoding import encode_diagram

_HTTP_OK = 200
_REQUEST_TIMEOUT = 30
_USER_AGENT = "Scribpy/0.1 (+https://github.com/example/scribpy)"

_log = logging.getLogger(__name__)


def kroki_render(
    language: str,
    diagram: str,
    error_cls: type[Exception],
) -> bytes:
    """Render a diagram through Kroki's encoded GET endpoint.

    Args:
        language: Kroki diagram language path segment.
        diagram: Diagram source without fenced code delimiters.
        error_cls: Domain exception type raised for transport failures.

    Returns:
        Rendered PNG bytes.

    Raises:
        Exception: The supplied domain exception when Kroki fails.
    """
    encoded = encode_diagram(diagram)
    path = f"/{language}/png/{encoded}"
    _log.debug("%s render request: https://kroki.io%s", language, path)
    connection: HTTPSConnection | None = None
    data: bytes
    try:
        connection = HTTPSConnection("kroki.io", timeout=_REQUEST_TIMEOUT)
        connection.request(
            "GET",
            path,
            headers={"User-Agent": _USER_AGENT},
        )
        response = connection.getresponse()
        data = response.read()
        if response.status != _HTTP_OK:
            detail = data.decode("utf-8", errors="replace").strip()
            reason = detail or response.reason
            msg = f"Kroki returned HTTP {response.status}: {reason}"
            _log.error("%s render failed: %s", language, msg)
            raise error_cls(msg)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        msg = f"Kroki returned HTTP {exc.code}: {detail or exc.reason}"
        _log.error("%s render error: %s", language, msg)
        raise error_cls(msg) from exc
    except URLError as exc:
        msg = f"Kroki request failed: {exc.reason}"
        _log.error("%s render error: %s", language, exc.reason)
        raise error_cls(msg) from exc
    finally:
        if connection is not None:
            connection.close()
    _log.info("%s render OK (%d bytes)", language, len(data))
    return data
