# Production integration (NextGen API host)

The public NextGen website serves the GrowthAudit dashboard as static HTML, CSS
and JavaScript, but `/growth-audit-api` cannot execute Python when the
production build publishes Python source as a static file. Frontend returning
HTTP 200 is *not* evidence of working scans.

## Recommended deployment for the existing NextGen architecture

1. Install a reviewed copy of `rajachanna/GrowthAudit-Pro` alongside the
   existing FastAPI backend. Keep the scanner's public URL/DNS pinning and
   `robots.txt` checks intact.
2. In the existing backend process, import the integration router from
   `integrations.nextgen_fastapi` and call `app.include_router(router)`.
   Do not expose the local developer server directly to the internet.
3. In the production web app `vercel.json`, change the *existing* first
   `/growth-audit-api` rewrite to the same-origin proxy destination:
   `https://api.nextgentechdev.com/api/growth-audit`. Preserve all other
   API rewrites. This keeps the frontend JS URL and all other services unchanged.
4. Verify the upstream `/api/growth-audit` GET responds with a JSON service
   contract and POST of `{"url":"http://127.0.0.1/"}` rejects with HTTP 400
   **without fetching anything**. Then verify a real allowed public website
   produces exactly 17 evidence-based findings.
5. Run `python3 scripts/check_live_growth_audit.py` to verify the production
   dashboard and same-origin proxy. Never declare the deployment ready until
   this passes.

This is a deliberately limited, robots-respecting single-page public audit.
Set Cloudflare/edge rate limiting and monitor CPU, requests and errors before
marketing at scale. The in-process 20 requests/minute limiter is not
distributed and the scanner has no queue. Do not promise Search Console,
Core Web Vitals or Google rankings without separate measured integrations.
