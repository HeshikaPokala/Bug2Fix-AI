from __future__ import annotations


def first_active_user(users: list[dict]) -> dict:
    # Intentional bug for the second demo scenario: raises IndexError when no
    # user in the list is active.
    active = [u for u in users if u.get("active")]
    return active[0]
