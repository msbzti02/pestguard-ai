"""
Retry Decorator — core/retry.py
=================================
Provides a configurable exponential-backoff retry decorator for
external API calls (LLM, weather, VLM).

Usage:
    from core.retry import retry_with_backoff

    @retry_with_backoff(max_attempts=3, base_delay=1.0, exceptions=(Exception,))
    def call_external_api():
        ...
"""

import time
import functools
from typing import Tuple, Type

from core.logger import get_logger

log = get_logger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    label: str = "",
):
    """
    Exponential-backoff retry decorator.

    Args:
        max_attempts:   Total number of tries (including the first).
        base_delay:     Seconds to wait before the second attempt.
        backoff_factor: Multiplier applied to the delay after each failure.
        exceptions:     Exception types that trigger a retry.
        label:          Human-readable label shown in log messages.

    Delays: 1 s → 2 s → 4 s (with defaults)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tag = label or func.__name__
            delay = base_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        log.error(
                            f"[{tag}] All {max_attempts} attempts failed. "
                            f"Last error: {exc}"
                        )
                        raise
                    log.warning(
                        f"[{tag}] Attempt {attempt}/{max_attempts} failed: {exc}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

        return wrapper
    return decorator
