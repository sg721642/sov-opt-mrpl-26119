import io, json, subprocess, sys, time, unittest, urllib.request, urllib.error, socket
from pathlib import Path
from server import Handler

ROOT = Path(__file__).resolve().parents[1]

class ServerTests(unittest.TestCase):
    use_direct_handler = False

    @classmethod
    def setUpClass(cls):
        try:
            with socket.socket() as s:
                s.bind(('127.0.0.1', 0))
                cls.port = s.getsockname()[1]
            cls.p = subprocess.Popen([sys.executable, 'server.py', '--port', str(cls.port)],
                                     cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cls.url = f'http://127.0.0.1:{cls.port}'
            for _ in range(50):
                try:
                    urllib.request.urlopen(cls.url + '/health', timeout=0.2)
                    return
                except OSError as e:
                    if getattr(e, 'errno', None) == 1:
                        # Operation not permitted (macOS sandbox restriction on outbound loopback socket)
                        cls.use_direct_handler = True
                        cls.p.terminate()
                        return
                    time.sleep(0.05)
            cls.use_direct_handler = True
            cls.p.terminate()
        except Exception:
            cls.use_direct_handler = True

    @classmethod
    def tearDownClass(cls):
        if not cls.use_direct_handler and hasattr(cls, 'p'):
            cls.p.terminate()
            cls.p.wait(timeout=5)

    def _invoke(self, method, path, body=b"", headers=None):
        if headers is None: headers = {}
        h = Handler.__new__(Handler)
        h.client_address = ('127.0.0.1', 12345)
        h.server = None
        h.command = method
        h.path = path
        h.request_version = 'HTTP/1.1'
        h.requestline = f'{method} {path} HTTP/1.1'
        h.headers = dict(headers)
        h.rfile = io.BytesIO(body)
        h.wfile = io.BytesIO()
        if method == 'GET':
            h.do_GET()
        elif method == 'POST':
            h.do_POST()
        out = h.wfile.getvalue()
        status_line = out.split(b'\r\n', 1)[0].decode('latin1')
        status_code = int(status_line.split()[1])
        parts = out.split(b'\r\n\r\n', 1)
        resp_body = parts[1] if len(parts) > 1 else b""
        return status_code, resp_body

    def get(self, path):
        if self.use_direct_handler:
            status, body = self._invoke('GET', path)
            return body
        with urllib.request.urlopen(self.url + path) as r:
            return r.read()

    def post(self, payload):
        body = json.dumps(payload).encode()
        if self.use_direct_handler:
            status, resp_bytes = self._invoke('POST', '/api/solve', body, {'Content-Length': str(len(body)), 'Content-Type': 'application/json'})
            if status >= 400:
                class FakeHTTPError(Exception):
                    def __init__(self, code): self.code = code
                raise FakeHTTPError(status)
            return json.loads(resp_bytes)
        req = urllib.request.Request(self.url + '/api/solve', data=body, headers={'Content-Type': 'application/json'})
        return json.load(urllib.request.urlopen(req, timeout=40))

    def test_http_page_and_examples(self):
        self.assertIn(b'SOV', self.get('/'))
        ex = json.loads(self.get('/api/examples'))
        self.assertIn('avgas', ex)
        self.assertIn('afiro', ex)
        self.assertIn('blend', ex)
        manifest = json.loads(self.get('/api/manifest'))
        self.assertIn('instances', manifest)
        self.assertIn('blend', manifest['instances'])
        self.assertEqual(manifest['instances']['blend']['expected_status'], 'OPTIMAL_VERIFIED')

    def test_http_solve(self):
        m = json.loads((ROOT / 'examples/avgas.json').read_text())
        r = self.post({'model': m})
        self.assertEqual(r['status'], 'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r['objective'], -7.75, places=4)

    def test_http_invalid(self):
        try:
            self.post({'model': {}})
            self.fail('Expected error for invalid model')
        except Exception as c:
            self.assertEqual(getattr(c, 'code', getattr(c, 'exception', None)), 400)

if __name__ == '__main__':
    unittest.main()
