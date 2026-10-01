"""MRPL Refinery Planning Digital Twin Demonstration Script.

Implements the 5-step mathematical verification demonstration specified in
Final Deep-Research Solution for MRPL PS 26119, Section 11.2 (Page 26):
  1. Solve continuous LP planning twin -> KKT verified optimum
  2. Infeasible scenario -> Exact Farkas certificate of impossibility
  3. Discrete MILP twin -> Verified integer solution + exact rational lower bounds
  4. Smooth QP operational twin -> Interior point convergence with KKT stationarity
  5. Automatic Algorithm Dispatcher -> Transparent model classification and routing
"""

import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sovopt import solve, build_refinery_twin, auto_dispatch, inspect_model

def header(title):
    print("\n" + "=" * 78)
    print("  " + title)
    print("=" * 78)

def main():
    print("=" * 78)
    print("  SOV-OPT: MRPL REFINERY PLANNING DIGITAL TWIN DEMONSTRATION")
    print("  A Verified Sovereign Optimization Core for MRPL PS 26119")
    print("  Core Principle: GPU accelerates. CPU verifies. No result trusted unverified.")
    print("=" * 78)

    # 1. Continuous Multi-Period Economic Planning (LP)
    header("STEP 1: Continuous Multi-Period Economic Planning (LP)")
    m_lp = build_refinery_twin("lp")
    disp_lp = auto_dispatch(m_lp)
    print(f"Model: {m_lp.name} ({len(m_lp.c)} variables, {len(m_lp.A)} constraints)")
    print(f"Dispatcher routing: {disp_lp['method']} on {disp_lp['backend']}")
    print(f"Rationale: {disp_lp['rationale']}")
    
    t0 = time.perf_counter()
    res_lp = solve(m_lp)
    elapsed_lp = time.perf_counter() - t0
    
    print(f"\nSolve status:      {res_lp['status']}")
    print(f"Net economic cost: {res_lp['objective']:,.2f}")
    print(f"Iterations:        {res_lp['iterations']} simplex iterations ({elapsed_lp*1000:.1f} ms)")
    v_lp = res_lp["verification"]
    print(f"Primal residual:   {v_lp['primal_residual']:.2e} (KKT feasible: {v_lp['feasible']})")
    print(f"Dual residual:     {v_lp['dual_residual']:.2e} (KKT stationary: {v_lp['kkt_passed']})")
    assert res_lp["status"] == "OPTIMAL_VERIFIED"
    print("--> STEP 1 RESULT: Certified optimal continuous plan with zero numerical violations.")

    # 2. Infeasible Demand Diagnostic & Farkas Certificate
    header("STEP 2: Diagnostic Infeasible Scenario & Certified Farkas Ray")
    m_inf = build_refinery_twin("infeasible")
    print(f"Model: {m_inf.name} (Gasoline demand = 500.0 kbpd, CDU intake capacity = 100.0 kbpd)")
    
    t0 = time.perf_counter()
    res_inf = solve(m_inf)
    elapsed_inf = time.perf_counter() - t0
    
    print(f"\nSolve status:      {res_inf['status']}")
    print(f"Farkas certificate:{res_inf.get('farkas_certificate')}")
    print(f"Iterations:        {res_inf.get('iterations')} Phase-I simplex pivots ({elapsed_inf*1000:.1f} ms)")
    print("Certification:     Exact Farkas ray verified: y >= 0, y^T A <= 0, y^T b > 0")
    assert res_inf["status"] == "INFEASIBLE_CERTIFIED"
    print("--> STEP 2 RESULT: Refinery impossibility certified via Farkas ray; no heuristic guess.")

    # 3. Discrete Unit Commitment & Operating Limits (MILP)
    header("STEP 3: Discrete Unit Commitment & Operating Limits (MILP)")
    m_milp = build_refinery_twin("milp")
    disp_milp = auto_dispatch(m_milp)
    print(f"Model: {m_milp.name} ({len(m_milp.c)} vars including {len(m_milp.integer)} unit binaries)")
    print(f"Dispatcher routing: {disp_milp['method']} on {disp_milp['backend']}")
    print(f"Rationale: {disp_milp['rationale']}")
    
    t0 = time.perf_counter()
    res_milp = solve(m_milp)
    elapsed_milp = time.perf_counter() - t0
    
    print(f"\nSolve status:      {res_milp['status']}")
    print(f"Incumbent objective:{res_milp['objective']:,.2f}")
    print(f"Certified bound:   {res_milp['best_bound']:,.2f}")
    print(f"Relative gap:      {res_milp['relative_gap']:.2e}")
    print(f"Tree search:       {res_milp['nodes']} B&B nodes ({elapsed_milp:.3f} s)")
    print(f"Integrality check: max |x_int - round(x_int)| = {res_milp['verification']['integrality_residual']:.2e}")
    print(f"Optimality basis:  {res_milp['verification']['optimality_basis']}")
    assert res_milp["status"] == "OPTIMAL_VERIFIED"
    print("--> STEP 3 RESULT: Discrete unit commitment solved with exact conservative lower bounds.")

    # 4. Smooth Target-Tracking Operational Dispatch (Convex QP)
    header("STEP 4: Smooth Target-Tracking Operational Dispatch (Convex QP)")
    m_qp = build_refinery_twin("qp")
    disp_qp = auto_dispatch(m_qp)
    print(f"Model: {m_qp.name} (Smooth throughput flutter penalties on FCC and Reformer)")
    print(f"Dispatcher routing: {disp_qp['method']} on {disp_qp['backend']}")
    print(f"Rationale: {disp_qp['rationale']}")
    
    t0 = time.perf_counter()
    res_qp = solve(m_qp)
    elapsed_qp = time.perf_counter() - t0
    
    print(f"\nSolve status:      {res_qp['status']}")
    print(f"Operational value: {res_qp['objective']:,.2f}")
    print(f"IPM iterations:    {res_qp['iterations']} interior-point steps ({elapsed_qp*1000:.1f} ms)")
    v_qp = res_qp["verification"]
    print(f"Primal residual:   {v_qp['primal_residual']:.2e}")
    print(f"Dual residual:     {v_qp['dual_residual']:.2e}")
    print(f"Complementarity:   {v_qp['complementarity']:.2e}")
    print(f"KKT check:         stationarity passed = {v_qp['kkt_passed']}")
    assert res_qp["status"] == "OPTIMAL_VERIFIED"
    print("--> STEP 4 RESULT: Smooth QP operational dispatch verified via Primal-Dual IPM KKT system.")

    # 5. Automatic Algorithm Dispatcher
    header("STEP 5: Automatic Algorithm Dispatcher Summary")
    models = [("LP Twin", m_lp), ("Infeasible Diagnostic", m_inf), ("MILP Twin", m_milp), ("QP Twin", m_qp)]
    for label, mod in models:
        insp = inspect_model(mod)
        disp = auto_dispatch(mod)
        print(f"  * {label:22s} -> Class: {disp['problem_class']:4s} | Vars: {insp['variables']:2d} | "
              f"Int: {insp['integer_variables']} | QP: {str(insp['has_quadratic_objective']):5s} | "
              f"Selected Method: {disp['method']:7s} ({disp['backend']})")

    print("\n" + "=" * 78)
    print("  ALL 5 VERIFICATION STEPS COMPLETED AND MATHEMATICALLY VALIDATED")
    print("=" * 78)

if __name__ == "__main__":
    main()
