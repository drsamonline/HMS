# Audit / Activity

Every change is recorded with who, what, before, after and a request id. The trail
is append-only and hash-chained, which means a change made outside the application is
detectable.

The nightly verifier checks the chain. A break in it is not a display problem; it
means the trail was altered, and that is an incident rather than a support call.

Reading the trail is not surveillance of staff. It is what lets a hospital answer an
assessor, and what makes "I did not do that" a claim the system can check.
