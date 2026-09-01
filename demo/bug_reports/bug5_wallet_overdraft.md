Title: Wallet withdrawal crashes when amount exceeds overdraft limit

Description:
When a customer requests a withdrawal larger than their balance plus the $50 overdraft allowance, the wallet service throws a runtime exception and returns HTTP 500 instead of a clean decline response.

Expected behavior:
The endpoint should return a 402 "insufficient funds" response, not crash.

Actual behavior:
The endpoint throws an exception and the withdrawal request fails ungracefully.

Environment:
- Python 3.11
- macOS
- Service version: 2.0.1

Reproduction hints:
- Trigger `/wallet/withdraw` for an account with balance $100 requesting a $200 withdrawal (exceeds the $50 overdraft limit).
