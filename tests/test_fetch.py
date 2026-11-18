import unittest
from unittest.mock import patch
from growthaudit import fetch
from growthaudit.fetch import FetchError,fetch_public
from growthaudit.security import UnsafeTarget

class FakeResponse:
    def __init__(self,status=200,body=b"hello",headers=None):
        self.status=status;self._body=body;self._headers=headers or [("Content-Type","text/html")]
    def getheaders(self):return self._headers
    def read(self,n):return self._body[:n]

class FakeConn:
    responses=[]
    calls=[]
    def __init__(self,target,ip,timeout):
        self.target=target
    def request(self,method,path,headers):
        FakeConn.calls.append((self.target.url,method,path,headers))
    def getresponse(self):return FakeConn.responses.pop(0)
    def close(self):pass

class FetchTests(unittest.TestCase):
    def setUp(self):
        FakeConn.responses=[];FakeConn.calls=[]
        patcher1=patch.object(fetch,"public_ips",lambda host,port,resolver=None:["93.184.216.34"])
        patcher2=patch.object(fetch,"PinnedHTTPSConnection",FakeConn)
        patcher3=patch.object(fetch,"PinnedHTTPConnection",FakeConn)
        for p in (patcher1,patcher2,patcher3):
            p.start();self.addCleanup(p.stop)
    def test_valid_fetch(self):
        FakeConn.responses=[FakeResponse(200,b"<html/>")]
        result=fetch_public("https://www.example.com/")
        self.assertEqual(result.status,200)
        self.assertEqual(result.body,b"<html/>")
        self.assertEqual(FakeConn.calls[0][1],"GET")
        self.assertNotIn("Cookie",FakeConn.calls[0][3])
    def test_redirect_same_host(self):
        FakeConn.responses=[
            FakeResponse(301,b"",[("Location","/new")]),
            FakeResponse(200,b"ok")
        ]
        result=fetch_public("https://www.example.com/old")
        self.assertEqual(result.redirects,1)
        self.assertEqual(result.url,"https://www.example.com/new")
    def test_redirect_to_metadata_blocked_before_request(self):
        FakeConn.responses=[FakeResponse(302,b"",[("Location","http://169.254.169.254/latest")])]
        with self.assertRaises(UnsafeTarget):fetch_public("https://www.example.com/")
        self.assertEqual(len(FakeConn.calls),1)
    def test_redirect_cross_host_blocked_before_request(self):
        FakeConn.responses=[FakeResponse(302,b"",[("Location","https://other.example.com")])]
        with self.assertRaises(FetchError):fetch_public("https://www.example.com/")
        self.assertEqual(len(FakeConn.calls),1)
    def test_redirect_limit(self):
        FakeConn.responses=[
            FakeResponse(302,b"",[("Location","/a")]),
            FakeResponse(302,b"",[("Location","/b")])
        ]
        with self.assertRaises(FetchError):
            fetch_public("www.example.com",max_redirects=1)
    def test_max_response_bytes(self):
        FakeConn.responses=[FakeResponse(200,b"x"*105)]
        with self.assertRaises(FetchError):
            fetch_public("www.example.com",max_bytes=100)
    def test_content_length_preflight(self):
        FakeConn.responses=[FakeResponse(200,b"",[("Content-Length","9999999")])]
        with self.assertRaises(FetchError):fetch_public("www.example.com")
    def test_url_policy_before_dns(self):
        with self.assertRaises(UnsafeTarget):fetch_public("http://localhost")
        self.assertEqual(len(FakeConn.calls),0)
    def test_port_injection_in_redirect(self):
        FakeConn.responses=[FakeResponse(301,b"",[("Location","https://www.example.com:9999/test")])]
        with self.assertRaises(UnsafeTarget):fetch_public("www.example.com")
    def test_request_contains_only_safe_fixed_headers(self):
        FakeConn.responses=[FakeResponse()]
        fetch_public("https://www.example.com/")
        _,method,path,headers=FakeConn.calls[0]
        self.assertEqual(headers["Host"],"www.example.com")
        self.assertEqual(headers["Connection"],"close")
        self.assertEqual(headers["Accept-Encoding"],"identity")

if __name__=="__main__":unittest.main()
