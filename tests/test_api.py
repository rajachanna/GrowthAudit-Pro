import unittest
import json
from growthaudit.serverless import handle_request,_RECENT,respond,allow_scan
from growthaudit.security import UnsafeTarget
from growthaudit.fetch import FetchError

def engine(url):
    return {"url":url,"findings":[],"summary":{"passed":0,"failed":0,"high_priority":0}}

class APITests(unittest.TestCase):
    def setUp(self):_RECENT.clear()
    def test_health(self):
        status,data=handle_request("GET","/api/growth-audit/health")
        self.assertEqual(status,200)
        self.assertTrue(json.loads(data)["ok"])
    def test_ready(self):
        status,data=handle_request("GET","/api/growth-audit")
        self.assertEqual(status,200)
    def test_invalid_json(self):
        status,data=handle_request("POST","/api/growth-audit",b"{")
        self.assertEqual(status,400)
    def test_missing_url(self):
        status,data=handle_request("POST","/api/growth-audit",b"{}")
        self.assertEqual(status,400)
    def test_non_string_url(self):
        status,data=handle_request("POST","/api/growth-audit",b'{"url":42}')
        self.assertEqual(status,400)
    def test_payload_limit(self):
        status,data=handle_request("POST","/api/growth-audit",b"a"*5000)
        self.assertEqual(status,413)
    def test_success_no_outbound_on_mock(self):
        status,data=handle_request("POST","/api/growth-audit",b'{"url":"https://www.example.com"}',engine=engine)
        self.assertEqual(status,200)
        self.assertEqual(json.loads(data)["url"],"https://www.example.com")
    def test_unsafe_url_rejected(self):
        status,data=handle_request("POST","/api/growth-audit",b'{"url":"http://127.0.0.1"}',
                                  engine=lambda _:(_ for _ in ()).throw(UnsafeTarget("Not public")))
        self.assertEqual(status,400)
    def test_fetch_error_rejected(self):
        status,data=handle_request("POST","/api/growth-audit",b'{"url":"example.com"}',
                                  engine=lambda _:(_ for _ in ()).throw(FetchError("bad response")))
        self.assertEqual(status,422)
    def test_no_stack_trace_in_unexpected_error(self):
        status,data=handle_request("POST","/api/growth-audit",b'{"url":"example.com"}',
                                  engine=lambda _:(_ for _ in ()).throw(RuntimeError("private api key")))
        self.assertEqual(status,502)
        self.assertNotIn(b"private api key",data)
    def test_rate_limit(self):
        for _ in range(20):
            self.assertTrue(allow_scan(now=500))
        self.assertFalse(allow_scan(now=500))
        self.assertTrue(allow_scan(now=561))
    def test_no_cors_opt_in(self):
        status,data=handle_request("OPTIONS","/api/growth-audit")
        self.assertEqual(status,405)
    def test_json_response(self):
        s,b=respond({"x":"unicode ✓"})
        self.assertEqual(s,200)
        self.assertTrue(b.startswith(b"{"))

if __name__=="__main__":unittest.main()
