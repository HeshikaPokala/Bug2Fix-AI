Title: Ticket triage crashes on out-of-range priority level

Description:
When an upstream integration sends a priority level outside the valid 0-3 range (a known bug in a partner's webhook payload), the ticket triage service throws a runtime exception instead of defaulting to low priority.

Expected behavior:
The service should default to "low" priority for an out-of-range value, not crash.

Actual behavior:
The service throws an exception and the ticket fails to import.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger the ticket import webhook with `level=7` (outside the valid 0-3 range).
