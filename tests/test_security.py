import unittest
import socket
from growthaudit.security import normalize_url,public_ips,UnsafeTarget


class URLPolicyTests(unittest.TestCase):
    def test_normalizes_domain(self):
        t=normalize_url("Example.COM")
        self.assertEqual(t.url,"https://example.com/")
        self.assertEqual(t.host,"example.com")
        self.assertEqual(t.port,443)
    def test_https_path_and_query(self):
        t=normalize_url("https://www.example.com/path?a=3#ignored")
        self.assertEqual(t.url,"https://www.example.com/path?a=3")
    def test_http_allowed(self):
        t=normalize_url("http://example.com/contact")
        self.assertEqual(t.port,80)
    def test_unicode_domains_are_idna(self):
        t=normalize_url("https://bücher.example.org/")
        self.assertTrue(t.host.startswith("xn--"))
    def test_rejects_non_web_schemes(self):
        for url in ["file:///etc/passwd","ftp://example.com","gopher://example.com","data:text/plain,test"]:
            with self.subTest(url=url),self.assertRaises(UnsafeTarget):
                normalize_url(url)
    def test_rejects_private_or_reserved_domains(self):
        for url in [
            "localhost","http://localhost:80","https://host.docker.internal",
            "http://metadata.google.internal/computeMetadata/v1",
            "http://server.local","https://test.internal",
            "http://127.0.0.1","https://10.0.0.1","http://192.168.0.1",
            "http://169.254.169.254","https://[::1]",
            "https://example.localhost","http://foo.home.arpa",
        ]:
            with self.subTest(url=url),self.assertRaises(UnsafeTarget):normalize_url(url)
    def test_rejects_ports(self):
        for url in ["https://example.com:8443","http://example.com:8080","http://example.com:25"]:
            with self.subTest(url=url),self.assertRaises(UnsafeTarget):normalize_url(url)
    def test_rejects_credentials(self):
        with self.assertRaises(UnsafeTarget):normalize_url("https://user:password@example.com/")
    def test_rejects_obfuscated_hostname(self):
        for url in ["https://example..com","https://bad%2eexample.com","https://foo\\@bar.com"]:
            with self.subTest(url=url),self.assertRaises(UnsafeTarget):normalize_url(url)
    def test_rejects_control_characters(self):
        with self.assertRaises(UnsafeTarget):normalize_url("example.com\nHost: metadata")
    def test_url_size_limit(self):
        with self.assertRaises(UnsafeTarget):normalize_url("example.com/"+"a"*2200)
    def test_nonstring_input(self):
        with self.assertRaises(UnsafeTarget):normalize_url(None)
    def test_rejects_mixed_public_and_private_dns(self):
        def resolver(*args,**kwargs):
            return [
                (socket.AF_INET,socket.SOCK_STREAM,6,"",("93.184.216.34",443)),
                (socket.AF_INET,socket.SOCK_STREAM,6,"",("10.0.0.1",443))
            ]
        with self.assertRaises(UnsafeTarget):public_ips("example.com",443,resolver=resolver)
    def test_resolves_public_ips(self):
        def resolver(*args,**kwargs):
            return [(socket.AF_INET,socket.SOCK_STREAM,6,"",("93.184.216.34",443))]
        self.assertEqual(public_ips("example.com",443,resolver=resolver),["93.184.216.34"])
    def test_dns_errors_are_safe(self):
        def resolver(*args,**kwargs):raise OSError("private network state")
        with self.assertRaisesRegex(UnsafeTarget,"could not be resolved"):
            public_ips("example.com",443,resolver=resolver)
    def test_public_dns_empty(self):
        with self.assertRaises(UnsafeTarget):public_ips("example.com",443,resolver=lambda *a,**k:[])
    def test_no_ipv4_mapped_private(self):
        def resolver(*args,**kwargs):
            return [(socket.AF_INET6,socket.SOCK_STREAM,6,"",("::ffff:10.0.0.1",443,0,0))]
        with self.assertRaises(UnsafeTarget):public_ips("example.com",443,resolver=resolver)


if __name__=="__main__":unittest.main()
