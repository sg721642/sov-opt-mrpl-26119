"""Strict free-format MPS subset. Reject unsupported dialects instead of guessing.
Finite LO/UP/FX/BV bounds required (default lower zero). Minimization only.
"""
from pathlib import Path
from .model import Model

def read_mps(path):
    rows={};cols={};rhs={};bounds={};ints=set();section=None;obj=None;name=Path(path).stem;marker=False;rhsname=None;bndname=None
    for lineno,line in enumerate(Path(path).read_text().splitlines(),1):
        t=line.split()
        if not t or t[0].startswith('*'):continue
        key=t[0]
        if key in ('NAME','ROWS','COLUMNS','RHS','BOUNDS','ENDATA','OBJSENSE') and (len(t)==1 or key=='NAME'):
            section=key
            if key=='NAME' and len(t)>1:name=t[1]
            continue
        if section=='OBJSENSE':
            if t!=['MIN']:raise ValueError('Only MIN MPS is supported')
        elif section=='ROWS':
            if len(t)!=2 or t[0] not in ('N','L','G','E') or t[1] in rows:raise ValueError(f'Invalid ROWS at {lineno}')
            rows[t[1]]=t[0]
            if t[0]=='N':
                if obj is not None:raise ValueError('Multiple N rows unsupported')
                obj=t[1]
        elif section=='COLUMNS':
            if len(t)==3 and t[1].strip("'\"")=='MARKER':
                mode=t[2].strip("'\"")
                if mode not in ('INTORG','INTEND'):raise ValueError('Invalid integer marker')
                marker=mode=='INTORG';continue
            if len(t) not in (3,5):raise ValueError('Only explicit free-format COLUMNS supported')
            col=cols.setdefault(t[0],{})
            if marker:ints.add(t[0])
            for i in range(1,len(t),2):
                if t[i] not in rows:raise ValueError('Unknown row')
                col[t[i]]=col.get(t[i],0.)+float(t[i+1])
        elif section=='RHS':
            if len(t) not in (3,5):raise ValueError('Invalid RHS')
            if rhsname is not None and rhsname!=t[0]:raise ValueError('Multiple RHS sets unsupported')
            rhsname=t[0]
            for i in range(1,len(t),2):
                if t[i] not in rows:raise ValueError('Unknown RHS row')
                if t[i]==obj and float(t[i+1])!=0:raise ValueError('Objective offset unsupported')
                rhs[t[i]]=float(t[i+1])
        elif section=='BOUNDS':
            if len(t)<3 or t[0] not in ('LO','UP','FX','BV','LI','UI'):raise ValueError('Unsupported MPS bound')
            if bndname is not None and bndname!=t[1]:raise ValueError('Multiple bound sets unsupported')
            bndname=t[1]
            if t[2] not in cols:raise ValueError('Unknown bound column')
            b=bounds.setdefault(t[2],[0.,None]);kind=t[0]
            if kind=='BV':b[:]=[0.,1.];ints.add(t[2])
            else:
                if len(t)!=4:raise ValueError('Missing bound value')
                v=float(t[3])
                if kind in ('LO','LI','FX'):b[0]=v
                if kind in ('UP','UI','FX'):b[1]=v
                if kind in ('LI','UI'):ints.add(t[2])
        else:raise ValueError(f'Unsupported MPS section or content at line {lineno}: {line}')
    if obj is None or not cols:raise ValueError('Missing objective/columns')
    names=list(cols);rn=[r for r in rows if r!=obj]
    b=[bounds.get(c,[0,None]) for c in names]
    if any(v[1] is None for v in b):raise ValueError('Prototype requires an explicit finite upper bound for every variable; do not invent a big-M')
    return Model.from_dict(dict(name=name,names=names,c=[cols[c].get(obj,0) for c in names],A=[[cols[c].get(r,0) for c in names] for r in rn],row_lower=[rhs.get(r,0) if rows[r] in ('G','E') else None for r in rn],row_upper=[rhs.get(r,0) if rows[r] in ('L','E') else None for r in rn],lower=[v[0] for v in b],upper=[v[1] for v in b],integer=[j for j,c in enumerate(names) if c in ints]))
