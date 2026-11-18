import unittest
import json
from growthaudit.fetch import FetchResult,FetchError
from growthaudit.engine import run_audit, report_json, report_markdown
from growthaudit.security import UnsafeTarget

def response(url,status=200,body=b"",content_type="text/plain",headers=None):
    return FetchResult(url,status,content_type,body,headers or {},75,0)

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.calls=[]
    def mock(self,url,**kw):
        self.calls.append(url)
        if url.endswith("/robots.txt"):
            return response(url,body=b"User-agent: *\nAllow: /\n")
        if url.endswith("/sitemap.xml"):
            return response(url,body=b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>',content_type="application/xml")
        return response(url,body=b"<html lang='en'><head><title>A useful title for a demo website</title></head><body><h1>Welcome</h1></body></html>",
                        content_type="text/html; charset=utf-8",headers={"x-content-type-options":"nosniff"})
    def test_successful_run_has_real_source(self):
        report=run_audit("https://www.example.com",fetcher=self.mock)
        self.assertEqual(report["network"]["http_status"],200)
        self.assertEqual(report["request"]["entered_url"],"https://www.example.com/")
        self.assertEqual(report["discovery"]["robots"],"found")
        self.assertEqual(report["discovery"]["sitemap"],"found")
        self.assertEqual(len(self.calls),3)
    def test_robots_disallow_blocks_before_fetching_target(self):
        def restricted(url,**kwargs):
            self.calls.append(url)
            if url.endswith("robots.txt"):
                return response(url,body=b"User-agent: GrowthAuditPro\nDisallow: /\n")
            raise AssertionError("Should not touch blocked pages")
        with self.assertRaises(PermissionError):run_audit("https://www.example.com/private",fetcher=restricted)
        self.assertEqual(len(self.calls),1)
    def test_robots_403_blocks(self):
        def restricted(url,**kwargs):return response(url,status=403)
        with self.assertRaises(PermissionError):run_audit("example.com",fetcher=restricted)
    def test_robots_unavailable_fails_closed(self):
        def fail(url,**kwargs):raise FetchError("connection failed")
        with self.assertRaises(FetchError):run_audit("example.com",fetcher=fail)
    def test_missing_robots_is_not_fake_pass(self):
        def mock(url,**kwargs):
            if url.endswith("robots.txt"):return response(url,status=404)
            return self.mock(url,**kwargs)
        result=run_audit("www.example.com",fetcher=mock)
        self.assertEqual(result["discovery"]["robots"],"missing")
        self.assertFalse(next(f["passed"] for f in result["findings"] if f["id"]=="DISC-01"))
    def test_non_html_rejected(self):
        def binary(url,**kwargs):
            if url.endswith("robots.txt"):return response(url,body=b"User-agent: *\nAllow: /")
            return response(url,body=b"%PDF",content_type="application/pdf")
        with self.assertRaises(FetchError):run_audit("example.com",fetcher=binary)
    def test_page_404_rejected(self):
        def bad(url,**kw):
            if url.endswith("robots.txt"):return response(url,status=404)
            return response(url,status=404)
        with self.assertRaises(FetchError):run_audit("example.com",fetcher=bad)
    def test_different_final_domain_not_audited(self):
        def different(url,**kw):
            if url.endswith("robots.txt"):return response(url,body=b"User-agent: *\nAllow: /")
            return response("https://other.example.com/",body=b"<html/>",content_type="text/html")
        with self.assertRaises(FetchError):run_audit("example.com",fetcher=different)
    def test_invalid_sitemap_not_reported_as_found(self):
        def invalid(url,**kw):
            if url.endswith("sitemap.xml"):return response(url,body=b"<html>not a sitemap</html>",content_type="text/html")
            return self.mock(url,**kw)
        report=run_audit("example.com",fetcher=invalid)
        self.assertEqual(report["discovery"]["sitemap"],"not XML sitemap")
    def test_proper_json_report(self):
        r=run_audit("www.example.com",fetcher=self.mock)
        self.assertEqual(json.loads(report_json(r))["tool"],"GrowthAudit Pro")
    def test_markdown_reports_limitations(self):
        r=run_audit("www.example.com",fetcher=self.mock)
        self.assertIn("## Limitations",report_markdown(r))
        self.assertIn("Google",report_markdown(r))
    def test_rejects_private_domain_early(self):
        with self.assertRaises(UnsafeTarget):run_audit("http://127.0.0.1",fetcher=self.mock)
        self.assertEqual(self.calls,[])
    def test_result_records_small_page(self):
        r=run_audit("https://www.example.com",fetcher=self.mock)
        self.assertLess(r["network"]["bytes_downloaded"],1000)

if __name__=="__main__":unittest.main()
