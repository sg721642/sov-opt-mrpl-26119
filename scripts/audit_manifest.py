import json
from pathlib import Path

m = json.loads((Path("data/manifests/gpu_pdhg_lp.json")).read_text())
# Filter out non-instance keys (like metadata/config)
instances = {k: v for k, v in m.items() if isinstance(v, dict) and "stratum" in v}
print(f"Total instances: {len(instances)}")
print()
for k, v in sorted(instances.items(), key=lambda x: (x[1].get("stratum",""), x[0])):
    sha = v.get("SHA256", "?")
    print(f"{k:20s} | {v.get('stratum','?'):6s} | n={v.get('n_variables','?'):5} | m={v.get('n_constraints','?'):5} | nnz={v.get('n_nonzeros','?'):6} | sha={sha[:16]}...")
