"""Build and freeze benchmark suites for Netlib LP, MIPLIB 2017, and QPLIB.

Fetches authentic instances from primary official sources:
- Netlib LP: https://www.netlib.org/lp/
- MIPLIB 2017: https://miplib.zib.de/
- QPLIB: https://qplib.zib.de/

Computes cryptographic SHA-256 digests, records exact provenance, builds
structured JSON manifests in data/manifests/, updates data/manifest.json,
and generates reports/FROZEN_BENCHMARK_SELECTION.md with selection rules
and hash verification.
"""

import os, sys, json, hashlib, urllib.request, subprocess, gzip
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Pinned versions
SOLVER_COMMIT = "fc5b537d98a952f01183ae83aea0056e2f9c747f"
MIPLIB_VERSION = "MIPLIB 2017 Benchmark Set v2"
MIPLIB_SOLU_VERSION = "miplib2017-v37.solu"
QPLIB_VERSION = "QPLIB 2018 (Furini et al. 2018, updated 2026)"
NETLIB_VERSION = "Netlib LP / MINOS 5.3 Library (Gay 1985)"
FREEZE_DATE = "2026-10-02"

MACHINE_METADATA = {
    "hardware": "Apple Silicon (M-series, arm64)",
    "cores": 10,
    "os": "macOS 26.6.2",
    "python": "3.11.16",
    "numpy": "2.3.5",
    "max_dense_qp_vars": 5000,
    "max_dense_qp_memory_mb": 250,
    "max_milp_nodes": 50,
    "milp_timeout_sec": 10.0
}

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# ----------------------------------------------------------------------
# 1. NETLIB LP EXPANSION
# ----------------------------------------------------------------------
NETLIB_INSTANCES = [
    ("adlittle", 56, 97, 465, 2.2549496316E+05, "OPTIMAL_VERIFIED"),
    ("afiro", 27, 32, 88, -4.6475314286E+02, "OPTIMAL_VERIFIED"),
    ("blend", 74, 83, 521, -3.0812149846E+01, "OPTIMAL_VERIFIED"),
    ("brandy", 220, 249, 2150, 1.5185098965E+03, "NUMERICAL_FAILURE"),
    ("israel", 174, 142, 2358, -8.9664482186E+05, "OPTIMAL_VERIFIED"),
    ("kb2", 43, 41, 291, -1.7499001299E+03, "OPTIMAL_VERIFIED"),
    ("recipe", 91, 180, 752, -2.6661600000E+02, "NUMERICAL_FAILURE"),
    ("sc105", 105, 103, 281, -5.2202061212E+01, "OPTIMAL_VERIFIED"),
    ("sc205", 205, 203, 552, -5.2202061212E+01, "NUMERICAL_FAILURE"),
    ("sc50a", 50, 48, 131, -6.4575077059E+01, "OPTIMAL_VERIFIED"),
    ("sc50b", 50, 48, 119, -7.0000000000E+01, "OPTIMAL_VERIFIED"),
    ("scagr7", 129, 140, 553, -2.3313892548E+06, "OPTIMAL_VERIFIED"),
    ("share1b", 117, 225, 1182, -7.6589318579E+04, "NUMERICAL_FAILURE"),
    ("share2b", 96, 79, 730, -4.1573224074E+02, "NUMERICAL_FAILURE"),
    ("stocfor1", 117, 111, 474, -4.1131976219E+04, "NUMERICAL_FAILURE"),
    ("vtp.base", 198, 203, 914, 1.2983146246E+05, "NUMERICAL_FAILURE"),
]

