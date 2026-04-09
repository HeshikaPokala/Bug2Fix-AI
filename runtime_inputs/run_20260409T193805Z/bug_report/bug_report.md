Title: Batch Processing API crashes for empty payload

Description:
When processing requests with an empty list of values, the service throws a runtime exception and returns HTTP 500.

Expected behavior:
The endpoint should return a valid response and gracefully handle empty lists.

Actual behavior:
The endpoint throws an exception and fails the request.

Environment:
- Python 3.11
- macOS
- Service version: 1.4.2

Reproduction hints:
- Trigger `/process` endpoint with `{"values": []}` payload.
