"""Synthetic refinery-inspired blending; no MRPL plant data or validated economics."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'examples';root.mkdir(exist_ok=True)
# Volumes in arbitrary consistent units; costs in cost units / volume.
# Low-sulfur and high-sulfur feed, premium and regular blends.
base=dict(name='Synthetic refinery blending LP',names=['low_to_premium','high_to_premium','low_to_regular','high_to_regular'],c=[52,34,52,34],lower=[0]*4,upper=[100]*4,A=[[1,1,0,0],[0,0,1,1],[1,0,1,0],[0,1,0,1],[-.5,1.5,0,0],[0,0,-1.3,.7]],row_lower=[60,50,None,None,None,None],row_upper=[60,50,85,100,0,0])
(root/'refinery_lp.json').write_text(json.dumps(base,indent=2))
qp=dict(base);qp['name']='Synthetic refinery smooth blending QP';qp['Q']=[[.08 if i==j else 0 for j in range(4)] for i in range(4)]
(root/'refinery_qp.json').write_text(json.dumps(qp,indent=2))
m=dict(base);m['name']='Synthetic refinery activation MILP';m['names']=base['names']+['high_feed_enabled'];m['c']=base['c']+[120];m['lower']=[0]*5;m['upper']=[100]*4+[1];m['integer']=[4];m['A']=[r+[0] for r in base['A']]+[[0,1,0,1,-100]];m['row_lower']=base['row_lower']+[None];m['row_upper']=base['row_upper']+[0]
(root/'refinery_milp.json').write_text(json.dumps(m,indent=2))
# Exact-integer coefficients make this infeasibility witness rationally checkable.
f=dict(name='Contradictory production requirements',c=[1],A=[[1],[1]],row_lower=[8,None],row_upper=[None,3],lower=[0],upper=[10])
(root/'infeasible.json').write_text(json.dumps(f,indent=2))
(root/'tiny.mps').write_text('''NAME TINY
ROWS
 N COST
 L CAP
COLUMNS
 X COST -3 CAP 1
 Y COST -2 CAP 1
RHS
 RHS1 CAP 4
BOUNDS
 UP BND X 3
 UP BND Y 3
ENDATA
''')
