Title: Trip telemetry crashes on zero-duration GPS readings

Description:
When a GPS device reports a trip segment with zero elapsed hours (a known device glitch), the telemetry service throws a runtime exception instead of skipping the segment.

Expected behavior:
The service should return 0 average speed for a zero-duration segment, not crash.

Actual behavior:
The service throws an exception and the telemetry batch job fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger the telemetry batch job with a trip segment where `hours=0`.
