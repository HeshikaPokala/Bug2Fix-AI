Title: Active user lookup crashes when no users are active

Description:
When a request for the "first active user" endpoint is made and no users in the payload are marked active, the service throws a runtime exception and returns HTTP 500.

Expected behavior:
The endpoint should return a valid response (e.g. null / 404) when no active users exist.

Actual behavior:
The endpoint throws an exception and fails the request.

Environment:
- Python 3.11
- macOS
- Service version: 1.4.2

Reproduction hints:
- Trigger `/users/active` endpoint with a payload where every user has `"active": false`.
