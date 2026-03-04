import time


def now_sec() -> float:
    """Monotonic simulation clock."""
    return time.monotonic()
