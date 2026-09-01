from __future__ import annotations


def set_max_retries(n: int) -> str:
    # Intentional bug: raises a bare, unhandled ValueError for an unreasonable
    # retry count instead of rejecting the config change cleanly.
    if n > 10:
        raise ValueError(f"retry count {n} is unreasonably high")
    return f"max retries set to {n}"
