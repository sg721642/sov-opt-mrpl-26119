import unittest,itertools,json
from pathlib import Path
from fractions import Fraction
import numpy as np
from sovopt import Model,load,solve
from sovopt.linalg import LU
from sovopt.verify import verify,safe_lower_bound,exact_farkas
ROOT=Path(__file__).resolve().parents[1]

def model(c,A=None,lo=None,hi=None,integer=(),Q=None):
    return Model.from_dict(dict(c=c,A=[] if A is None else A,lower=[0]*len(c) if lo is None else lo,upper=[5]*len(c) if hi is None else hi,integer=list(integer),Q=Q))

class SolverTests(unittest.TestCase):
    def test_lu_pivot_refinement(self):
        rng=np.random.default_rng(12)
        for n in range(1,15):
            A=rng.normal(size=(n,n));b=rng.normal(size=n);x=LU(A).solve(b)
            self.assertLess(np.max(abs(A@x-b)),1e-10)

    def test_verified_real_instances(self):
        """Test real-source documented instances with published reference values."""
        # 1. AVGAS (Petroleum refinery aviation gasoline blending LP, Symonds 1955)
        r_avgas=solve(load(ROOT/'data/verified/avgas.mps'))
        self.assertEqual(r_avgas['status'],'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_avgas['objective'],-7.75,places=4)
        self.assertTrue(r_avgas['verification']['kkt_passed'])

        # 2. AFIRO (Netlib LP, Michael Saunders, Systems Optimization Laboratory Stanford)
        r_afiro=solve(load(ROOT/'data/verified/afiro.mps'))
        self.assertEqual(r_afiro['status'],'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_afiro['objective'],-464.75314285714285,places=4)
        self.assertTrue(r_afiro['verification']['kkt_passed'])

        # 3. SC50A (Netlib LP, staircase model)
        r_sc50a=solve(load(ROOT/'data/verified/sc50a.mps'))
        self.assertEqual(r_sc50a['status'],'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_sc50a['objective'],-64.5750770585645,places=4)
        self.assertTrue(r_sc50a['verification']['kkt_passed'])

        # 4. SC50B (Netlib LP, staircase model)
        r_sc50b=solve(load(ROOT/'data/verified/sc50b.mps'))
        self.assertEqual(r_sc50b['status'],'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_sc50b['objective'],-70.0,places=4)
        self.assertTrue(r_sc50b['verification']['kkt_passed'])

        # 5. QP_EXAMPLE (Convex QP with QUADOBJ, analytical optimum c1=0.7625, c2=0.475)
        r_qp=solve(load(ROOT/'data/verified/qp_example.qps'))
        self.assertEqual(r_qp['status'],'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r_qp['objective'],8.371875,places=4)
        self.assertTrue(r_qp['verification']['kkt_passed'])

    def test_infeasible_certificate(self):
        m=load(ROOT/'data/legacy_synthetic/infeasible.json');r=solve(m)
        self.assertEqual(r['status'],'INFEASIBLE_CERTIFIED');self.assertTrue(exact_farkas(m,r['certificate']))
        self.assertFalse(exact_farkas(m,[0]*4))

    def test_bad_candidate(self):
        m=load(ROOT/'data/verified/avgas.json')
        self.assertFalse(verify(m,[2.0]*8)['feasible'])
        self.assertFalse(verify(m,[float('nan')]*8)['kkt_passed'])
        self.assertFalse(verify(m,[1.0]*8,[0]*len(m.inequalities()[1]))['kkt_passed'])

    def test_box_and_fixed(self):
        for lo,hi in [([-3,2],[5,2]),([0,0],[0,0]),([-5,-2],[-1,3])]:
            m=model([-2,3],lo=lo,hi=hi);r=solve(m)
            self.assertEqual(r['status'],'OPTIMAL_VERIFIED');self.assertAlmostEqual(r['objective'],-2*hi[0]+3*lo[1])

    def test_degenerate_scaled(self):
        for scale in [1e-8,1,1e8]:
            m=Model.from_dict(dict(c=[-1,-1],A=[[scale,scale],[scale,scale]],row_upper=[scale,scale],lower=[0,0],upper=[2,2]))
            r=solve(m);self.assertEqual(r['status'],'OPTIMAL_VERIFIED');self.assertAlmostEqual(r['objective'],-1)

    def test_known_random_lp_kkt(self):
        rng=np.random.default_rng(84)
        for case in range(50):
            n=4;m=6;x=rng.uniform(.5,4.5,n);A=rng.normal(size=(m,n));z=rng.uniform(.1,3,m);c=-A.T@z
            obj=Model.from_dict(dict(c=c.tolist(),A=A.tolist(),row_upper=(A@x).tolist(),lower=[0]*n,upper=[5]*n))
            r=solve(obj);self.assertEqual(r['status'],'OPTIMAL_VERIFIED',r.get('message'));self.assertAlmostEqual(r['objective'],c@x,places=6)
            bound=safe_lower_bound(obj,r['dual']);self.assertLessEqual(float(bound),r['objective']+1e-8)

    def test_random_integer_exhaustive(self):
        rng=np.random.default_rng(34)
        for _ in range(25):
            A=rng.integers(-3,4,(3,3));h=rng.integers(1,9,3);c=rng.integers(-4,5,3)
            m=Model.from_dict(dict(c=c.tolist(),A=A.tolist(),row_upper=h.tolist(),lower=[0]*3,upper=[3]*3,integer=[0,1,2]))
            truth=min(c@x for x in itertools.product(range(4),repeat=3) if np.all(A@x<=h))
            r=solve(m);self.assertEqual(r['status'],'OPTIMAL_VERIFIED',r.get('message'));self.assertAlmostEqual(r['objective'],truth)
            self.assertLessEqual(r['best_bound'],truth+1e-8)

    def test_random_qp_known_kkt(self):
        rng=np.random.default_rng(90)
        for _ in range(20):
            n=4;x=rng.uniform(.5,4.5,n);A=rng.normal(size=(3,n));Q=np.diag(rng.uniform(.5,2,n));z=rng.uniform(.1,2,3);c=-Q@x-A.T@z
            m=Model.from_dict(dict(c=c.tolist(),Q=Q.tolist(),A=A.tolist(),row_upper=(A@x).tolist(),lower=[0]*n,upper=[5]*n))
            r=solve(m);self.assertEqual(r['status'],'OPTIMAL_VERIFIED');self.assertAlmostEqual(r['objective'],c@x+.5*x@Q@x,places=4)

    def test_nonconvex_and_miqp_rejected(self):
        with self.assertRaises(ValueError):model([0],Q=[[-1]])
        with self.assertRaises(ValueError):model([0],Q=[[1]],integer=[0])

    def test_pdhg(self):
        m=model([-1,-2]);r=solve(m,backend='pdhg-cpu',max_iter=1000)
        self.assertEqual(r['status'],'OPTIMAL_VERIFIED');self.assertAlmostEqual(r['objective'],-15)
        r=solve(load(ROOT/'data/verified/avgas.json'),backend='pdhg-cpu',max_iter=5000)
        self.assertEqual(r['status'],'OPTIMAL_VERIFIED')
        self.assertAlmostEqual(r['objective'],-7.75,places=2)

    def test_limits(self):
        r=solve(load(ROOT/'data/verified/flugpl.json'),max_nodes=0)
        self.assertEqual(r['status'],'LIMIT_REACHED');self.assertNotIn('x',r)
        r=solve(load(ROOT/'data/verified/qp_example.json'),max_iter=1)
        self.assertEqual(r['status'],'LIMIT_REACHED')

    def test_mps_and_qps(self):
        m_lp=load(ROOT/'data/verified/afiro.mps')
        self.assertEqual(m_lp.name,'AFIRO')
        self.assertEqual(len(m_lp.c),32)
        m_qp=load(ROOT/'data/verified/qp_example.qps')
        self.assertEqual(m_qp.name,'QPexample')
        self.assertIsNotNone(m_qp.Q)

    def test_honest_failure_statuses(self):
        """Documented honest failures: unresolvable or ill-conditioned instances must not return OPTIMAL."""
        r_blend=solve(load(ROOT/'data/verified/blend.mps'))
        self.assertEqual(r_blend['status'],'NUMERICAL_FAILURE')
        self.assertIn('Singular',r_blend.get('message',''))

        r_flug=solve(load(ROOT/'data/verified/flugpl.mps'),max_nodes=50,time_limit=10.0)
        self.assertEqual(r_flug['status'],'NUMERICAL_FAILURE')
        self.assertIn('Unresolved LP',r_flug.get('message',''))

    def test_fraction_bound_for_any_multiplier(self):
        m=model([-2,3]);G,h,_=m.inequalities();rng=np.random.default_rng(9)
        for _ in range(15):self.assertLessEqual(safe_lower_bound(m,rng.uniform(0,5,len(h))),Fraction(-10))

if __name__=='__main__':unittest.main(verbosity=2)
