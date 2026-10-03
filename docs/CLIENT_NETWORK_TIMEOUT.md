# Client Network Timeout

Batch 25 adds bounded HTTP request timeouts to the HHMS client. Requests default to 15 seconds and use `AbortController`.

A timeout emits `hhms:request-timeout`, updates the client connection state, and shows a retryable connection message. It does not silently discard the current form or clear the authenticated session.

The timeout can be overridden per request with `timeoutMs` when a future operation legitimately needs a different budget.
