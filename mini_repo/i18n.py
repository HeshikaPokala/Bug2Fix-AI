from __future__ import annotations


def get_translation(translations: dict[str, str], locale: str) -> str:
    # Intentional bug: crashes with KeyError for an unsupported locale instead
    # of falling back to English.
    return translations[locale]
