import argparse, json, sys
from pathlib import Path
from . import load, solve, build_refinery_twin, __version__

def format_trust_report(r):
    lines = [
        "=" * 80,
        "SOV-OPT NUMERICAL TRUST REPORT",
        "A Verified Sovereign Optimization Core for MRPL PS 26119",
        "=" * 80,
        f"Model Name:        {r.get('model_name', 'Unknown')}",
        f"Problem Class:     {r.get('dispatch', {}).get('problem_class', 'Unknown')}",
        f"Dimensions:        {r.get('variables', '-')} vars, {r.get('rows', '-')} constraints, {r.get('nonzeros', '-')} nonzeros",
        f"Solver Version:    sovopt {r.get('solver_version', __version__)}",
        f"Method / Backend:  {r.get('dispatch', {}).get('method', r.get('algorithm', 'simplex'))} ({r.get('backend', 'cpu')})",
        f"Execution Time:    {r.get('elapsed_seconds', 0.0):.4f} seconds",
        "-" * 80,
        f"TERMINAL STATUS:   {r.get('status')}",
        f"Objective Sense:   {r.get('objective_sense', 'minimize')}",
        f"Objective Value:   {r.get('objective') if r.get('objective') is not None else 'N/A'}",
        f"Certified Bound:   {r.get('best_bound') if r.get('best_bound') is not None else 'N/A'}",
        f"Relative Gap:      {r.get('relative_gap') if r.get('relative_gap') is not None else 'N/A'}",
        "-" * 80,
        "NUMERICAL VERIFICATION & INVARIANTS:",
    ]
    v = r.get('verification', {})
    if v:
        pr = v.get('primal_residual')
        dr = v.get('dual_residual')
        ir = v.get('integrality_residual')
        kkt = v.get('kkt_passed')
        lines.append(f"  Primal Residual (r_p):      {pr:.2e}  [{'PASS' if pr is not None and pr <= 1e-4 else 'FAIL'}]" if pr is not None else "  Primal Residual (r_p):      N/A")
        lines.append(f"  Dual Residual (r_d):        {dr:.2e}  [{'PASS' if dr is not None and dr <= 1e-4 else 'FAIL'}]" if dr is not None else "  Dual Residual (r_d):        N/A")
        lines.append(f"  Integrality Violation (r_I):{ir:.2e}  [{'PASS' if ir is not None and ir <= 1e-4 else 'FAIL'}]" if ir is not None else "  Integrality Violation (r_I):N/A")
        lines.append(f"  KKT Stationarity / Feas:    {'VERIFIED' if kkt else 'NOT MET'}")
        if v.get('optimality_basis'):
            lines.append(f"  Optimality Basis:           {v['optimality_basis']}")
    if r.get('farkas_certificate'):
        lines.append("  Farkas Infeasibility Ray:   EXACT CERTIFIED (y >= 0, y^T A <= 0, y^T b > 0)")
    if r.get('dispatch', {}).get('rationale'):
        lines.append(f"  Dispatch Rationale:         {r['dispatch']['rationale']}")
    lines.append("=" * 80)
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser(description='SOV-OPT Sovereign Numerical Optimization Core (MRPL PS 26119)')
    p.add_argument('model', nargs='?', default=None, help='Path to model JSON/MPS file')
    p.add_argument('--refinery-twin', choices=['lp', 'milp', 'qp', 'infeasible'], default=None, help='Run built-in MRPL refinery planning twin variant')
    p.add_argument('--backend', choices=['cpu', 'pdhg-cpu', 'pdhg-cuda'], default='cpu', help='Solver hardware/execution backend')
    p.add_argument('--method', choices=['auto', 'simplex', 'dual-simplex', 'ipm', 'bb', 'pdhg-cpu', 'pdhg-gpu'], default='auto', help='Algorithm selection (default: auto)')
    p.add_argument('--tol', type=float, default=1e-7, help='Numerical tolerance')
    p.add_argument('--output', help='Save solve results to output file')
    p.add_argument('--no-scaling', action='store_true', help='Disable Ruiz equilibrium scaling')
    p.add_argument('--report', action='store_true', help='Print formatted Numerical Trust Report instead of JSON')
    p.add_argument('--format', choices=['json', 'report'], default=None, help='Output format')
    a = p.parse_args()

    if a.refinery_twin:
        model = build_refinery_twin(a.refinery_twin)
    elif a.model:
        try:
            model = load(a.model)
        except (ValueError, KeyError, OSError) as e:
            err = {'status': 'INVALID_MODEL', 'message': str(e)}
            print(json.dumps(err, indent=2))
            return 2
    else:
        p.error("Must provide either a model file path or --refinery-twin.")

    try:
        r = solve(model, backend=a.backend, tol=a.tol, method=a.method, scaling=not a.no_scaling)
    except (ValueError, KeyError, OSError) as e:
        r = {'status': 'INVALID_MODEL', 'message': str(e)}

    use_report = a.report or (a.format == 'report')
    output_text = format_trust_report(r) if use_report else json.dumps(
        r, indent=2, allow_nan=False,
        default=lambda o: o.item() if hasattr(o, 'item') else (o.tolist() if hasattr(o, 'tolist') else str(o))
    )

    if a.output:
        Path(a.output).parent.mkdir(parents=True, exist_ok=True)
        Path(a.output).write_text(output_text + '\n')

    print(output_text)
    return 0 if r.get('status') in ('OPTIMAL_VERIFIED', 'INFEASIBLE_CERTIFIED') else 2

if __name__ == '__main__':
    sys.exit(main())
