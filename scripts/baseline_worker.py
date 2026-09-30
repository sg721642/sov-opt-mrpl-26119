"""EXTERNAL BENCHMARK ONLY. Never imported by sovopt.
Run in a separate interpreter/process.
Standalone parser for original MPS files feeding into SciPy HiGHS / highspy.
Validates the original parsed problem, independent of sovopt's parser and JSON.
"""
import sys, json, time
from pathlib import Path
import numpy as np

def parse_mps_standalone(path):
    """Self-contained MPS parser independent of sovopt."""
    rows = {}
    cols = {}
    rhs = {}
    bounds = {}
    ints = set()
    section = None
    obj_row = None
    marker = False

    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('*'):
            continue
        tokens = line.split()
        key = tokens[0]
        if key in ('NAME', 'ROWS', 'COLUMNS', 'RHS', 'BOUNDS', 'ENDATA', 'OBJSENSE'):
            section = key
            continue
        if section == 'ROWS':
            rtype, rname = tokens[0], tokens[1]
            rows[rname] = rtype
            if rtype == 'N' and obj_row is None:
                obj_row = rname
        elif section == 'COLUMNS':
            if len(tokens) == 3 and tokens[1].strip("'\"") == 'MARKER':
                marker = (tokens[2].strip("'\"") == 'INTORG')
                continue
            cname = tokens[0]
            col_dict = cols.setdefault(cname, {})
            if marker:
                ints.add(cname)
            for i in range(1, len(tokens), 2):
                col_dict[tokens[i]] = col_dict.get(tokens[i], 0.0) + float(tokens[i+1])
        elif section == 'RHS':
            start_idx = 1 if len(tokens) in (3, 5) else 0
            for i in range(start_idx, len(tokens), 2):
                rname, val = tokens[i], float(tokens[i+1])
                rhs[rname] = val
        elif section == 'BOUNDS':
            btype = tokens[0]
            start_idx = 2 if len(tokens) in (3, 4) and tokens[1] not in cols else 1
            cname = tokens[start_idx]
            val = float(tokens[start_idx+1]) if len(tokens) > start_idx+1 else None
            b = bounds.setdefault(cname, [0.0, np.inf])
            if btype == 'UP' and val is not None: b[1] = val
            elif btype == 'LO' and val is not None: b[0] = val
            elif btype == 'FX' and val is not None: b[0] = val; b[1] = val
            elif btype == 'FR': b[0] = -np.inf; b[1] = np.inf
            elif btype == 'MI': b[0] = -np.inf
            elif btype == 'PL': b[1] = np.inf
            elif btype == 'BV': b[0] = 0.0; b[1] = 1.0; ints.add(cname)
            elif btype in ('LI', 'UI'):
                ints.add(cname)
                if btype == 'LI' and val is not None: b[0] = val
                if btype == 'UI' and val is not None: b[1] = val

    cnames = list(cols.keys())
    con_rows = [r for r in rows if r != obj_row]
    c_vec = np.array([cols[c].get(obj_row, 0.0) for c in cnames], dtype=float)
    A_mat = np.array([[cols[c].get(r, 0.0) for c in cnames] for r in con_rows], dtype=float)
    row_l = np.array([rhs.get(r, 0.0) if rows[r] in ('G', 'E') else -np.inf for r in con_rows], dtype=float)
    row_u = np.array([rhs.get(r, 0.0) if rows[r] in ('L', 'E') else np.inf for r in con_rows], dtype=float)
    var_l = np.array([bounds.get(c, [0.0, np.inf])[0] for c in cnames], dtype=float)
    var_u = np.array([bounds.get(c, [0.0, np.inf])[1] for c in cnames], dtype=float)
    int_indices = [j for j, c in enumerate(cnames) if c in ints]

    return {
        'c': c_vec, 'A': A_mat, 'row_lower': row_l, 'row_upper': row_u,
        'lower': var_l, 'upper': var_u, 'integer': int_indices, 'names': cnames
    }

if __name__ == '__main__':
    from scipy.optimize import linprog, milp, Bounds, LinearConstraint
    target = Path(sys.argv[1])
    start = time.perf_counter()
    if target.suffix == '.mps':
        d = parse_mps_standalone(target)
    else:
        d = json.loads(target.read_text())
        d['c'] = np.array(d['c'])
        d['A'] = np.array(d.get('A', []))
        d['lower'] = np.array([-np.inf if v is None else v for v in d['lower']])
        d['upper'] = np.array([np.inf if v is None else v for v in d['upper']])
        d['row_lower'] = np.array([-np.inf if v is None else v for v in d.get('row_lower', [-np.inf]*len(d['A']))])
        d['row_upper'] = np.array([np.inf if v is None else v for v in d.get('row_upper', [np.inf]*len(d['A']))])

    c, A = d['c'], d['A']
    if d.get('integer'):
        integrality = np.zeros(len(c))
        integrality[d['integer']] = 1
        r = milp(c, integrality=integrality, bounds=Bounds(d['lower'], d['upper']),
                 constraints=LinearConstraint(A, d['row_lower'], d['row_upper']), options={'time_limit': 30})
    else:
        G = []
        h = []
        for a, lo, hi in zip(A, d['row_lower'], d['row_upper']):
            if np.isfinite(hi): G.append(a); h.append(hi)
            if np.isfinite(lo): G.append(-a); h.append(-lo)
        r = linprog(c, A_ub=G or None, b_ub=h or None,
                    bounds=list(zip(d['lower'], d['upper'])), method='highs')

    print(json.dumps(dict(
        backend='external SciPy/HiGHS process',
        input_source=str(target),
        success=bool(r.success),
        objective=None if r.fun is None else float(r.fun),
        seconds=time.perf_counter() - start,
        message=r.message
    )))