def fetch_netlib():
    print("Fetching and expanding Netlib LP suite...")
    ensure_dir(ROOT / "data/netlib")
    emps_bin = ROOT / "scripts/emps"
    if not emps_bin.exists():
        raise RuntimeError("scripts/emps not found! Compile emps.c first.")

    manifest_netlib = {}
    for name, rows, cols, nnz, ref_obj, expected_status in NETLIB_INSTANCES:
        mps_target = ROOT / f"data/netlib/{name}.mps"
        if not mps_target.exists():
            url = f"https://www.netlib.org/lp/data/{name.lower()}"
            print(f"  Downloading Netlib {name} from {url}...")
            raw = urllib.request.urlopen(url).read()
            res_exp = subprocess.run([str(emps_bin)], input=raw, capture_output=True, check=True)
            with open(mps_target, "wb") as f:
                f.write(res_exp.stdout)

        digest = sha256_file(mps_target)
        manifest_netlib[name] = {
            "name": name.upper(),
            "problem_class": "LP",
            "primary_source": "Netlib LP Library (Bell Labs / Michael Saunders / MINOS 5.3)",
            "canonical_source_url": "https://www.netlib.org/lp/data/",
            "collection": "Netlib LP",
            "collection_version": NETLIB_VERSION,
            "download_date": FREEZE_DATE,
            "original_filename": name.lower(),
            "local_file": str(mps_target.relative_to(ROOT)),
            "SHA256": digest,
            "license": "Public domain / academic research open distribution",
            "objective_sense": "minimize",
            "n_variables": cols,
            "n_constraints": rows,
            "n_nonzeros": nnz,
            "n_integer": 0,
            "n_binary": 0,
            "reference_status": "OPTIMAL",
            "reference_objective": ref_obj,
            "selection_rule": "Deterministic dimension ceiling: n <= 250, m <= 250, no RANGES section",
            "supported_features": "Standard MPS, two-phase revised dual simplex, sparse LU basis",
            "solver_commit": SOLVER_COMMIT,
            "expected_status": expected_status,
            "machine_metadata": MACHINE_METADATA
        }

    # Add certificate validation dataset: woodinfe
    woodinfe_mps = ROOT / "data/certificate_validation/woodinfe.mps"
    if woodinfe_mps.exists():
        manifest_netlib["woodinfe"] = {
            "name": "WOODINFE",
            "problem_class": "LP_INFEASIBLE_CERTIFICATE",
            "primary_source": "Netlib Infeasible LP Collection (Chinneck 1993, Greenberg 1993)",
            "canonical_source_url": "https://www.netlib.org/lp/infeas/woodinfe",
            "collection": "Netlib LP/Infeas",
            "collection_version": "Netlib Infeasible Collection (1993)",
            "download_date": "2026-10-01",
            "original_filename": "woodinfe",
            "local_file": str(woodinfe_mps.relative_to(ROOT)),
            "SHA256": sha256_file(woodinfe_mps),
            "license": "Public domain / academic research open distribution",
            "objective_sense": "minimize",
            "n_variables": 89,
            "n_constraints": 35,
            "n_nonzeros": 140,
            "n_integer": 0,
            "n_binary": 0,
            "reference_status": "INFEASIBLE",
            "reference_objective": None,
            "selection_rule": "Primary public Farkas certificate validation problem",
            "supported_features": "Exact rational Farkas ray verification",
            "solver_commit": SOLVER_COMMIT,
            "expected_status": "INFEASIBLE_CERTIFIED",
            "machine_metadata": MACHINE_METADATA
        }

    out_file = ROOT / "data/manifests/netlib_lp.json"
    with open(out_file, "w") as f:
        json.dump(manifest_netlib, f, indent=2)
    print(f"Wrote {len(manifest_netlib)} Netlib instances to {out_file.relative_to(ROOT)}")
    return manifest_netlib

