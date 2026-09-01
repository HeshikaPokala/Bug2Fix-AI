from __future__ import annotations


def get_feature_flag(flags: dict[str, bool], flag_name: str) -> bool:
    # Intentional bug: crashes with KeyError for a flag name that was never
    # registered instead of defaulting to off.
    return flags[flag_name]
