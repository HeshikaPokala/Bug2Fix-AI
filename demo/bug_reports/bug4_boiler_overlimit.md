Title: Boiler control API crashes on over-limit temperature request

Description:
When a technician sends a temperature setpoint above the safe boiler limit, the control service throws a runtime exception and returns HTTP 500 instead of rejecting the request cleanly.

Expected behavior:
The endpoint should return a 400 "unsafe temperature" response, not crash.

Actual behavior:
The endpoint throws an exception and the control request fails ungracefully.

Environment:
- Python 3.11
- macOS
- Service version: 2.0.1

Reproduction hints:
- Trigger `/boiler/set` with `{"celsius": 150}`, well above the 100C safety limit.