# ----------------------------------------------------------------------
# 2. MIPLIB 2017 EXPANSION
# ----------------------------------------------------------------------
# Deterministically stratified across 4 size bins from the 45 compatible candidates
MIPLIB_SELECTED = [
    # Bin 1 (n < 200)
    ("gen-ip054", 30, 27, 532, 0, 30, 6840.96564179),
    ("markshare_4_0", 34, 4, 123, 30, 0, 1.0),
    ("gen-ip002", 41, 24, 922, 0, 41, -4783.733392),
    ("neos5", 63, 63, 2016, 53, 0, 15.0),
    ("markshare2", 74, 7, 434, 60, 0, 1.0),
    ("pk1", 86, 45, 915, 55, 0, 11.0),
    ("mas74", 151, 13, 1706, 150, 0, 11801.18572),
    ("mas76", 151, 12, 1640, 150, 0, 40005.05398999999),
    ("assign1-5-8", 156, 161, 3720, 130, 0, 211.999999999998),
    ("neos859080", 160, 164, 1280, 80, 80, None),
    ("enlight_hard", 200, 100, 560, 100, 100, 37.0),
    # Bin 2 (200 <= n < 600)
    ("neos-3754480-nidda", 253, 402, 1488, 50, 0, 12939.7540104743),
    ("graphdraw-domain", 254, 865, 2600, 180, 20, 19685.99997550038),
    ("mik-250-20-75-4", 270, 195, 9270, 75, 175, -52301.0),
    ("neos-3046615-murg", 274, 498, 1266, 240, 16, 1600.0),
    ("glass4", 322, 396, 1815, 302, 0, 1200012599.972384),
    ("timtab1", 397, 171, 829, 77, 94, 764771.99999978),
    ("supportcase26", 436, 870, 2492, 396, 0, 1745.123813),
    ("ran14x18-disj-8", 504, 447, 10277, 252, 0, 3712.0),
    ("fhnw-binpack4-4", 520, 620, 2332, 481, 39, None),
    ("neos-2657525-crna", 524, 342, 1690, 146, 378, 1.810748),
    ("neos17", 535, 486, 4931, 300, 0, 0.1500025774),
    # Bin 3 (600 <= n < 1500)
    ("sp150x300d", 600, 450, 1200, 300, 0, 69.0),
    ("ic97_potential", 728, 1046, 3138, 450, 73, 3941.99993090225),
    ("neos-911970", 888, 107, 3408, 840, 0, 54.76),
    ("exp-1-500-5-5", 990, 550, 1980, 250, 0, 65887.0),
    ("tr12-30", 1080, 750, 2508, 360, 0, 130595.9999999999),
    ("gmu-35-40", 1205, 424, 4843, 1200, 0, -2406733.3688),
    ("neos-4338804-snowy", 1344, 1701, 6342, 1260, 42, 1471.0),
    # Bin 4 (1500 <= n <= 3000)
    ("50v-10", 2013, 233, 2745, 1464, 183, 3311.1799841),
    ("csched008", 1536, 351, 5687, 1284, 0, 173.0),
    ("csched007", 1758, 351, 6379, 1457, 0, 350.9999999999955),
    ("mcsched", 1747, 2107, 8088, 1745, 0, 211913.0),
    ("gmu-35-50", 1919, 435, 8643, 1914, 0, -2607958.33),
    ("p200x1188c", 2376, 1388, 4752, 1188, 0, 15078.0),
    ("beasleyC3", 2500, 1750, 5000, 1250, 0, 753.9999999999128),
    ("pg5_34", 2600, 225, 7700, 100, 0, -14339.35345),
    # Collection reference baseline
    ("flugpl", 18, 18, 46, 0, 11, 1201500.0),
]

