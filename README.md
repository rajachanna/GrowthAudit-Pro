# GrowthAudit Pro

**Free public website technical review studio** — powered by real HTML fetches and explainable checks.

[![CI](https://github.com/rajachanna/GrowthAudit-Pro/actions/workflows/ci.yml/badge.svg)](https://github.com/rajachanna/GrowthAudit-Pro/actions/workflows/ci.yml)

Live tool: **https://www.nextgentechdev.com/growth-audit**

[NextGen Tech Solutions](https://www.nextgentechdev.com/) · [Security model](SECURITY.md) · [Engineering case study](docs/CASE_STUDY.md) · [Integration notes](docs/PRODUCTION-INTEGRATION.md)

## Production status (verified 2026-11-19 UTC)

**The live audit API is working.** The public dashboard, CSS and JavaScript all
returned HTTP 200. The live `/growth-audit-api` endpoint returned its JSON
service contract and rejected a loopback IP target with HTTP 400. A real POST
to `https://www.python.org/` returned HTTP 200 and **17 measured HTML/HTTP
check findings**, with six items for review in that one run. The site's main
backend `/health` also remained healthy after the integration.

### What fixed the outage

The earlier production Vercel configuration served the Python source as a
static file instead of executing the function. The scanner was mounted in
the existing, already-running NextGen FastAPI backend on the user's Oracle
server using [`integrations/nextgen_fastapi.py`](integrations/nextgen_fastapi.py).
The public website's `/growth-audit-api` rewrite now forwards requests to
`https://api.nextgentechdev.com/api/growth-audit`, preserving the same-origin
browser API, the other NextGen routes and the report-download UI.

The [production contract workflow](.github/workflows/production-contract.yml)
checks the live frontend, script/styles, JSON API and blocked-target rejection
on every push and daily. Monitoring is not a guarantee of uninterrupted uptime;
keep the upstream rate limiter and Cloudflare security protections enabled.

**Repository ownership:** GrowthAudit Pro source and tests are maintained
here under `rajachanna/GrowthAudit-Pro`. The deployed NextGen public website
currently has a separate integration repository; migrate that website to
Raja's account separately when deployment ownership and DNS are coordinated.
Do not confuse Vercel source publication with a standalone GrowthAudit deployment
(the connected Vercel account denied standalone project creation with 403).

## What is implemented

- Real, bounded server-side retrieval of one public HTTP(S) HTML page after reading robots.txt.
- A public-domain SSRF prevention policy, DNS-to-socket IP pinning and HTTPS certificate verification.
- Bounded, independently validated redirects; cross-host redirects ask for final URL before continuing.
- Lightweight inspection of robots.txt, sitemap.xml, HTTP headers and the supplied HTML document.
- **17 concrete checks** covering: SEO title/description, noindex, H1, canonical, internal links, JSON-LD syntax, mobile viewport, language, image alt, form control clues, conversion CTA, HTTPS, nosniff, CSP, robots instructions, XML sitemap.
- Each result includes observed evidence, severity, recommendation, category, passed/failed state and checklist weight.
- A **transparent weighted technical checklist score**; no unsupported Google ranking, PageSpeed, Core Web Vitals or AI visibility score.
- Professional responsive browser dashboard, filtered findings and free JSON / Markdown / Print-to-PDF report.
- Consent-first website inquiry handoff, with user review before submission.
- CLI, same-origin HTTP API, Vercel-compatible Python adapter, local development server and regression tests.
- Website performance and CrUX metrics are **not measured** by this release. [Google PageSpeed Insights](https://pagespeed.web.dev/) provides actual performance audits.

## Run locally

Python 3.10+, Node only for optional JS syntax checks. No third-party Python packages:

```bash
git clone https://github.com/rajachanna/GrowthAudit-Pro.git
cd GrowthAudit-Pro
python -m growthaudit.devserver
```

Open http://127.0.0.1:8769/growth-audit. For a single CLI report:

```bash
python -m growthaudit https://www.python.org/ --format markdown
python -m growthaudit https://www.python.org/ --format json --output website-report.json
```

Scanner can fail closed when robots.txt or the site blocks bots. Cross-host redirects (e.g. apex to www) require entering the final hostname. Real sites can restrict data-center IP ranges.

## Local API

```bash
curl -sS http://127.0.0.1:8769/api/growth-audit/health
curl -sS -X POST http://127.0.0.1:8769/api/growth-audit -H 'Content-Type: application/json' -d '{"url":"https://www.python.org/"}'
```

The JSON API returns one report with `findings`, `network`, `discovery`, `page`, `summary`, and `measurements` (performance is `null` because not measured).

## Production Vercel architecture

Static HTML/CSS/JS is served from NextGen Tech Solutions production website. `api/growth-audit.py` maps to a Python serverless function; the host's `vercel.json` **must route `/api/growth-audit` to this function before its catch-all API proxy**.

Important operational controls: configure Vercel WAF/distributed throttling, set network request limits and monitor the function logs. The built-in per-process limiter is not distributed. Do not claim the online API works until a real production response has been verified.

## Architecture

```text
growthaudit/
  security.py    public URL policy, DNS filtering
  fetch.py       pinned-socket HTTP + TLS, response budgets and redirects
  htmlcheck.py   HTML parser and 17 weighted evidence checks
  engine.py      robots permissions, bounded scan orchestration, reports
  serverless.py  Python HTTP handler with safe responses and local throttle
  devserver.py   local same-origin UI/API development server
  cli.py         offline CLI for public URL reports
api/
  growth-audit.py  Vercel Python function adapter
web/
  index.html, styles.css, app.js
tests/
  69+ network-independent regression tests
```

## Correctness and limitations

A website can score 100/100 on our 17-item checklist and still have slow speed, weak content, poor rankings, broken interactions or zero paying customers. No real Core Web Vitals, Google search performance, conversions, security certification or full accessibility audit is claimed.

## License
MIT © 2026 NextGen Tech Solutions.
