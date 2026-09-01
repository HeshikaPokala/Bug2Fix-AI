Title: Post categorization crashes for untagged posts

Description:
When the content service tries to derive a primary category from a post's first tag, it throws a runtime exception for posts with zero tags instead of using a default category.

Expected behavior:
The endpoint should fall back to a default category (e.g. "uncategorized") when there are no tags.

Actual behavior:
The endpoint throws an exception and fails the request.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/posts/categorize` for a post with an empty `tags` list.