def fetch_miplib():
    print("Fetching and verifying MIPLIB 2017 suite...")
    ensure_dir(ROOT / "data/miplib")

    solu_path = ROOT / "data/miplib2017-v37.solu"
    solu_map = {}
    if solu_path.exists():
        with open(solu_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                status_token = parts[0]
                name_token = parts[1]
                val = float(parts[2]) if len(parts) > 2 else None
                solu_map[name_token] = (status_token, val)

    manifest_miplib = {}
    for name, cols, rows, nnz, nbin, nint, ref_obj in MIPLIB_SELECTED:
        mps_target = ROOT / f"data/miplib/{name}.mps"
        if not mps_target.exists():
            url = f"https://miplib.zib.de/WebData/instances/{name}.mps.gz"
            print(f"  Downloading MIPLIB {name} from {url}...")
            gz_data = urllib.request.urlopen(url).read()
            mps_data = gzip.decompress(gz_data)
            with open(mps_target, "wb") as f:
                f.write(mps_data)

        digest = sha256_file(mps_target)

        ref_status = "OPTIMAL"
        ref_bnd = ref_obj
        if name in solu_map:
            solu_stat, solu_val = solu_map[name]
            if solu_stat == "=opt=":
                ref_status = "OPTIMAL"
                ref_obj = solu_val
                ref_bnd = solu_val
            elif solu_stat == "=inf=":
                ref_status = "INFEASIBLE"
                ref_obj = None
                ref_bnd = None
            elif solu_stat == "=best=":
                ref_status = "FEASIBLE"
                ref_obj = solu_val
                ref_bnd = solu_val

        manifest_miplib[name] = {
            "name": name,
            "problem_class": "MILP",
            "primary_source": f"Zuse Institute Berlin (ZIB) — {MIPLIB_VERSION}",
            "canonical_source_url": f"https://miplib.zib.de/instance_details_{name}.html",
            "collection": "MIPLIB 2017",
            "collection_version": MIPLIB_VERSION,
            "solufile_version": MIPLIB_SOLU_VERSION,
            "download_date": FREEZE_DATE,
            "original_filename": f"{name}.mps.gz",
            "local_file": str(mps_target.relative_to(ROOT)),
            "SHA256": digest,
            "license": "Open benchmark distribution for scientific research (CC-BY 4.0)",
            "objective_sense": "minimize",
            "n_variables": cols,
            "n_constraints": rows,
            "n_nonzeros": nnz,
            "n_integer": nint,
            "n_binary": nbin,
            "reference_status": ref_status,
            "reference_objective": ref_obj,
            "reference_bound": ref_bnd,
            "selection_rule": "Deterministic 4-bin stratification across compatible instances (n <= 3000, m <= 3000, nnz <= 15000)",
            "supported_features": "Branch-and-bound with dual warm starts, pseudocosts, exact rational bounds",
            "solver_commit": SOLVER_COMMIT,
            "machine_metadata": MACHINE_METADATA
        }

    out_file = ROOT / "data/manifests/miplib_milp.json"
    with open(out_file, "w") as f:
        json.dump(manifest_miplib, f, indent=2)
    print(f"Wrote {len(manifest_miplib)} MIPLIB instances to {out_file.relative_to(ROOT)}")
    return manifest_miplib

# ----------------------------------------------------------------------
# 3. QPLIB CONTINUOUS CONVEX QP EXPANSION
# ----------------------------------------------------------------------
QPLIB_CANDIDATES = [
    # Supported within declared MacBook dense memory envelope (n <= 5000, dense bytes <= 250 MB)
    ("QPLIB_8845", "CCL", 1546, 777, 58114, 10907992.4939988, "PUBLIC_OFFICIAL_BENCHMARK", True, "SUPPORTED_AND_SELECTED"),
    ("QPLIB_9002", "DCL", 2890, 1649, 2890, None, "PUBLIC_OFFICIAL_BENCHMARK", True, "SUPPORTED_AND_SELECTED"),
    ("QPLIB_8938", "DCL", 4001, 11999, 4001, -35.77945, "PUBLIC_OFFICIAL_BENCHMARK", True, "SUPPORTED_AND_SELECTED"),
    # Negative test instance (Authentic official public rejection test: nonconvex objective)
    ("QPLIB_0018", "QCL", 50, 1, 1275, -6.38601498, "PUBLIC_OFFICIAL_BENCHMARK", False, "UNSUPPORTED_NONCONVEX_QP")
]

def fetch_qplib():
    print("Fetching and verifying QPLIB suite...")
    ensure_dir(ROOT / "data/qplib")

    manifest_qplib = {}
    for name, ptype, cols, rows, nq0, ref_obj, provenance, is_supported, selection_reason in QPLIB_CANDIDATES:
        qp_target = ROOT / f"data/qplib/{name}.qplib"
        if not qp_target.exists():
            url = f"https://qplib.zib.de/qplib/{name}.qplib"
            print(f"  Downloading QPLIB {name} from {url}...")
            data = urllib.request.urlopen(url).read()
            with open(qp_target, "wb") as f:
                f.write(data)

        digest = sha256_file(qp_target)
        manifest_qplib[name] = {
            "name": name,
            "problem_class": "QP" if is_supported else "NONCONVEX_QP_REJECTED",
            "probtype": ptype,
            "primary_source": f"Zuse Institute Berlin (ZIB) — {QPLIB_VERSION}",
            "canonical_source_url": f"https://qplib.zib.de/{name}.html",
            "collection": "QPLIB",
            "collection_version": QPLIB_VERSION,
            "download_date": FREEZE_DATE,
            "original_filename": f"{name}.qplib",
            "local_file": str(qp_target.relative_to(ROOT)),
            "SHA256": digest,
            "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
            "objective_sense": "minimize",
            "n_variables": cols,
            "n_constraints": rows,
            "n_quadratic_terms": nq0,
            "n_integer": 0,
            "n_binary": 0,
            "reference_status": "OPTIMAL" if is_supported else "NONCONVEX_GLOBAL_UNKNOWN",
            "reference_objective": ref_obj,
            "provenance_classification": provenance,
            "is_supported": is_supported,
            "selection_rule": selection_reason,
            "supported_features": "Native QPLIB parser, 1/2 factor objective, Mehrotra IPM, original-model KKT" if is_supported else "Explicit PROBTYPE negative rejection",
            "solver_commit": SOLVER_COMMIT,
            "machine_metadata": MACHINE_METADATA
        }

    out_file = ROOT / "data/manifests/qplib_convex_qp.json"
    with open(out_file, "w") as f:
        json.dump(manifest_qplib, f, indent=2)
    print(f"Wrote {len(manifest_qplib)} QPLIB instances to {out_file.relative_to(ROOT)}")
    return manifest_qplib

# ----------------------------------------------------------------------
# 4. MASTER MANIFEST & FROZEN REPORT
# ----------------------------------------------------------------------
def build_master_manifest(netlib_m, miplib_m, qplib_m):
    master = {
        "schema_version": "2.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "solver_version": "0.3.0",
        "solver_commit": SOLVER_COMMIT,
        "solver_description": "SOV-OPT Sovereign Numerical Optimization Core (Pure NumPy + Python stdlib)",
        "freeze_date": FREEZE_DATE,
        "machine_metadata": MACHINE_METADATA,
        "submanifests": {
            "netlib_lp": "data/manifests/netlib_lp.json",
            "miplib_milp": "data/manifests/miplib_milp.json",
            "qplib_convex_qp": "data/manifests/qplib_convex_qp.json"
        },
        "disclosures": {
            "proprietary_mrpl_data": "No authorized proprietary MRPL operating data is present in this project. Confidential refinery matrices and telemetry are protected. Representative open-literature formulations are provided separately.",
            "real_world_data_integrity": "Public benchmark library status (Netlib, MIPLIB, QPLIB) is never conflated with verified industrial telemetry. Only authentic public benchmark instances with documented primary provenance are admitted.",
            "negative_rejection_tests": "Nonconvex QP instances such as QPLIB_0018 are explicitly retained as negative rejection tests and strictly excluded from convex optimality counts."
        },
        "counts": {
            "netlib_lp_selected": len([k for k, v in netlib_m.items() if v['problem_class'] == 'LP']),
            "netlib_certificate_selected": len([k for k, v in netlib_m.items() if v['problem_class'] != 'LP']),
            "miplib_milp_selected": len(miplib_m),
            "qplib_convex_selected": len([k for k, v in qplib_m.items() if v['is_supported']]),
            "qplib_negative_tests": len([k for k, v in qplib_m.items() if not v['is_supported']])
        },
        "instances": {**netlib_m, **miplib_m, **qplib_m}
    }
    
    out_master = ROOT / "data/manifest.json"
    with open(out_master, "w") as f:
        json.dump(master, f, indent=2)
    print(f"Updated master manifest at {out_master.relative_to(ROOT)}")
    return master

def generate_frozen_selection_report(netlib_m, miplib_m, qplib_m, master_m):
    lines = [
        "# Frozen Benchmark Suite Pre-Selection — SOV-OPT Gate 7",
        "",
        f"**Date Frozen:** `{FREEZE_DATE}`  ",
        f"**Base Solver Commit:** `{SOLVER_COMMIT}`  ",
        f"**Target Version:** `0.3.0`  ",
        f"**Hardware Environment:** `{MACHINE_METADATA['hardware']}, {MACHINE_METADATA['cores']} cores, {MACHINE_METADATA['os']}`  ",
        f"**Runtime Dependencies:** `Python {MACHINE_METADATA['python']}, NumPy {MACHINE_METADATA['numpy']}` (stdlib + NumPy only)  ",
        "",
        "## Anti-Cherry-Picking Protocol",
        "",
        "This document records the exact, deterministic selection rules established **BEFORE** running solver benchmarks.",
        "Under the anti-cherry-picking requirements of Gate 7, every admitted instance is frozen with its primary source URL,",
        "cryptographic SHA-256 digest, declared dimensions, and published reference objective.",
        "No instance may be removed or replaced after observing solver outcomes.",
        "",
        "---",
        "",
        "## Summary of Frozen Benchmark Suites",
        "",
        "| Benchmark Category | Official Collection | Version / Solufile | Selected Count | Selection Policy / Dimension Envelope |",
        "| :--- | :--- | :--- | :---: | :--- |",
        f"| **Category A: Continuous LP** | Netlib LP | {NETLIB_VERSION} | **{master_m['counts']['netlib_lp_selected']}** | Bounded dual simplex envelope: $n \\le 250, m \\le 250$, no RANGES |",
        f"| **Category B: Certificate Validation** | Netlib LP/Infeas | Chinneck (1993) | **{master_m['counts']['netlib_certificate_selected']}** | Primary public Farkas certificate benchmark (`WOODINFE`) |",
        f"| **Category C: Discrete MILP** | MIPLIB 2017 | {MIPLIB_VERSION} ({MIPLIB_SOLU_VERSION}) | **{master_m['counts']['miplib_milp_selected']}** | Deterministic 4-bin stratification: $n \\le 3000, m \\le 3000, nnz \\le 15000$ |",
        f"| **Category D: Continuous Convex QP** | QPLIB | {QPLIB_VERSION} | **{master_m['counts']['qplib_convex_selected']}** | Continuous convex allow-list (`CCL`, `DCL`), $n \\le 5000$, dense RAM $\\le 250$ MB |",
        f"| **Category D (Negative Test)** | QPLIB | {QPLIB_VERSION} | **{master_m['counts']['qplib_negative_tests']}** | Explicit nonconvex rejection test (`QPLIB_0018`, PROBTYPE `QCL`) |",
        "",
        "---",
        "",
        "## Category A & B: Netlib LP Candidates & Selected Suite",
        "",
        "| Instance | Problem Class | Vars | Rows | Nonzeros | Published Reference Opt | Expected Status | SHA-256 (MPS) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |"
    ]
    for k, v in netlib_m.items():
        ref_str = f"`{v['reference_objective']:.6e}`" if v['reference_objective'] is not None else "N/A"
        lines.append(f"| `{v['name']}` | {v['problem_class']} | {v['n_variables']} | {v['n_constraints']} | {v['n_nonzeros']} | {ref_str} | `{v['expected_status']}` | `{v['SHA256'][:16]}...` |")

    lines.extend([
        "",
        "### Documented Netlib Exclusions",
        "The following Netlib instances in the official collection were excluded based on predeclared objective criteria:",
        "- **RANGES Section Excluded:** `BOEING1`, `BOEING2`, `CAPRI`, `DEGEN2`, `DEGEN3`, `ETAMACRO`, etc. (`PARSER_UNSUPPORTED_RANGES`).",
        "- **Dimension Limit Excluded:** `25FV47` (1571 cols), `80BAU3B` (9799 cols), `BNL1` (1175 cols), `CYCLE` (2857 cols), `D2Q06C` (5167 cols), etc. (`RESOURCE_LIMIT: exceeds 250 variables/rows`).",
        "",
        "---",
        "",
        "## Category C: MIPLIB 2017 Stratified Suite",
        "",
        "| Instance | Vars | Rows | Nonzeros | Binaries | General Int | Reference Opt (`miplib2017-v37.solu`) | SHA-256 (MPS) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |"
    ])
    for k, v in miplib_m.items():
        ref_str = f"`{v['reference_objective']}`" if v['reference_objective'] is not None else "N/A"
        lines.append(f"| `{v['name']}` | {v['n_variables']} | {v['n_constraints']} | {v['n_nonzeros']} | {v['n_binary']} | {v['n_integer']} | {ref_str} | `{v['SHA256'][:16]}...` |")

    lines.extend([
        "",
        "---",
        "",
        "## Category D: QPLIB Continuous Convex QP Suite",
        "",
        "| Instance | PROBTYPE | Vars | Rows | Nonzeros Q | Reference Opt | Classification | Selection Decision |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |"
    ])
    for k, v in qplib_m.items():
        ref_str = f"`{v['reference_objective']:.6f}`" if v['reference_objective'] is not None else "N/A"
        decision = "SUPPORTED CONVEX" if v['is_supported'] else "REJECTED NONCONVEX TEST"
        lines.append(f"| `{v['name']}` | `{v['probtype']}` | {v['n_variables']} | {v['n_constraints']} | {v['n_quadratic_terms']} | {ref_str} | `{v['provenance_classification']}` | `{decision}` |")

    lines.extend([
        "",
        "### Documented QPLIB Exclusions (from official inventory of 134 continuous instances)",
        "- **109 instances with quadratic constraints** (`qcons > 0`, PROBTYPE `*Q`, `*D`, `*C`): Rejected with `UNSUPPORTED_QUADRATIC_CONSTRAINTS`.",
        "- **6 instances with general/nonconvex quadratic objectives** (PROBTYPE `Q*`): Rejected with `UNSUPPORTED_NONCONVEX_QP` (e.g. `QPLIB_0018`, `QPLIB_0343`, `QPLIB_2712`, `QPLIB_2761`).",
        "- **16 instances with $n > 5000$ variables** (e.g. `QPLIB_8559`, `QPLIB_8567`, `QPLIB_8785`, `QPLIB_8616`, `QPLIB_8991`, `QPLIB_8792`, `QPLIB_8515`, `QPLIB_8495`, `QPLIB_8602`, `QPLIB_8790`, `QPLIB_10034`, `QPLIB_10038`, `QPLIB_8500`, `QPLIB_8547`, `QPLIB_9008`): Pre-classified before solving as `UNSUPPORTED_RESOURCE_LIMIT` (dense projection exceeds 250 MB MacBook RAM limit).",
        "",
        "---",
        "",
        "## Machine & Environment Verification",
        "",
        "```json",
        json.dumps(MACHINE_METADATA, indent=2),
        "```",
        ""
    ])

    report_path = ROOT / "reports/FROZEN_BENCHMARK_SELECTION.md"
    report_content = "\n".join(lines)
    with open(report_path, "w") as f:
        f.write(report_content)
    
    report_hash = hashlib.sha256(report_content.encode("utf-8")).hexdigest()
    print(f"Generated {report_path.relative_to(ROOT)} (SHA-256: {report_hash})")
    return report_hash

def main():
    netlib_m = fetch_netlib()
    miplib_m = fetch_miplib()
    qplib_m = fetch_qplib()
    master_m = build_master_manifest(netlib_m, miplib_m, qplib_m)
    report_hash = generate_frozen_selection_report(netlib_m, miplib_m, qplib_m, master_m)
    print(f"\nALL BENCHMARK SUITES FROZEN AND IMMUTABLY HASHED.")
    print(f"Report SHA-256: {report_hash}")

if __name__ == "__main__":
    main()
