from __future__ import annotations


def get_display_name(user: dict) -> str:
    # Intentional bug: crashes when user is None instead of falling back to a
    # placeholder display name.
    return user["first_name"] + " " + user["last_name"]
