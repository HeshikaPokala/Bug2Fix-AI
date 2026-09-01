Title: Profile page crashes when user record is missing

Description:
When the profile service is asked to render a display name for a user ID that has no matching record (e.g. a deleted account), it throws a runtime exception and returns HTTP 500 instead of showing a placeholder.

Expected behavior:
The endpoint should show a placeholder name (e.g. "Deleted User") when no user record is found.

Actual behavior:
The endpoint throws an exception and fails the request.

Environment:
- Python 3.11
- macOS
- Service version: 2.1.0

Reproduction hints:
- Trigger `/profile/render` for a user ID with no matching database record (lookup returns null).
