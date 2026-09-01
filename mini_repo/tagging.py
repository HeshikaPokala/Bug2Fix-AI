from __future__ import annotations


def first_tag(tags: list[str]) -> str:
    # Intentional bug: crashes when a post has no tags instead of returning
    # a default category.
    return tags[0]
