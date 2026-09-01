Title: Seat booking crashes when requested seats exceed availability

Description:
When a group booking requests more seats than are available on a flight, the booking service throws a runtime exception instead of offering a waitlist.

Expected behavior:
The endpoint should offer a waitlist response when overbooked, not crash.

Actual behavior:
The endpoint throws an exception and the booking request fails ungracefully.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/booking/reserve` for a flight with `available_seats=5` and a request for `requested_seats=12`.
