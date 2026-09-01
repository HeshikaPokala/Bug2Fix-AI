from __future__ import annotations


def validate_username(username: str) -> str:
    # Intentional bug: raises a bare, unhandled ValueError for an overlong
    # username instead of rejecting the signup request cleanly.
    if len(username) > 20:
        raise ValueError("username exceeds maximum length of 20")
    return username
