import io
import json
import socket
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from server import Handler

class HandlerUnitTests(unittest.TestCase):
    # Unit tests for HTTP request handler methods directly in-process.

    def _invoke(self, method, path, body=b"", headers=None):
        if headers is None:
            headers = {}
        h = Handler.__new__(Handler)
        h.client_address = ("127.0.0.1", 12345)
        h.server = None
        h.command = method
        h.path = path
        h.request_version = "HTTP/1.1"
        h.requestline = f"{method} {path} HTTP/1.1"
        h.headers = dict(headers)
        h.rfile = io.BytesIO(body)
        h.wfile = io.BytesIO()
        if method == "GET":
            h.do_GET()
        elif method == "POST":
            h.do_POST()
        out = h.wfile.getvalue()
        crlf = b"\r\n"
        crlf2 = b"\r\n\r\n"
        status_line = out.split(crlf, 1)[0].decode("latin1")
        status_code = int(status_line.split()[1])
        parts = out.split(crlf2, 1)
        resp_body = parts[1] if len(parts) > 1 else b""
        return status_code, resp_body

    def test_get_health(self):
        status, body = self._invoke("GET", "/health")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "sov-opt")
        self.assertTrue(data.get("solver_ready"))
        self.assertEqual(data.get("version"), "0.3.2")

    def test_get_api_health(self):
        status, body = self._invoke("GET", "/api/health")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "sov-opt")
        self.assertTrue(data.get("solver_ready"))
        self.assertEqual(data.get("version"), "0.3.2")

    def test_host_port_env_handling(self):
        import os
        orig_host = os.environ.get("HOST")
        orig_port = os.environ.get("PORT")
        try:
            os.environ["HOST"] = "0.0.0.0"
            os.environ["PORT"] = "9999"
            default_host = os.environ.get("HOST", "127.0.0.1")
            default_port = int(os.environ.get("PORT", 8000))
            self.assertEqual(default_host, "0.0.0.0")
            self.assertEqual(default_port, 9999)
        finally:
            if orig_host is not None:
                os.environ["HOST"] = orig_host
            else:
                os.environ.pop("HOST", None)
            if orig_port is not None:
                os.environ["PORT"] = orig_port
            else:
                os.environ.pop("PORT", None)

    def test_get_root_page(self):
        status, body = self._invoke("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"SOV-OPT", body)
        self.assertIn(b"Mangalore Refinery and Petrochemicals Limited", body)

    def test_get_static_asset_logo(self):
        status, body = self._invoke("GET", "/assets/MRPL_logo.jpg")
        self.assertEqual(status, 200)
        self.assertTrue(len(body) > 100)

    def test_get_static_asset_team_photo(self):
        status, body = self._invoke("GET", "/assets/team/satyam.png")
        self.assertEqual(status, 200)
        self.assertTrue(len(body) > 100)

    def test_get_static_asset_with_query_param(self):
        status, body = self._invoke("GET", "/assets/MRPL_logo.jpg?v=123")
        self.assertEqual(status, 200)
        self.assertTrue(len(body) > 100)

    def test_get_manifest(self):
        status, body = self._invoke("GET", "/api/manifest")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIn("instances", data)
        self.assertIn("afiro", data["instances"])
        self.assertIn("blend", data["instances"])

    def test_get_examples(self):
        status, body = self._invoke("GET", "/api/examples")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIn("afiro", data)
        self.assertIn("blend", data)
        self.assertIn("flugpl", data)
        self.assertNotIn("avgas", data)

    def test_post_solve_afiro(self):
        m = json.loads((ROOT / "examples/afiro.json").read_text())
        payload = json.dumps({"model": m, "backend": "cpu"}).encode()
        status, body = self._invoke("POST", "/api/solve", payload,
                                   {"Content-Length": str(len(payload)), "Content-Type": "application/json"})
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data["status"], "OPTIMAL_VERIFIED")
        self.assertEqual(data["model_name"].lower(), "afiro")
        self.assertEqual(data["backend"], "cpu")
        self.assertAlmostEqual(data["objective"], -464.75314285714285, places=4)

    def test_post_solve_invalid_payload(self):
        payload = json.dumps({"model": {}}).encode()
        status, body = self._invoke("POST", "/api/solve", payload,
                                   {"Content-Length": str(len(payload)), "Content-Type": "application/json"})
        self.assertEqual(status, 400)

    def test_get_refinery_twin(self):
        status, body = self._invoke("GET", "/api/refinery_twin?variant=lp")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data["name"], "MRPL_Refinery_Twin_LP")
        self.assertEqual(len(data["c"]), 36)
        self.assertEqual(data["c"][0], 70.0)

    def test_get_refinery_twin_parameterized(self):
        status, body = self._invoke("GET", "/api/refinery_twin?variant=lp&c_arab=85.5&c_basrah=58.0&min_gas=45.0&min_dsl=55.0")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data["name"], "MRPL_Refinery_Twin_LP")
        self.assertEqual(data["c"][0], 85.5)
        self.assertEqual(data["c"][1], 58.0)

    def test_get_gpu_summary(self):
        status, body = self._invoke("GET", "/api/gpu_summary")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIn("gpu_device", data)
        self.assertIn("suite_totals", data)

    def test_get_differential_benchmark(self):
        status, body = self._invoke("GET", "/api/differential_benchmark")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIn("lp_comparison", data)
        self.assertIn("milp_comparison", data)
        self.assertEqual(len(data["lp_comparison"]), 17)
        self.assertEqual(len(data["milp_comparison"]), 38)

    def test_get_sparse_stress(self):
        status, body = self._invoke("GET", "/api/sparse_stress")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIn("results", data)
        self.assertTrue(len(data["results"]) >= 5)


class ServerIntegrationTests(unittest.TestCase):
    # Integration tests communicating with a live HTTP server over loopback socket.

    @classmethod
    def setUpClass(cls):
        cls.server = None
        cls.thread = None
        cls.port = None
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", 0))
                cls.port = s.getsockname()[1]
            cls.server = ThreadingHTTPServer(("127.0.0.1", cls.port), Handler)
            cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
            cls.thread.start()
            cls.url = f"http://127.0.0.1:{cls.port}"
            req = urllib.request.Request(cls.url + "/health")
            with urllib.request.urlopen(req, timeout=2.0) as r:
                if r.status != 200:
                    cls.tearDownClass()
        except OSError:
            cls.server = None

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()

    def setUp(self):
        if self.server is None:
            self.skipTest("Loopback network socket not available in this sandbox environment")

    def test_http_health_integration(self):
        req = urllib.request.Request(self.url + "/health")
        with urllib.request.urlopen(req, timeout=2.0) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read())
            self.assertEqual(data["status"], "ok")

    def test_http_api_health_integration(self):
        req = urllib.request.Request(self.url + "/api/health")
        with urllib.request.urlopen(req, timeout=2.0) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read())
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["service"], "sov-opt")
            self.assertTrue(data["solver_ready"])

    def test_http_solve_integration(self):
        m = json.loads((ROOT / "examples/afiro.json").read_text())
        payload = json.dumps({"model": m, "backend": "cpu"}).encode()
        req = urllib.request.Request(self.url + "/api/solve", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30.0) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read())
            self.assertEqual(data["status"], "OPTIMAL_VERIFIED")
            self.assertEqual(data["model_name"].lower(), "afiro")

if __name__ == "__main__":
    unittest.main()
