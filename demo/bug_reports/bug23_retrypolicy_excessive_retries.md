Title: Retry policy config crashes on an unreasonable retry count

Description:
When an operator submits a retry-policy config change with an unreasonably high retry count, the config service throws a runtime exception instead of rejecting the change.

Expected behavior:
The endpoint should return a 400 response for an unreasonable retry count, not crash.

Actual behavior:
The endpoint throws an exception and the config change fails ungracefully.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/config/retry-policy` with `{"n": 50}`, well above the sane maximum of 10.
