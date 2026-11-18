"""Local development server: static UI plus same-origin /api/growth-audit.

Start: python -m growthaudit.devserver
Not intended as a directly exposed public production server.
"""
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .serverless import handler

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/"web"
MAPPING={
    "/":"index.html","/growth-audit":"index.html",
    "/growth-audit.css":"styles.css",
    "/growth-audit.js":"app.js"
}
MIME={".css":"text/css",".js":"text/javascript",".html":"text/html"}


class DevHandler(handler):
    def do_GET(self):
        path=urlsplit(self.path).path
        if path.startswith("/api/growth-audit"):return super().do_GET()
        filename=MAPPING.get(path)
        if filename is None:
            self._headers(404,0);return
        file=WEB/filename
        payload=file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",MIME[file.suffix]+"; charset=utf-8")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Length",str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def do_POST(self):
        if urlsplit(self.path).path!="/api/growth-audit":
            self._headers(404,0);return
        return super().do_POST()


def main():
    import os
    port=int(os.environ.get("PORT","8769"))
    host=os.environ.get("HOST","127.0.0.1")
    httpd=ThreadingHTTPServer((host,port),DevHandler)
    print(f"GrowthAudit Pro local UI: http://{host}:{port}/growth-audit",flush=True)
    httpd.serve_forever()


if __name__=="__main__":main()
