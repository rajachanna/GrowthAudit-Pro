# Security scope and responsible usage

GrowthAudit Pro is designed to scan **public pages only**, not internal services.

## Implemented protections
- The scan accepts only HTTP or HTTPS and requires public domain names.
- Credentials, IP literals, internal/reserved hostnames and unusual ports are blocked.
- DNS answers are checked for global IPs; mixed public/private results are rejected.
- The HTTP client **pins the validated IP to the socket connection**, including TLS hostname verification.
- Redirects are bounded and revalidated. Redirects to another hostname are not fetched; instead the visitor can resubmit the final URL so its robots policy is evaluated.
- A user-supplied HTTP proxy or arbitrary custom headers cannot be supplied.
- Connection timeouts and downloaded content budgets are bounded.
- robots.txt is checked before fetching a target page; if access rules are unavailable, the scan fails closed.
- Public API accepts only a short JSON request, has a best-effort per-process rate limit, hides internal exception text and does not enable cross-origin requests.
- Website content is parsed as text; UI uses textContent to prevent reflected HTML injection in findings.
- No source code is uploaded or executed, and no website passwords are accepted.

## Gaps requiring production controls
- The in-memory rate limiter is **not shared across Vercel serverless instances**. Configure Vercel WAF/rate controls or persistent distributed quotas before high-traffic/paid use.
- Hostname-based policy cannot fully protect against every exotic DNS or redirect edge case; review SSRF defenses regularly.
- This is a **single-page limited audit**, not a full security, accessibility, SEO or performance assessment.
- Standard web logs may capture requested target domains; do not scan confidential or private URLs.

## Responsible use
Only scan a website when you have authorization or the website permits public crawling under applicable terms. The tool does not ignore robots restrictions or log into accounts.

Security reports can be filed through GitHub's private vulnerability reporting when enabled. Do not put passwords, personal details or customer private content in public issues.
