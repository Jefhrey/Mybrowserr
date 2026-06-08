import unittest
from unittest.mock import Mock, patch
from app.browser import URL, browserCache, sockets, Browser

CACHE_EXPIRE = 100

class TestURL(unittest.TestCase):
    def test_parse_http(self):
        u = URL("http://example.com")
        self.assertEqual(u.scheme, "http")
        self.assertEqual(u.host, "example.com")
        self.assertEqual(u.port, 80)
        self.assertEqual(u.path, "/")

        u2 = URL("https://example.com:8443/path")
        self.assertEqual(u2.scheme, "https")
        self.assertEqual(u2.port, 8443)
        self.assertEqual(u2.path, "/path")

    def test_add_headers(self):
        u = URL("http://example.com")
        req = "GET / HTTP/1.1\r\n"
        out = u.addHeaders(req, {"X-Test": "1", "Accept": "text/html"})
        self.assertIn("X-Test: 1\r\n", out)
        self.assertIn("Accept: text/html\r\n", out)

    def test_cache(self):
        link = URL("http://localhost:9000/demo")
        content = link.request_direct({}, 0)
        expire_time, cached_content = browserCache.get(link.host + link.path)
        self.assertEqual(content, cached_content)

if __name__ == "__main__":
    unittest.main()