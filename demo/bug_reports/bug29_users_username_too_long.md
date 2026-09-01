Title: Signup crashes on an overlong username

Description:
When a signup request includes a username longer than 20 characters, the signup service throws a runtime exception instead of rejecting the request cleanly.

Expected behavior:
The endpoint should return a 400 response for an overlong username, not crash.

Actual behavior:
The endpoint throws an exception and the signup request fails ungracefully.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/signup` with a username longer than 20 characters (e.g. copy-pasted from a display name field).
