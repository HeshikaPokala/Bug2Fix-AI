from __future__ import annotations


def get_user_permission(permissions: dict[str, list[str]], role: str) -> list[str]:
    # Intentional bug: crashes with KeyError for a role not in the permission
    # map instead of denying access cleanly.
    return permissions[role]
