Title: Scheduler crashes on out-of-range day index from calendar sync

Description:
When the third-party calendar sync sends a day-of-week index outside the valid 0-6 range (a known bug in their API during daylight-saving transitions), the scheduler service throws a runtime exception instead of skipping the malformed entry.

Expected behavior:
The service should skip / reject malformed day indices with a clear validation error, not crash.

Actual behavior:
The service throws an exception and the whole sync batch fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.1.0

Reproduction hints:
- Trigger the calendar sync job with a day index of 9 (outside the valid Mon-Sun 0-6 range), which the third-party API is known to send during DST transitions.
