import json,subprocess,sys,time,unittest,urllib.request,urllib.error,socket
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as s:s.bind(('127.0.0.1',0));cls.port=s.getsockname()[1]
        cls.p=subprocess.Popen([sys.executable,'server.py','--port',str(cls.port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        cls.url=f'http://127.0.0.1:{cls.port}'
        for _ in range(100):
            try:urllib.request.urlopen(cls.url+'/health',timeout=.2);break
            except OSError:time.sleep(.02)
        else:raise RuntimeError('Server failed to start')
    @classmethod
    def tearDownClass(cls):cls.p.terminate();cls.p.wait(timeout=5)
    def post(self,payload):
        req=urllib.request.Request(self.url+'/api/solve',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        return json.load(urllib.request.urlopen(req,timeout=40))
    def test_http_page_and_examples(self):
        with urllib.request.urlopen(self.url) as r:self.assertIn(b'SOV',r.read())
        with urllib.request.urlopen(self.url+'/api/examples') as r:self.assertIn('refinery_lp',json.load(r))
    def test_http_solve(self):
        m=json.loads((ROOT/'examples/refinery_lp.json').read_text());r=self.post({'model':m})
        self.assertEqual(r['status'],'OPTIMAL_VERIFIED');self.assertEqual(r['objective'],4865)
    def test_http_invalid(self):
        with self.assertRaises(urllib.error.HTTPError) as c:self.post({'model':{}})
        self.assertEqual(c.exception.code,400)
if __name__=='__main__':unittest.main()
