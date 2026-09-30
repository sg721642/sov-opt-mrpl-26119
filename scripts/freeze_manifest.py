"""Freeze local files without inventing optima or downloading licensed datasets."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('files',nargs='+');p.add_argument('--output',default='reports/manifest.json');a=p.parse_args()
paths=[Path(f).resolve() for f in a.files]
out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
# Relative paths are portable when the containing folder is shared intact.
import os
out.write_text(json.dumps({'seed':26119,'instances':[{'path':os.path.relpath(f,out.resolve().parent),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'known_objective':None,'source':'fill official source URL before publication'} for f in paths]},indent=2)+'\n');print(out)
