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

def run_highspy(target):
    import highspy, importlib.metadata
    try:
        version = importlib.metadata.version("highspy")
    except Exception:
        try:
            version = f"{highspy.HIGHS_VERSION_MAJOR}.{highspy.HIGHS_VERSION_MINOR}.{highspy.HIGHS_VERSION_PATCH}"
        except Exception:
            version = "unknown"

    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    import os
    if "HIGHS_TIME_LIMIT" in os.environ:
        h.setOptionValue("time_limit", float(os.environ["HIGHS_TIME_LIMIT"]))
    target_str = str(target)
    temp_mps = None
    if target_str.endswith('.bz2'):
        import tempfile, bz2, shutil
        temp_mps = tempfile.NamedTemporaryFile(suffix='.mps', delete=False)
        with bz2.open(target_str, 'rb') as f_in:
            shutil.copyfileobj(f_in, temp_mps)
        temp_mps.close()
        actual_target = temp_mps.name
    elif target_str.endswith('.gz'):
        import tempfile, gzip, shutil
        temp_mps = tempfile.NamedTemporaryFile(suffix='.mps', delete=False)
        with gzip.open(target_str, 'rb') as f_in:
            shutil.copyfileobj(f_in, temp_mps)
        temp_mps.close()
        actual_target = temp_mps.name
    else:
        actual_target = target_str

    try:
        status = h.readModel(actual_target)
    finally:
        if temp_mps is not None:
            import os
            try:
                os.unlink(temp_mps.name)
            except OSError:
                pass

    if status != highspy.HighsStatus.kOk:
        return {'backend': f'highspy {version} (native C++ HiGHS)', 'solver_version': version, 'status': 'READ_ERROR', 'objective': None}
    
    lp = h.getLp()
    num_cols = h.getNumCol()
    num_rows = h.getNumRow()
    int_count = sum(1 for x in lp.integrality_ if x != highspy.HighsVarType.kContinuous) if hasattr(lp, "integrality_") else 0
    sense = "MAXIMIZE" if h.getObjectiveSense()[1] == highspy.ObjSense.kMaximize else "MINIMIZE"

    t0 = time.perf_counter()
    h.run()
    elapsed = time.perf_counter() - t0
    info = h.getInfo()
    model_status = str(h.getModelStatus())
    has_primal = (info.primal_solution_status == 2)
    obj = float(info.objective_function_value) if has_primal else None
    best_bound = None
    if int_count > 0 and hasattr(info, "mip_dual_bound") and abs(info.mip_dual_bound) < 1e20:
        best_bound = float(info.mip_dual_bound)

    return {
        'backend': f'highspy {version} (native C++ HiGHS)',
        'solver_name': 'HiGHS',
        'solver_version': version,
        'input_source': str(target),
        'parsed_dimensions': {
            'variables': num_cols,
            'constraints': num_rows,
            'integers': int_count
        },
        'objective_sense': sense,
        'model_status': model_status,
        'success': 'kOptimal' in model_status,
        'objective': obj,
        'best_bound': best_bound,
        'has_primal_solution': has_primal,
        'has_dual_solution': (info.dual_solution_status == 2),
        'simplex_iterations': info.simplex_iteration_count,
        'ipm_iterations': info.ipm_iteration_count,
        'seconds': elapsed
    }

def run_scipy(target):
    from scipy.optimize import linprog, milp, Bounds, LinearConstraint
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

    return dict(
        backend='external SciPy/HiGHS process',
        solver_name='SciPy',
        input_source=str(target),
        parsed_dimensions={
            'variables': len(c),
            'constraints': len(A),
            'integers': len(d.get('integer', []))
        },
        objective_sense='MINIMIZE',
        success=bool(r.success),
        model_status='Optimal' if r.success else str(r.status),
        objective=None if r.fun is None else float(r.fun),
        seconds=time.perf_counter() - start,
        message=r.message
    )

if __name__ == '__main__':
    target = Path(sys.argv[1])
    try:
        import highspy
        res = run_highspy(target)
    except ImportError:
        res = run_scipy(target)
    print(json.dumps(res, indent=2))

