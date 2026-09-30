"""Recompute an exported browser audit independently of the solve operation."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sovopt import Model
from sovopt.verify import verify,exact_farkas
p=json.loads(Path(sys.argv[1]).read_text());m=Model.from_dict(p['model']);r=p['result']
if m.fingerprint()!=r['model_sha256']:raise SystemExit('Model hash mismatch')
if 'x' in r:print(json.dumps(verify(m,r['x'],r.get('dual')),indent=2))
elif 'certificate' in r:print('Exact Farkas check:',exact_farkas(m,r['certificate']))
else:print('No candidate or certificate to verify')
# A complete MILP proof cannot be reconstructed from the final incumbent alone.
