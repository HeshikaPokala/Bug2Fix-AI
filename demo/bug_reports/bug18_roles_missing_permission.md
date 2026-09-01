Title: Access control crashes for a role not in the permission map

Description:
When a request comes in for a role that isn't yet registered in the permission map (e.g. a newly introduced 'viewer' role), the access-control service throws a runtime exception instead of denying access.

Expected behavior:
The endpoint should deny access cleanly (403) for an unrecognized role, not crash.

Actual behavior:
The endpoint throws an exception and returns HTTP 500.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/access/check` for role `"viewer"`, which isn't yet in the permission map (`{"admin": [...], "editor": [...]}`).
