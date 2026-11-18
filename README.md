# GrowthAudit Pro

**Free public website technical review studio** — powered by real HTML fetches and explainable checks.

[![CI](https://github.com/rajachanna/GrowthAudit-Pro/actions/workflows/ci.yml/badge.svg)](https://github.com/rajachanna/GrowthAudit-Pro/actions/workflows/ci.yml)

Public dashboard: **https://www.nextgentechdev.com/growth-audit** (scanner API deployment currently **not healthy**; see status below).

[NextGen Tech Solutions](https://www.nextgentechdev.com/) · [Security model](SECURITY.md) · [Engineering case study](docs/CASE_STUDY.md)

## Production status (verified 2026-11-18 UTC)

The live `/growth-audit` page, JS and CSS return HTTP 200. The production
`/growth-audit-api` scanner endpoint returns **HTTP 404**, so the free scan
button **does not currently work end-to-end**. A direct request to the Python
source path returned a static octet-stream response instead of running a
serverless handler; this points to production routing/build/runtime configuration
or a deployment ownership mismatch, **not** a passing API deployment.
The original code and regression test suite pass CI, but that is not production proof.

The [production contract workflow](.github/workflows/production-contract.yml)
tests the public frontend, API JSON contract and loopback-target rejection on
every push and daily. It currently fails intentionally while the API is broken;
the workflow is a detector, **not** a substitute for fixing the deployment.

The repo includes a [standalone Vercel config](vercel.json) that maps static
assets and Python serverless routes. A request to create a separate Vercel
project under team `raja-8b55` was denied with **403 Forbidden** by the
connected Vercel account. No separate deployment was created. The public
NextGen website may be owned by another Vercel account; confirm the actual
production project's build settings before changing its routing.

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
