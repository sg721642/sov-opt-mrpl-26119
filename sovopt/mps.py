"""Extended free/fixed-format MPS/QPS parser.
Supports: MIN/MAX objective sense, LO/UP/FX/BV/LI/UI/FR/MI/PL bound types,
default lower=0 and default upper=+inf, objective constant (RHS on N row),
single-name RHS/BOUNDS sets with continuation lines, and QUADOBJ for convex QP.
Rejects non-empty RANGES, multiple N rows, multiple RHS sets, and unknown bound types.
"""
from pathlib import Path
import numpy as np
from .model import Model

def read_mps(path):
    rows={}; cols={}; rhs={}; bounds={}; ints=set(); quad_entries=[]
    section=None; obj=None; name=Path(path).stem; marker=False
    rhsname=None; bndname=None; maximize=False; obj_offset=0.0
    last_col=None

    for lineno, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line or line.startswith('*'): continue
        t=line.split()
        if not t: continue

        # In standard MPS, section headers start in column 1 (no leading whitespace)
        if not line[0].isspace():
            key=t[0]
            if key in ('NAME','ROWS','COLUMNS','RHS','BOUNDS','RANGES','QUADOBJ','ENDATA','OBJSENSE'):
                section=key
                if key=='NAME' and len(t)>1: name=t[1]
                if key=='ENDATA': break
                continue
            else:
                raise ValueError(f'Unsupported MPS section or indicator at line {lineno}: {line}')

        if section=='OBJSENSE':
            if t[0] in ('MAX','MAXIMIZE'): maximize=True
            elif t[0] not in ('MIN','MINIMIZE'): raise ValueError(f'Unknown OBJSENSE at {lineno}: {t[0]}')
        elif section=='RANGES':
            raise ValueError(f'Non-empty RANGES section is not supported (line {lineno}); preprocess the model to split ranged rows')
        elif section=='ROWS':
            if len(t)!=2 or t[0] not in ('N','L','G','E') or t[1] in rows:
                raise ValueError(f'Invalid ROWS at {lineno}: {line}')
            rows[t[1]]=t[0]
            if t[0]=='N':
                if obj is not None: raise ValueError('Multiple N rows unsupported')
                obj=t[1]
        elif section=='COLUMNS':
            # Check for integer markers: col_name 'MARKER' 'INTORG' / 'INTEND'
            if len(t)==3 and t[1].strip("'\"")=='MARKER':
                mode=t[2].strip("'\"")
                if mode not in ('INTORG','INTEND'): raise ValueError(f'Invalid integer marker at {lineno}')
                marker=mode=='INTORG'
                continue
            if len(t) in (2, 4) and t[0] in rows and last_col is not None:
                # Continuation line for the current column
                col=cols[last_col]
                for i in range(0, len(t), 2):
                    if t[i] not in rows: raise ValueError(f'Unknown row {t[i]} at {lineno}')
                    col[t[i]]=col.get(t[i], 0.)+float(t[i+1])
            elif len(t) in (3, 5):
                last_col=t[0]
                col=cols.setdefault(t[0], {})
                if marker: ints.add(t[0])
                for i in range(1, len(t), 2):
                    if t[i] not in rows: raise ValueError(f'Unknown row {t[i]} at {lineno}')
                    col[t[i]]=col.get(t[i], 0.)+float(t[i+1])
            else:
                raise ValueError(f'Invalid COLUMNS format at line {lineno}: {line}')
        elif section=='RHS':
            if len(t) in (2, 4) and t[0] in rows:
                entries=[(t[i], float(t[i+1])) for i in range(0, len(t), 2)]
            elif len(t) in (3, 5):
                if rhsname is not None and rhsname!=t[0]: raise ValueError('Multiple RHS sets unsupported')
                rhsname=t[0]
                entries=[(t[i], float(t[i+1])) for i in range(1, len(t), 2)]
            else:
                raise ValueError(f'Invalid RHS at line {lineno}: {line}')
            for rname, val in entries:
                if rname not in rows: raise ValueError(f'Unknown RHS row {rname} at {lineno}')
                if rname==obj:
                    obj_offset=-val
                else:
                    rhs[rname]=val
        elif section=='BOUNDS':
            btype=t[0]
            if btype not in ('LO','UP','FX','BV','LI','UI','FR','MI','PL'):
                raise ValueError(f'Unsupported MPS bound type {btype!r} at {lineno}')
            if len(t)==2:
                col_name=t[1]; val=None
            elif len(t)==3:
                if t[1] in cols:
                    col_name=t[1]; val=float(t[2])
                else:
                    if bndname is not None and bndname!=t[1]: raise ValueError('Multiple bound sets unsupported')
                    bndname=t[1]; col_name=t[2]; val=None
            elif len(t)==4:
                if bndname is not None and bndname!=t[1]: raise ValueError('Multiple bound sets unsupported')
                bndname=t[1]; col_name=t[2]; val=float(t[3])
            else:
                raise ValueError(f'Invalid BOUNDS at line {lineno}: {line}')

            if col_name not in cols: raise ValueError(f'Unknown bound column {col_name!r} at {lineno}')
            b=bounds.setdefault(col_name, [0., np.inf])
            if btype=='BV':
                b[:]=[0., 1.]; ints.add(col_name)
            elif btype=='FR':
                b[:]=[-np.inf, np.inf]
            elif btype=='MI':
                b[0]=-np.inf
            elif btype=='PL':
                b[1]=np.inf
            else:
                if val is None: raise ValueError(f'Missing bound value at {lineno}')
                if btype in ('LO','LI','FX'): b[0]=val
                if btype in ('UP','UI','FX'): b[1]=val
                if btype in ('LI','UI'): ints.add(col_name)
        elif section=='QUADOBJ':
            if len(t)!=3: raise ValueError(f'Invalid QUADOBJ line at {lineno}: {line}')
            c1, c2, val = t[0], t[1], float(t[2])
            quad_entries.append((c1, c2, val))

    if obj is None or not cols: raise ValueError('Missing objective row or empty COLUMNS section')
    names=list(cols)
    rn=[r for r in rows if r!=obj]
    b=[bounds.get(c, [0., np.inf]) for c in names]

    c_vec=[cols[c].get(obj, 0.) for c in names]
    if maximize: c_vec=[-v for v in c_vec]

    Q = None
    if quad_entries:
        Q = np.zeros((len(names), len(names)), dtype=float)
        for c1, c2, val in quad_entries:
            if c1 not in cols or c2 not in cols: raise ValueError(f'Unknown column in QUADOBJ: {c1}, {c2}')
            i, j = names.index(c1), names.index(c2)
            Q[i, j] += val
            if i != j: Q[j, i] += val
        if maximize:
            Q = -Q

    return Model.from_dict(dict(
        name=name, names=names,
        c=c_vec,
        A=[[cols[c].get(r, 0.) for c in names] for r in rn],
        row_lower=[rhs.get(r, 0.) if rows[r] in ('G','E') else None for r in rn],
        row_upper=[rhs.get(r, 0.) if rows[r] in ('L','E') else None for r in rn],
        lower=[v[0] for v in b],
        upper=[v[1] for v in b],
        integer=[j for j,c in enumerate(names) if c in ints],
        Q=None if Q is None else Q.tolist(),
        maximize=maximize,
        obj_offset=obj_offset,
    ))
