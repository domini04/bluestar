"""
CLI progress utilities.

Provides a safe status context manager that uses Rich when console output is
enabled and a TTY is present; otherwise, it becomes a no-op.
"""

from contextlib import contextmanager
import sys
from typing import Iterator

from ..config import config


@contextmanager
def status(message: str) -> Iterator[None]:
    """Show a status spinner in CLI mode; no-op in non-interactive contexts."""
    use_rich = bool(config.console_output) and sys.stdout.isatty()
    if not use_rich:
        # No-op context
        yield
        return

    try:
        from rich.console import Console
        console = Console()
        with console.status(message):
            yield
    except Exception:
        # Fallback to no-op if Rich is unavailable or any error occurs
        yield


