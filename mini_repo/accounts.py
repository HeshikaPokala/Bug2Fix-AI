from __future__ import annotations


def get_account_email(account: dict) -> str:
    # Intentional bug: crashes when account is an empty/unknown record instead
    # of returning a placeholder.
    return account["email"]
