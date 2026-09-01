Title: Late fee job crashes on severely overdue accounts

Description:
When the late-fee batch job processes an account overdue by more than 90 days, it throws a runtime exception instead of routing it to the collections workflow.

Expected behavior:
The job should route accounts overdue beyond 90 days to collections, not crash.

Actual behavior:
The job throws an exception and the whole late-fee batch fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger the late-fee batch job for an account with `days_overdue=120`.
