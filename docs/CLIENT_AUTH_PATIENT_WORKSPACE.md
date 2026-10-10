# Client Authentication and Patient Workspace

The client now has an authenticated session and a first real clinical workspace.

- Uses `POST /api/v1/auth/login`.
- Keeps the bearer token in `sessionStorage` for the current client session.
- Clears the token on HTTP 401 and returns to sign-in.
- Uses `GET /api/v1/patients` for patient search/listing.
- Uses the stable WebView2 origin `https://app.hhms.local` instead of `file://`.
- Patient detail and clinical module screens remain later milestones.
