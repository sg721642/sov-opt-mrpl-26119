"""Local demo server: bounded requests, subprocess isolation, hard solve timeout.
For public use put this behind an authenticated reverse proxy with TLS/rate limits.
"""
import argparse,json,os,subprocess,sys,tempfile,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SLOTS=threading.BoundedSemaphore(2)
EXAMPLES={p.stem:p for p in (ROOT/'examples').glob('*.json')}
class Handler(BaseHTTPRequestHandler):
    def send(self,status,data,kind='application/json'):
        if kind=='application/json':data=json.dumps(data,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
    def do_HEAD(self):
        return self.do_GET()
    def do_GET(self):
        if self.path=='/health':return self.send(200,{'status':'ok','version':'0.1.7'})
        if self.path=='/api/manifest':return self.send(200,json.loads((ROOT/'data/manifest.json').read_text()))
        if self.path=='/api/examples':return self.send(200,{k:json.loads(p.read_text()) for k,p in EXAMPLES.items()})
        if self.path in ('/','/index.html'):return self.send(200,(ROOT/'web/index.html').read_bytes(),'text/html; charset=utf-8')
        self.send(404,{'error':'Not found'})
    def do_POST(self):
        if self.path!='/api/solve':return self.send(404,{'error':'Not found'})
        origin=self.headers.get('Origin')
        if origin and origin not in ('http://'+self.headers.get('Host',''),'https://'+self.headers.get('Host','')):return self.send(403,{'error':'Origin not allowed'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=300000:raise ValueError('Request must be 1..300000 bytes')
            payload=json.loads(self.rfile.read(length));backend=payload.get('backend','cpu')
            if backend not in ('cpu','pdhg-cpu'):raise ValueError('Web demo supports CPU or CPU PDHG; use CLI for CUDA')
            from sovopt import Model
            model=Model.from_dict(payload['model'])
            if len(model.c)>100 or len(model.A)>150:raise ValueError('Web demo cap is 100 variables / 150 rows. Use CLI for larger tests.')
        except (ValueError,TypeError,KeyError,OverflowError) as e:return self.send(400,{'error':str(e)})
        if not SLOTS.acquire(blocking=False):return self.send(429,{'error':'Two solves already running; retry shortly'})
        try:
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'model.json';p.write_text(json.dumps(model.to_dict()))
                env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
                run=subprocess.run([sys.executable,'-m','sovopt',str(p),'--backend',backend],cwd=ROOT,env=env,capture_output=True,text=True,timeout=35)
                try:r=json.loads(run.stdout)
                except ValueError:r={'status':'NUMERICAL_FAILURE','message':f'Worker failed (code {run.returncode}): {run.stderr[:200].strip()}','gpu_executed':False}
                r.setdefault('gpu_executed',False)
                r['model_sha256']=model.fingerprint()
                r['model_name']=model.name
                r['backend']=backend
                self.send(200,r)
        except subprocess.TimeoutExpired:self.send(200,{'status':'LIMIT_REACHED','message':'35-second web worker deadline reached','gpu_executed':False,'model_sha256':model.fingerprint(),'model_name':model.name,'backend':backend})
        finally:SLOTS.release()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=int(os.environ.get('PORT',8000)));a=p.parse_args()
    print(f'SOV-OPT demo at http://{a.host}:{a.port}',flush=True)
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
