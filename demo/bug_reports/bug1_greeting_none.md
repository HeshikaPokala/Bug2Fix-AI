Title: Greeting API crashes when username is missing

Description:
When a request omits the "name" field (sent as null), the greeting service throws a runtime exception and returns HTTP 500.

Expected behavior:
The endpoint should return a generic greeting (e.g. "Hello there!") when no name is provided.

Actual behavior:
The endpoint throws an exception and fails the request.

Environment:
- Python 3.11
- macOS
- Service version: 2.0.1

Reproduction hints:
- Trigger `/greet` endpoint with `{"name": null}` payload.
