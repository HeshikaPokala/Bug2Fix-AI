Title: HVAC control crashes on over-limit fan speed request

Description:
When a technician sends a fan speed setpoint above 100%, the HVAC control service throws a runtime exception and returns HTTP 500 instead of rejecting it cleanly.

Expected behavior:
The endpoint should return a 400 response for an out-of-range fan speed, not crash.

Actual behavior:
The endpoint throws an exception and the control request fails ungracefully.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/hvac/fan/set` with `{"percent": 140}`, above the 100% maximum.
