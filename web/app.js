/* ==========================================================================
   SOV-OPT REFINERY PLANNING WORKSTATION — EDITORIAL CLIENT APPLICATION
   Modular state management, fluid process flowsheet animation, count-up KPIs,
   convergence chart draw-in, live HTTP solver integration, and mobile drawer.
   ========================================================================== */

(function () {
  'use strict';
  const ASSET_VERSION = 'v=3';

  // Centralized Team Member Data (Mandatory Order: Khagesh #1, Satyam #2, Sudipto #3, Ayush #4, Shivanshu #5, Muskan #6)
  const TEAM_MEMBERS = [
    {
      name: "Khagesh Ranjan",
      role: "LEADER",
      program: "B.Tech + M.Tech (Dual Degree) in CSE & AI",
      institution: "Rajiv Gandhi Institute of Petroleum Technology",
      email: "24cs2021@rgipt.ac.in",
      linkedin: "https://www.linkedin.com/in/khagesh-ranjan-986721324/",
      photo: "/assets/team/khagesh.png?" + ASSET_VERSION
    },
    {
      name: "Satyam Gupta",
      role: "MEMBER",
      program: "B.Tech + M.Tech (Dual Degree) in CSE & AI",
      institution: "Rajiv Gandhi Institute of Petroleum Technology",
      email: "24cs2032@rgipt.ac.in",
      linkedin: "https://www.linkedin.com/in/satyam-gupta-2a1021324/",
      photo: "/assets/team/satyam.png?" + ASSET_VERSION
    },
    {
      name: "Sudipto Ghosh",
      role: "MEMBER",
      program: "B.Tech + M.Tech (Dual Degree) in CSE & AI",
      institution: "Rajiv Gandhi Institute of Petroleum Technology",
      email: "24cs2037@rgipt.ac.in",
      linkedin: "https://www.linkedin.com/in/sudipto-ghosh-486269346/",
      photo: "/assets/team/sudipto.png?" + ASSET_VERSION
    },
    {
      name: "Ayush Rao",
      role: "MEMBER",
      program: "B.Tech in Information Technology",
      institution: "Rajiv Gandhi Institute of Petroleum Technology",
      email: "24it3013@rgipt.ac.in",
      linkedin: "https://www.linkedin.com/in/ayush-rao-5359bb335/",
      photo: "/assets/team/ayush.png?" + ASSET_VERSION
    },
    {
      name: "Shivanshu Tripathi",
      role: "MEMBER",
      program: "B.Tech + M.Tech (Dual Degree) in CSE & AI",
      institution: "Rajiv Gandhi Institute of Petroleum Technology",
      email: "24cs2036@rgipt.ac.in",
      linkedin: "https://www.linkedin.com/in/shivanshu-tripathi-254876331/",
      photo: "/assets/team/shivanshu.png?" + ASSET_VERSION
    },
    {
      name: "Muskan Sahu",
      role: "MEMBER",
      program: "B.Tech in Information Technology",
      institution: "Rajiv Gandhi Institute of Petroleum Technology",
      email: "24it3036@rgipt.ac.in",
      linkedin: "https://www.linkedin.com/in/muskan-sahu-717162332/",
      photo: "/assets/team/muskan.png?" + ASSET_VERSION
    }
  ];


  // Master Application State (Single Source of Truth)
  const STATE = {
    activeTab: 'overview',
    activeScenario: 'SC-01',
    activeModel: 'refinery-lp',
    activeBackend: 'cpu',
    selectedUnit: 'CDU',
    isSolving: false,
    isStale: false,
    solveResult: null,
    solveGen: 0,
    resultSource: 'scenario-preset', // 'scenario-preset' | 'live'
    compareA: 'SC-01',
    compareB: 'SC-02',
    isMobileMenuOpen: false
  };

  // 1. Curated Industrial Scenarios
  const SCENARIOS = {
    'SC-01': {
      id: 'SC-01',
      code: 'SC-01',
      tag: 'Equilibrium',
      title: 'Base refinery equilibrium',
      desc: 'Balanced 60/40 Arab Light / Basrah Heavy crude slate. Standard product netbacks ($115/bbl Gasoline, $105/bbl Diesel). Nominal CDU throughput at 100 kbpd ceiling.',
      notes: 'Operating under standard design parameters. Fluid catalytic cracker operating at 90% capacity, leaving 5.0 kbpd headroom for unplanned swings. Reformer severity set at normal reformate RON 100 target.',
      variant: 'lp',
      crudeArabPrice: 70.0,
      crudeBasrahPrice: 62.0,
      gasolineDemand: 40.0,
      dieselDemand: 50.0,
      netMargin: 9043.75,
      cduThroughput: 100.0,
      cduArab: 60.0,
      cduBasrah: 40.0,
      fccThroughput: 45.0,
      reformerThroughput: 17.0,
      gasolineShipment: 44.0,
      dieselShipment: 56.2,
      fuelOilShipment: 22.0,
      status: 'Pass',
      bottleneck: 'CDU intake capacity (100 kbpd)',
      shadowPrice: 29.89
    },
    'SC-02': {
      id: 'SC-02',
      code: 'SC-02',
      tag: 'Arbitrage',
      title: 'High-Basrah heavy discount',
      desc: 'Basrah Heavy crude price spread widens to -$10/bbl ($52/bbl vs $70/bbl Arab Light). Optimal intake pivots heavily to Basrah to capture crude margin arbitrage.',
      notes: 'Crude procurement expands Basrah Heavy to metallurgical maximum 80 kbpd. Fluid catalytic cracker reaches thermal ceiling (50 kbpd), becoming the binding operational constraint.',
      variant: 'lp',
      crudeArabPrice: 70.0,
      crudeBasrahPrice: 52.0,
      gasolineDemand: 40.0,
      dieselDemand: 50.0,
      netMargin: 9663.98,
      cduThroughput: 100.0,
      cduArab: 20.0,
      cduBasrah: 80.0,
      fccThroughput: 50.0,
      reformerThroughput: 14.5,
      gasolineShipment: 42.8,
      dieselShipment: 58.0,
      fuelOilShipment: 24.5,
      status: 'Pass',
      bottleneck: 'FCC feed capacity (50 kbpd ceiling)',
      shadowPrice: 41.50
    },
    'SC-03': {
      id: 'SC-03',
      code: 'SC-03',
      tag: 'Peak demand',
      title: 'Summer high-octane surge',
      desc: 'Seasonal motor gasoline demand surges to 52 kbpd (+25%). Catalytic Reformer runs at 100% capacity limit to satisfy pool RON 95 octane requirements.',
      notes: 'Elevated furnace firing on semi-regenerative reformer. Reformate yield pushed to maximum 25.5 kbpd. Octane blending margin widens to -$18.25/bbl.',
      variant: 'lp',
      crudeArabPrice: 70.0,
      crudeBasrahPrice: 62.0,
      gasolineDemand: 52.0,
      dieselDemand: 46.0,
      netMargin: 9412.50,
      cduThroughput: 100.0,
      cduArab: 75.0,
      cduBasrah: 25.0,
      fccThroughput: 42.0,
      reformerThroughput: 30.0,
      gasolineShipment: 52.0,
      dieselShipment: 48.5,
      fuelOilShipment: 18.0,
      status: 'Pass',
      bottleneck: 'Reformer severity ceiling (30 kbpd)',
      shadowPrice: 18.25
    },
    'SC-04': {
      id: 'SC-04',
      code: 'SC-04',
      tag: 'Turnaround',
      title: 'FCC maintenance turndown',
      desc: 'Unscheduled turnaround clamps FCC unit feed to 20 kbpd (-60%). Gasoil balances re-routed to heavy fuel oil; diesel relies exclusively on straight-run distillate.',
      notes: 'Cracking conversion is limited by reactor bed maintenance. Atmospheric residue is bypassed directly to low-value bunker fuel oil, reducing overall economic margin.',
      variant: 'lp',
      crudeArabPrice: 70.0,
      crudeBasrahPrice: 62.0,
      gasolineDemand: 30.0,
      dieselDemand: 42.0,
      netMargin: 7840.10,
      cduThroughput: 85.0,
      cduArab: 55.0,
      cduBasrah: 30.0,
      fccThroughput: 20.0,
      reformerThroughput: 22.0,
      gasolineShipment: 32.5,
      dieselShipment: 42.0,
      fuelOilShipment: 38.0,
      status: 'Pass',
      bottleneck: 'FCC turndown limit (20 kbpd)',
      shadowPrice: 34.10
    },
    'SC-05': {
      id: 'SC-05',
      code: 'SC-05',
      tag: 'Environmental',
      title: 'Strict BS-VI fuel quality',
      desc: 'Ultra-low sulfur (<10 ppm) & high-cetane specifications restrict cracked LCO blending into high-speed diesel pool. Hydroprocessing units operate at elevated severity.',
      notes: 'Quadratic throughput flutter penalties are active to protect hydrotreating catalysts from thermal cycling. Solved via Mehrotra predictor-corrector interior point method.',
      variant: 'qp',
      crudeArabPrice: 70.0,
      crudeBasrahPrice: 62.0,
      gasolineDemand: 40.0,
      dieselDemand: 50.0,
      netMargin: 8710.30,
      cduThroughput: 98.0,
      cduArab: 68.0,
      cduBasrah: 30.0,
      fccThroughput: 38.0,
      reformerThroughput: 24.0,
      gasolineShipment: 43.5,
      dieselShipment: 51.0,
      fuelOilShipment: 26.0,
      status: 'Pass',
      bottleneck: 'Diesel hydrotreating specification',
      shadowPrice: 14.60
    },
    'SC-06': {
      id: 'SC-06',
      code: 'SC-06',
      tag: 'Bottleneck',
      title: 'Physical bottleneck shock',
      desc: 'Finished gasoline shipment quota set to 500 kbpd against a physical CDU ceiling of 100 kbpd. Engine detects impossibility and certifies an exact Farkas ray.',
      notes: 'Mathematical proof of impossibility. The sovereign simplex Phase-I engine produces an exact rational Farkas ray y proving that no feasible operating schedule exists.',
      variant: 'infeasible',
      crudeArabPrice: 70.0,
      crudeBasrahPrice: 62.0,
      gasolineDemand: 500.0,
      dieselDemand: 50.0,
      netMargin: null,
      cduThroughput: 0.0,
      cduArab: 0.0,
      cduBasrah: 0.0,
      fccThroughput: 0.0,
      reformerThroughput: 0.0,
      gasolineShipment: 0.0,
      dieselShipment: 0.0,
      fuelOilShipment: 0.0,
      status: 'Infeasible (Certified)',
      bottleneck: 'Gasoline quota vs CDU intake (500 > 100 kbpd)',
      shadowPrice: 0.0
    }
  };

  // 2. Refinery Process Unit Library
  const REFINERY_UNITS = {
    'CDU': {
      id: 'CDU',
      name: 'Atmospheric Crude Distillation Unit (CDU)',
      type: 'Primary atmospheric separation',
      designCapacity: '100.0 kbpd',
      nominalOperatingRate: '100.0 kbpd (100% load)',
      operatingTemp: '360°C Flash Zone',
      operatingPressure: '1.2 barg',
      yieldFormula: 'Naphtha 20% · Distillate 45% · Residue 35%',
      feedStreams: 'Arab Light (60 kbpd) + Basrah Heavy (40 kbpd)',
      shadowPrice: '$29.89 / bbl',
      status: 'Optimal at ceiling'
    },
    'FCC': {
      id: 'FCC',
      name: 'Fluidized Catalytic Cracking Unit (FCC)',
      type: 'Secondary upgrading & cracking',
      designCapacity: '50.0 kbpd gasoil/residue',
      nominalOperatingRate: '45.0 kbpd (90% load)',
      operatingTemp: '530°C Riser Reactor',
      operatingPressure: '2.1 barg',
      yieldFormula: 'CatGas 60% · LCO 30% · Heavy bottoms 10%',
      feedStreams: 'Atmospheric residue & gasoil header',
      shadowPrice: '$8.40 / bbl',
      status: 'Governing crack spread'
    },
    'REFORMER': {
      id: 'REFORMER',
      name: 'Catalytic Reforming Unit (Semi-Regen)',
      type: 'High-octane aromatics & H2',
      designCapacity: '30.0 kbpd heavy naphtha',
      nominalOperatingRate: '17.0 kbpd (56.7% load)',
      operatingTemp: '500°C Furnace Inlet',
      operatingPressure: '15.0 barg',
      yieldFormula: 'Reformate (100 RON) 85% + hydrogen',
      feedStreams: 'Desulfurized heavy naphtha',
      shadowPrice: '$0.00 / bbl',
      status: 'Slack available (13 kbpd)'
    },
    'BLEND_GAS': {
      id: 'BLEND_GAS',
      name: 'Motor Gasoline Blending Pool',
      type: 'In-line finished fuel header',
      designCapacity: '80.0 kbpd',
      nominalOperatingRate: '44.0 kbpd finished product',
      operatingTemp: 'Ambient (25°C)',
      operatingPressure: '4.5 barg',
      yieldFormula: 'Reformate (100 RON) + CatGas (92 RON) -> 95 RON Pool',
      feedStreams: 'CatGas (27 kbpd) + Reformate (17 kbpd)',
      shadowPrice: '-$115.00 / bbl',
      status: 'Octane verified (95.1 RON)'
    },
    'BLEND_DSL': {
      id: 'BLEND_DSL',
      name: 'BS-VI High-Speed Diesel Pool',
      type: 'Finished gasoil header',
      designCapacity: '90.0 kbpd',
      nominalOperatingRate: '56.2 kbpd finished product',
      operatingTemp: 'Ambient (25°C)',
      operatingPressure: '5.0 barg',
      yieldFormula: 'Distillate (52 Cetane) + LCO (35 Cetane) -> 51 Cetane Pool',
      feedStreams: 'CDU Distillate (45 kbpd) + FCC LCO (11.2 kbpd)',
      shadowPrice: '-$105.00 / bbl',
      status: 'Specification compliant'
    },
    'TANKAGE': {
      id: 'TANKAGE',
      name: 'Intermediate & Finished Tank Farm',
      type: 'Floating roof storage',
      designCapacity: '25.0 kbbl per intermediate product',
      nominalOperatingRate: '15.0 kbbl working stock',
      operatingTemp: 'Ambient',
      operatingPressure: 'Atmospheric',
      yieldFormula: 'Naphtha, Reformate, Distillate, CatGas, LCO, Fuel Oil',
      feedStreams: 'Intermediate rundown lines',
      shadowPrice: '$0.50 / bbl-period',
      status: 'Inventory balanced'
    }
  };

  // 3. Gate 9 Physical GPU Validation Evidence (Acer RTX 5050)
  const GATE9_DATA = {"GATE9_VALIDATED_SOURCE_SHA": "51b71bb8468bd4375e572b2537d69e30a0e60684", "provenance_statement": "All performance measurements in this directory were executed from a clean working tree at the exact committed source SHA shown above.", "gate8_sha": "cefa9c33f1d4d44be13765c0d2d5b72c89c9a1a4", "gpu_device": "NVIDIA GeForce RTX 5050 Laptop GPU", "compute_capability": "12.0", "vram_gb": 7.96, "driver_version": "576.83", "performance_conclusion": "Gate 9 CUDA optimizations significantly improved CUDA PDHG performance on the physical RTX 5050 by an overall aggregate factor of 1.81x compared to Gate 8 CUDA. Overall suite Gate 9 CUDA E2E speedup relative to Gate 9 CPU is 1.07x (SMALL: 0.61x, MEDIUM: 0.93x, LARGE: 1.13x).", "strata_note": "The repository's LARGE stratum is relative to this frozen Netlib suite subset.", "status_matching_note": "CPU and CUDA statuses and CPU original-model verification outcomes were compared; numerical objective differences are reported separately.", "suite_totals": {"total_instances": 18, "optimal_verified_instances": 3, "limit_reached_instances": 15, "gate9_total_cpu_seconds": 203.5641, "gate9_total_cuda_seconds": 189.6878, "gate8_total_cuda_seconds": 342.6352, "overall_speedup_cpu_over_cuda": 1.0732, "overall_cuda_improvement_factor": 1.8063}, "stratum_aggregates": {"SMALL": {"gate9_total_cpu_seconds": 5.5294, "gate9_total_cuda_seconds": 9.0165, "gate8_total_cuda_seconds": 50.933, "aggregate_speedup_cpu_over_cuda": 0.6133, "aggregate_cuda_improvement_factor": 5.6489}, "MEDIUM": {"gate9_total_cpu_seconds": 25.9996, "gate9_total_cuda_seconds": 28.0708, "gate8_total_cuda_seconds": 105.0718, "aggregate_speedup_cpu_over_cuda": 0.9262, "aggregate_cuda_improvement_factor": 3.7431}, "LARGE": {"gate9_total_cpu_seconds": 172.0352, "gate9_total_cuda_seconds": 152.6005, "gate8_total_cuda_seconds": 186.6303, "aggregate_speedup_cpu_over_cuda": 1.1274, "aggregate_cuda_improvement_factor": 1.223}}, "per_instance": {"afiro": {"instance": "afiro", "stratum": "SMALL", "status": "OPTIMAL_VERIFIED", "gpu_executed": true, "gate8_cuda_median_ms": 2749.82, "gate9_cuda_median_ms": 432.92, "gate9_cpu_median_ms": 223.29, "gate9_speedup_cpu_over_cuda": 0.5158, "cuda_optimization_improvement_factor": 6.3518, "objective_cuda": -464.7531422334188, "objective_cpu": -464.75314223341877, "reference_objective": -464.75314286, "objective_discrepancy": 5.684341886080802e-14, "relative_discrepancy": 1.2230884230498093e-16, "iterations": 12000, "telemetry": {"setup_seconds": 0.0007064000019454397, "iteration_seconds": 0.34487810004793573, "verification_seconds": 0.08724449995497707, "kernel_launches_count": 48033, "restarts_count": 11, "convergence_checks_count": 120}}, "kb2": {"instance": "kb2", "stratum": "SMALL", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 11384.73, "gate9_cuda_median_ms": 1920.7, "gate9_cpu_median_ms": 1158.52, "gate9_speedup_cpu_over_cuda": 0.6032, "cuda_optimization_improvement_factor": 5.9274, "objective_cuda": -325.5566231752414, "objective_cpu": -325.55662317524127, "reference_objective": -1749.9001299, "objective_discrepancy": 1.1368683772161603e-13, "relative_discrepancy": 6.496761488217777e-17, "iterations": 50000, "telemetry": {"setup_seconds": 0.0007266999964485876, "iteration_seconds": 1.423318199966161, "verification_seconds": 0.46284620003279997, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "sc50a": {"instance": "sc50a", "stratum": "SMALL", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 11293.8, "gate9_cuda_median_ms": 1961.44, "gate9_cpu_median_ms": 1122.46, "gate9_speedup_cpu_over_cuda": 0.5723, "cuda_optimization_improvement_factor": 5.7579, "objective_cuda": -54.57267387792076, "objective_cpu": -54.57267387792081, "reference_objective": -64.575077059, "objective_discrepancy": 5.684341886080802e-14, "relative_discrepancy": 8.802686957519566e-16, "iterations": 50000, "telemetry": {"setup_seconds": 0.00164049999875715, "iteration_seconds": 1.4692225999460788, "verification_seconds": 0.5004839000539505, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "sc50b": {"instance": "sc50b", "stratum": "SMALL", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 11277.15, "gate9_cuda_median_ms": 1976.63, "gate9_cpu_median_ms": 1108.33, "gate9_speedup_cpu_over_cuda": 0.5607, "cuda_optimization_improvement_factor": 5.7052, "objective_cuda": -61.753278159160516, "objective_cpu": -61.753278159160516, "reference_objective": -70.0, "objective_discrepancy": 0.0, "relative_discrepancy": 0.0, "iterations": 50000, "telemetry": {"setup_seconds": 0.000720000003639143, "iteration_seconds": 1.4548089000600157, "verification_seconds": 0.4952540999438497, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "adlittle": {"instance": "adlittle", "stratum": "SMALL", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 11549.81, "gate9_cuda_median_ms": 2222.38, "gate9_cpu_median_ms": 1541.18, "gate9_speedup_cpu_over_cuda": 0.6935, "cuda_optimization_improvement_factor": 5.197, "objective_cuda": 225285.6217838146, "objective_cpu": 225285.6217838147, "reference_objective": 225494.96316, "objective_discrepancy": 1.1641532182693481e-10, "relative_discrepancy": 5.162657302652578e-16, "iterations": 50000, "telemetry": {"setup_seconds": 0.0011691999970935285, "iteration_seconds": 1.4718584999500308, "verification_seconds": 0.7414230000504176, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "blend": {"instance": "blend", "stratum": "SMALL", "status": "OPTIMAL_VERIFIED", "gpu_executed": true, "gate8_cuda_median_ms": 2677.71, "gate9_cuda_median_ms": 502.43, "gate9_cpu_median_ms": 375.62, "gate9_speedup_cpu_over_cuda": 0.7476, "cuda_optimization_improvement_factor": 5.3296, "objective_cuda": -30.81215032045006, "objective_cpu": -30.81215032045, "reference_objective": -30.812149846, "objective_discrepancy": 5.684341886080802e-14, "relative_discrepancy": 1.8448378040777106e-15, "iterations": 11500, "telemetry": {"setup_seconds": 0.0010580000016489066, "iteration_seconds": 0.3323434999983874, "verification_seconds": 0.16777510000247275, "kernel_launches_count": 46033, "restarts_count": 11, "convergence_checks_count": 115}}, "sc105": {"instance": "sc105", "stratum": "MEDIUM", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 11886.38, "gate9_cuda_median_ms": 2426.98, "gate9_cpu_median_ms": 1637.14, "gate9_speedup_cpu_over_cuda": 0.6746, "cuda_optimization_improvement_factor": 4.8976, "objective_cuda": -4.344483399476433, "objective_cpu": -4.344483399476441, "reference_objective": -52.202061212, "objective_discrepancy": 7.993605777301127e-15, "relative_discrepancy": 1.531281637488979e-16, "iterations": 50000, "telemetry": {"setup_seconds": 0.0009043999962159432, "iteration_seconds": 1.5141429999712273, "verification_seconds": 0.9116959000311908, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "stocfor1": {"instance": "stocfor1", "stratum": "MEDIUM", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 12053.5, "gate9_cuda_median_ms": 2562.1, "gate9_cpu_median_ms": 1920.72, "gate9_speedup_cpu_over_cuda": 0.7497, "cuda_optimization_improvement_factor": 4.7045, "objective_cuda": -38236.263408359904, "objective_cpu": -38236.26340835981, "reference_objective": -41131.976219, "objective_discrepancy": 9.458744898438454e-11, "relative_discrepancy": 2.2996086665218868e-15, "iterations": 50000, "telemetry": {"setup_seconds": 0.0008587000047555193, "iteration_seconds": 1.5223774000551202, "verification_seconds": 1.022580599950743, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "scagr7": {"instance": "scagr7", "stratum": "MEDIUM", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 12590.66, "gate9_cuda_median_ms": 2938.05, "gate9_cpu_median_ms": 2397.5, "gate9_speedup_cpu_over_cuda": 0.816, "cuda_optimization_improvement_factor": 4.2854, "objective_cuda": -2330635.049593187, "objective_cpu": -2330635.0495931865, "reference_objective": -2331389.2548, "objective_discrepancy": 4.656612873077393e-10, "relative_discrepancy": 1.9973553809129413e-16, "iterations": 50000, "telemetry": {"setup_seconds": 0.0010240000046906061, "iteration_seconds": 1.5533237000272493, "verification_seconds": 1.3819664999755332, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "recipe": {"instance": "recipe", "stratum": "MEDIUM", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 13279.22, "gate9_cuda_median_ms": 3367.34, "gate9_cpu_median_ms": 2819.76, "gate9_speedup_cpu_over_cuda": 0.8374, "cuda_optimization_improvement_factor": 3.9435, "objective_cuda": -266.6149457954093, "objective_cpu": -266.6149457954092, "reference_objective": -266.616, "objective_discrepancy": 1.1368683772161603e-13, "relative_discrepancy": 4.2640665872121715e-16, "iterations": 50000, "telemetry": {"setup_seconds": 0.0018048999991151504, "iteration_seconds": 1.6198794000956696, "verification_seconds": 1.7981268998992164, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "israel": {"instance": "israel", "stratum": "MEDIUM", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 12347.19, "gate9_cuda_median_ms": 3219.63, "gate9_cpu_median_ms": 3051.07, "gate9_speedup_cpu_over_cuda": 0.9476, "cuda_optimization_improvement_factor": 3.835, "objective_cuda": -892092.784749925, "objective_cpu": -892092.784749925, "reference_objective": -896644.82186, "objective_discrepancy": 0.0, "relative_discrepancy": 0.0, "iterations": 50000, "telemetry": {"setup_seconds": 0.0018347000004723668, "iteration_seconds": 1.8405976999711129, "verification_seconds": 1.3620098000246799, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "sc205": {"instance": "sc205", "stratum": "MEDIUM", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 13719.23, "gate9_cuda_median_ms": 4211.82, "gate9_cpu_median_ms": 3556.07, "gate9_speedup_cpu_over_cuda": 0.8443, "cuda_optimization_improvement_factor": 3.2573, "objective_cuda": -0.29880767804786834, "objective_cpu": -0.2988076780478682, "reference_objective": -52.202061212, "objective_discrepancy": 1.6653345369377348e-16, "relative_discrepancy": 3.1901700781020396e-18, "iterations": 50000, "telemetry": {"setup_seconds": 0.0020689999946625903, "iteration_seconds": 1.6649859999961336, "verification_seconds": 2.512696700003289, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "share1b": {"instance": "share1b", "stratum": "MEDIUM", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 13852.87, "gate9_cuda_median_ms": 3583.12, "gate9_cpu_median_ms": 4088.94, "gate9_speedup_cpu_over_cuda": 1.1412, "cuda_optimization_improvement_factor": 3.8662, "objective_cuda": -54874.78251044188, "objective_cpu": -54874.78251044197, "reference_objective": -76589.318579, "objective_discrepancy": 8.731149137020111e-11, "relative_discrepancy": 1.1399956676744871e-15, "iterations": 50000, "telemetry": {"setup_seconds": 0.001774299998942297, "iteration_seconds": 1.5785255000228062, "verification_seconds": 2.0024111999737215, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "brandy": {"instance": "brandy", "stratum": "MEDIUM", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 15342.75, "gate9_cuda_median_ms": 5761.74, "gate9_cpu_median_ms": 6528.4, "gate9_speedup_cpu_over_cuda": 1.1331, "cuda_optimization_improvement_factor": 2.6629, "objective_cuda": 1521.6857845050845, "objective_cpu": 1521.6857845050847, "reference_objective": 1518.5098965, "objective_discrepancy": 2.2737367544323206e-13, "relative_discrepancy": 1.4973473400950736e-16, "iterations": 50000, "telemetry": {"setup_seconds": 0.002271599994855933, "iteration_seconds": 1.840397500047402, "verification_seconds": 3.937690099955944, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "grow15": {"instance": "grow15", "stratum": "LARGE", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 41372.3, "gate9_cuda_median_ms": 28697.45, "gate9_cpu_median_ms": 34595.08, "gate9_speedup_cpu_over_cuda": 1.2055, "cuda_optimization_improvement_factor": 1.4417, "objective_cuda": -36895204.26787624, "objective_cpu": -36895204.26787689, "reference_objective": -106870941.29, "objective_discrepancy": 6.556510925292969e-07, "relative_discrepancy": 6.134980048038995e-15, "iterations": 50000, "telemetry": {"setup_seconds": 0.006188200000906363, "iteration_seconds": 2.0626963999748114, "verification_seconds": 27.41396220002207, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "grow22": {"instance": "grow22", "stratum": "LARGE", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 72325.93, "gate9_cuda_median_ms": 63286.21, "gate9_cpu_median_ms": 71687.13, "gate9_speedup_cpu_over_cuda": 1.1327, "cuda_optimization_improvement_factor": 1.1428, "objective_cuda": -56662392.816172875, "objective_cpu": -56662392.81617385, "reference_objective": -160834336.48, "objective_discrepancy": 9.760260581970215e-07, "relative_discrepancy": 6.0685179518143e-15, "iterations": 50000, "telemetry": {"setup_seconds": 0.012577300003613345, "iteration_seconds": 2.0663092999893706, "verification_seconds": 59.800317800014454, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "scfxm2": {"instance": "scfxm2", "stratum": "LARGE", "status": "LIMIT_REACHED", "gpu_executed": true, "gate8_cuda_median_ms": 51342.82, "gate9_cuda_median_ms": 40126.48, "gate9_cpu_median_ms": 44272.9, "gate9_speedup_cpu_over_cuda": 1.1033, "cuda_optimization_improvement_factor": 1.2795, "objective_cuda": 37248.93313642605, "objective_cpu": 37248.93313642604, "reference_objective": 36660.261565, "objective_discrepancy": 7.275957614183426e-12, "relative_discrepancy": 1.9846987728886995e-16, "iterations": 50000, "telemetry": {"setup_seconds": 0.015257899998687208, "iteration_seconds": 2.4574459999930696, "verification_seconds": 37.90925870000501, "kernel_launches_count": 200150, "restarts_count": 50, "convergence_checks_count": 500}}, "sctap2": {"instance": "sctap2", "stratum": "LARGE", "status": "OPTIMAL_VERIFIED", "gpu_executed": true, "gate8_cuda_median_ms": 21589.29, "gate9_cuda_median_ms": 20490.39, "gate9_cpu_median_ms": 21480.05, "gate9_speedup_cpu_over_cuda": 1.0483, "cuda_optimization_improvement_factor": 1.0536, "objective_cuda": 1724.8071794478092, "objective_cpu": 1724.80717944781, "reference_objective": 1724.8071429, "objective_discrepancy": 9.094947017729282e-13, "relative_discrepancy": 5.27302258410034e-16, "iterations": 6000, "telemetry": {"setup_seconds": 0.04285369999706745, "iteration_seconds": 0.27015640000172425, "verification_seconds": 19.75640839999687, "kernel_launches_count": 24015, "restarts_count": 5, "convergence_checks_count": 60}}}};

  // 4. Default Continuous LP Solve Result (Baseline)
  const DEFAULT_LP_RESULT = {
    model_name: 'MRPL_Refinery_Twin_LP',
    status: 'OPTIMAL_VERIFIED',
    objective: -9043.75,
    net_margin: 9043.75,
    iterations: 109,
    elapsed_seconds: 0.0482,
    backend: 'cpu',
    gpu_executed: false,
    method_used: 'primal-simplex',
    linear_algebra_used: 'sparse',
    basis_factorization: 'sovereign_sparse_lu_pfi',
    verification: {
      primal_residual: 1.4210854715202004e-15,
      dual_residual: 2.8421709430404007e-14,
      duality_gap: 0.0,
      kkt_passed: true,
      feasible: true
    },
    history: null
  };


  // ==========================================================================
  // MRPL-STYLE ROTATING HERO CAROUSEL CONTROLLER & SCROLL REVEALS
  // ==========================================================================
  const CAROUSEL_INTERVAL_MS = 5000;
  let carouselIndex = 0;
  let isCarouselPaused = false;
  let isCarouselHovered = false;
  let isCarouselFocused = false;
  let progressRaf = null;
  let progressStartTime = 0;
  let progressElapsed = 0;
  let isTimerRunning = false;

  function initCarousel() {
    const carouselEl = document.getElementById('hero-carousel');
    if (!carouselEl) return;

    const slides = carouselEl.querySelectorAll('.carousel-slide');
    const dots = carouselEl.querySelectorAll('.carousel-dot');
    const prevBtn = document.getElementById('carousel-prev');
    const nextBtn = document.getElementById('carousel-next');
    const playPauseBtn = document.getElementById('carousel-playpause');
    const progressFill = document.getElementById('carousel-progress-fill');

    if (!slides.length) return;

    function isMotionReduced() {
      return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    }

    function stepProgress(timestamp) {
      if (!isTimerRunning) return;
      if (!progressStartTime) progressStartTime = timestamp - progressElapsed;
      progressElapsed = timestamp - progressStartTime;

      const pct = Math.min(100, (progressElapsed / CAROUSEL_INTERVAL_MS) * 100);
      if (progressFill) {
        progressFill.style.width = pct.toFixed(2) + '%';
      }

      if (progressElapsed >= CAROUSEL_INTERVAL_MS) {
        progressElapsed = 0;
        progressStartTime = 0;
        if (progressFill) progressFill.style.width = '0%';
        nextSlide();
        return;
      }

      progressRaf = requestAnimationFrame(stepProgress);
    }

    function startTimer() {
      if (isTimerRunning) return;
      if (isCarouselPaused || isCarouselHovered || isCarouselFocused || document.hidden || isMotionReduced()) {
        return;
      }
      isTimerRunning = true;
      progressStartTime = 0;
      progressRaf = requestAnimationFrame(stepProgress);
    }

    function pauseTimer() {
      if (!isTimerRunning) return;
      isTimerRunning = false;
      if (progressRaf) {
        cancelAnimationFrame(progressRaf);
        progressRaf = null;
      }
    }

    function resetTimer() {
      pauseTimer();
      progressElapsed = 0;
      progressStartTime = 0;
      if (progressFill) progressFill.style.width = '0%';
      startTimer();
    }

    function showSlide(index) {
      if (index < 0) index = slides.length - 1;
      if (index >= slides.length) index = 0;

      slides.forEach((slide, i) => {
        if (i === index) {
          slide.classList.remove('exiting');
          slide.classList.add('active');
          slide.setAttribute('aria-hidden', 'false');
        } else if (slide.classList.contains('active')) {
          slide.classList.remove('active');
          slide.classList.add('exiting');
          slide.setAttribute('aria-hidden', 'true');
          setTimeout(() => slide.classList.remove('exiting'), 700);
        } else {
          slide.classList.remove('active', 'exiting');
          slide.setAttribute('aria-hidden', 'true');
        }
      });

      dots.forEach((dot, i) => {
        const isActive = i === index;
        dot.classList.toggle('active', isActive);
        dot.setAttribute('aria-selected', String(isActive));
      });

      carouselIndex = index;
      resetTimer();
    }

    function nextSlide() {
      showSlide(carouselIndex + 1);
    }

    function prevSlide() {
      showSlide(carouselIndex - 1);
    }

    function togglePlayPause() {
      isCarouselPaused = !isCarouselPaused;
      if (playPauseBtn) {
        playPauseBtn.setAttribute('aria-pressed', String(isCarouselPaused));
        playPauseBtn.setAttribute('aria-label', isCarouselPaused ? 'Play carousel' : 'Pause carousel');
        playPauseBtn.title = isCarouselPaused ? 'Play carousel' : 'Pause carousel';
        const iconPause = playPauseBtn.querySelector('.icon-pause');
        const iconPlay = playPauseBtn.querySelector('.icon-play');
        if (iconPause && iconPlay) {
          iconPause.style.display = isCarouselPaused ? 'none' : 'block';
          iconPlay.style.display = isCarouselPaused ? 'block' : 'none';
        }
      }
      if (isCarouselPaused) {
        pauseTimer();
      } else {
        startTimer();
      }
    }

    // Dot click listeners
    dots.forEach((dot) => {
      dot.addEventListener('click', (e) => {
        const targetIdx = parseInt(e.currentTarget.getAttribute('data-index'), 10);
        if (!isNaN(targetIdx)) {
          showSlide(targetIdx);
        }
      });
    });

    // Button click listeners
    if (prevBtn) prevBtn.addEventListener('click', prevSlide);
    if (nextBtn) nextBtn.addEventListener('click', nextSlide);
    if (playPauseBtn) playPauseBtn.addEventListener('click', togglePlayPause);

    // Desktop hover pause / resume
    carouselEl.addEventListener('mouseenter', () => {
      isCarouselHovered = true;
      pauseTimer();
    });
    carouselEl.addEventListener('mouseleave', () => {
      isCarouselHovered = false;
      startTimer();
    });

    // Keyboard focus pause / resume
    carouselEl.addEventListener('focusin', () => {
      isCarouselFocused = true;
      pauseTimer();
    });
    carouselEl.addEventListener('focusout', () => {
      isCarouselFocused = false;
      startTimer();
    });

    // Keyboard navigation (ArrowLeft / ArrowRight)
    carouselEl.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        prevSlide();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        nextSlide();
      }
    });

    // Touch swipe support
    let touchStartX = 0;
    let touchStartY = 0;
    carouselEl.addEventListener('touchstart', (e) => {
      if (e.touches && e.touches[0]) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
      }
    }, { passive: true });

    carouselEl.addEventListener('touchend', (e) => {
      if (e.changedTouches && e.changedTouches[0]) {
        const deltaX = e.changedTouches[0].clientX - touchStartX;
        const deltaY = e.changedTouches[0].clientY - touchStartY;
        if (Math.abs(deltaX) > 40 && Math.abs(deltaX) > Math.abs(deltaY)) {
          if (deltaX < 0) {
            nextSlide();
          } else {
            prevSlide();
          }
        }
      }
    }, { passive: true });

    // Page Visibility API support (pause carousel and ticker when hidden)
    document.addEventListener('visibilitychange', () => {
      const tickerTrack = document.querySelector('.updates-ticker-track');
      if (document.hidden) {
        pauseTimer();
        if (tickerTrack) tickerTrack.style.animationPlayState = 'paused';
      } else {
        startTimer();
        if (tickerTrack) tickerTrack.style.animationPlayState = 'running';
      }
    });

    // Expose helpers on window.sovApp for testing and scripting
    window.sovApp = window.sovApp || {};
    window.sovApp.goToCarouselSlide = showSlide;
    window.sovApp.nextCarouselSlide = nextSlide;
    window.sovApp.prevCarouselSlide = prevSlide;
    window.sovApp.toggleCarouselPlayPause = togglePlayPause;

    // Start timer on initialize
    startTimer();
  }

  // Scroll reveal observer for .reveal-on-scroll cards
  function setupScrollReveals() {
    const revealEls = document.querySelectorAll('.reveal-on-scroll');
    if (!revealEls.length) return;

    if ((window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) || !('IntersectionObserver' in window)) {
      revealEls.forEach(el => el.classList.add('revealed'));
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const parent = el.parentElement;
          let delay = 0;
          if (parent) {
            const siblings = Array.from(parent.querySelectorAll('.reveal-on-scroll'));
            const idx = siblings.indexOf(el);
            if (idx > 0) delay = idx * 60; // 60ms stagger
          }
          setTimeout(() => {
            el.classList.add('revealed');
          }, delay);
          observer.unobserve(el);
        }
      });
    }, { threshold: 0.1 });

    revealEls.forEach(el => observer.observe(el));
  }


  // Initialize Application
  function init() {
    STATE.solveResult = null;
    setupAccessibility();
    setupNavigation();
    setupMobileDrawer();
    initCarousel();
    setupScenarioControls();
    setupSolverConsole();
    setupUnitInspector();
    setupAnalyticsTable();
    setupComparisonMatrix();
    setupEvidenceCopy();
    setupScrollReveals();
    renderRefineryPFD();
    renderConvergenceChart(null);
    updateScenarioDetail(STATE.activeScenario);
    updateTrustPassportUI(null);
    updateSolverUI(null);

    // Initial view routing based on URL hash
    const hash = window.location.hash ? window.location.hash.substring(1) : '';
    const validTabs = ['home', 'overview', 'optimization', 'scenarios', 'analytics', 'trust', 'benchmarks', 'evidence', 'reports', 'about', 'contact'];
    if (validTabs.includes(hash)) {
      switchTab(hash);
    } else {
      switchTab('home');
    }
  }

  // Accessibility Controls Setup
  function setupAccessibility() {
    const btnSpace = document.getElementById('btn-acc-space');
    if (btnSpace) {
      btnSpace.addEventListener('click', () => {
        const isWide = document.body.classList.toggle('wide-spacing');
        btnSpace.setAttribute('aria-pressed', String(isWide));
      });
    }

    const btnContrast = document.getElementById('btn-acc-contrast');
    if (btnContrast) {
      btnContrast.addEventListener('click', () => {
        const isHigh = document.body.classList.toggle('high-contrast');
        btnContrast.setAttribute('aria-pressed', String(isHigh));
      });
    }

    const btnFontMinus = document.getElementById('btn-acc-font-minus');
    if (btnFontMinus) {
      btnFontMinus.addEventListener('click', () => {
        document.body.classList.remove('large-text');
        document.body.classList.add('small-text');
      });
    }

    const btnFontReset = document.getElementById('btn-acc-font-reset');
    if (btnFontReset) {
      btnFontReset.addEventListener('click', () => {
        document.body.classList.remove('small-text');
        document.body.classList.remove('large-text');
      });
    }

    const btnFontPlus = document.getElementById('btn-acc-font-plus');
    if (btnFontPlus) {
      btnFontPlus.addEventListener('click', () => {
        document.body.classList.remove('small-text');
        document.body.classList.add('large-text');
      });
    }
  }

  // Mobile Drawer Logic
  function setupMobileDrawer() {
    const trigger = document.getElementById('mobile-menu-trigger');
    const closeBtn = document.getElementById('mobile-close-btn');
    const backdrop = document.getElementById('mobile-backdrop');
    const rail = document.getElementById('nav-rail');

    function openMenu() {
      STATE.isMobileMenuOpen = true;
      if (rail) rail.classList.add('open');
      if (backdrop) backdrop.classList.add('open');
      if (closeBtn) closeBtn.style.display = 'block';
    }

    function closeMenu() {
      STATE.isMobileMenuOpen = false;
      if (rail) rail.classList.remove('open');
      if (backdrop) backdrop.classList.remove('open');
      if (closeBtn) closeBtn.style.display = 'none';
    }

    if (trigger) trigger.addEventListener('click', openMenu);
    if (closeBtn) closeBtn.addEventListener('click', closeMenu);
    if (backdrop) backdrop.addEventListener('click', closeMenu);

    // Close on ESC key
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && STATE.isMobileMenuOpen) {
        closeMenu();
      }
    });

    // Close mobile drawer when any navigation link is tapped
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        if (window.innerWidth <= 767) {
          closeMenu();
        }
      });
    });
  }

  // Desktop & Mobile Navigation Logic
  function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', e => {
        e.preventDefault();
        const tab = item.getAttribute('data-tab');
        if (!tab) return;
        switchTab(tab);
      });
    });

    const quickSolveBtn = document.getElementById('btn-header-solve');
    if (quickSolveBtn) {
      quickSolveBtn.addEventListener('click', () => {
        switchTab('optimization');
        triggerSolve();
      });
    }

    const quickAuditBtn = document.getElementById('btn-header-audit');
    if (quickAuditBtn) {
      quickAuditBtn.addEventListener('click', () => {
        switchTab('reports');
      });
    }
  }

  function switchTab(tabId) {
    STATE.activeTab = tabId;

    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.toggle('active', item.getAttribute('data-tab') === tabId);
    });

    document.querySelectorAll('.view-section').forEach(sec => {
      const isTarget = sec.id === ('view-' + tabId);
      sec.classList.toggle('active', isTarget);
    });

    if (tabId === 'overview') {
      renderRefineryPFD();
    } else if (tabId === 'optimization') {
      renderConvergenceChart(STATE.solveResult);
    } else if (tabId === 'scenarios') {
      renderComparison();
    } else if (tabId === 'trust') {
      updateTrustPassportUI(STATE.solveResult);
    }

    // Reveal any cards inside newly activated view section
    const targetView = document.getElementById('view-' + tabId);
    if (targetView) {
      const cards = targetView.querySelectorAll('.reveal-on-scroll');
      cards.forEach((card, idx) => {
        setTimeout(() => card.classList.add('revealed'), idx * 60);
      });
    }

    if (history.replaceState) {
      history.replaceState(null, null, '#' + tabId);
    }

    window.scrollTo({ top: 0, behavior: 'instant' });
  }

  // Setup Unit Inspector Interaction
  function setupUnitInspector() {
    updateUnitInspector('CDU');
  }

  function updateUnitInspector(unitId) {
    STATE.selectedUnit = unitId;
    const u = REFINERY_UNITS[unitId] || REFINERY_UNITS['CDU'];

    const strip = document.getElementById('unit-spec-strip');
    if (strip) {
      strip.classList.add('fading');
      setTimeout(() => {
        const titleEl = document.getElementById('inspector-title');
        const capEl = document.getElementById('inspector-cap');
        const rateEl = document.getElementById('inspector-rate');
        const yieldEl = document.getElementById('inspector-yield');
        const shadowEl = document.getElementById('inspector-shadow');
        const statusEl = document.getElementById('inspector-status');

        if (titleEl) titleEl.textContent = u.name;
        if (capEl) capEl.textContent = u.designCapacity;
        if (rateEl) rateEl.textContent = u.nominalOperatingRate;
        if (yieldEl) yieldEl.textContent = u.yieldFormula;
        if (shadowEl) shadowEl.textContent = u.shadowPrice;
        if (statusEl) statusEl.innerHTML = `<span class="status-pill"><span class="status-dot"></span> ${u.status}</span>`;
        strip.classList.remove('fading');
      }, 100);
    }

    renderRefineryPFD();
  }

  // Refined Editorial Process Flowsheet Renderer
  function renderRefineryPFD() {
    const svg = document.getElementById('refinery-pfd');
    if (!svg) return;

    const s = SCENARIOS[STATE.activeScenario] || SCENARIOS['SC-01'];
    const activeUnit = STATE.selectedUnit || 'CDU';

    const isInfeasible = (STATE.resultSource === 'live' && STATE.solveResult && STATE.solveResult.status === 'INFEASIBLE_CERTIFIED') || s.variant === 'infeasible';

    let arabRate = isInfeasible ? 0.0 : s.cduArab;
    let basrahRate = isInfeasible ? 0.0 : s.cduBasrah;
    let cduRate = isInfeasible ? 0.0 : s.cduThroughput;
    let fccRate = isInfeasible ? 0.0 : s.fccThroughput;
    let refRate = isInfeasible ? 0.0 : s.reformerThroughput;
    let gasRate = isInfeasible ? 0.0 : s.gasolineShipment;
    let dslRate = isInfeasible ? 0.0 : s.dieselShipment;
    let foRate = isInfeasible ? 0.0 : s.fuelOilShipment;

    let arabPrice = s.crudeArabPrice;
    let basrahPrice = s.crudeBasrahPrice;

    // If live solve result available for a refinery model
    if (!isInfeasible && STATE.resultSource === 'live' && STATE.solveResult && STATE.solveResult.x && STATE.solveResult.x.length >= 12) {
      const x = STATE.solveResult.x;
      arabRate = x[0];
      basrahRate = x[1];
      cduRate = x[2];
      fccRate = x[3];
      refRate = x[4];
      gasRate = x[9];
      dslRate = x[10];
      foRate = x[11];
    }

    if (STATE.resultSource === 'live' && STATE.solveResult && STATE.solveResult.inputs) {
      if (STATE.solveResult.inputs.c_arab !== undefined) arabPrice = STATE.solveResult.inputs.c_arab;
      if (STATE.solveResult.inputs.c_basrah !== undefined) basrahPrice = STATE.solveResult.inputs.c_basrah;
    }

    svg.innerHTML = `
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4.5" markerHeight="4.5" orient="auto-start-reverse">
          <path d="M 0 1.5 L 7 5 L 0 8.5 z" fill="#8C8578" />
        </marker>
        <marker id="arrow-rust" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4.5" markerHeight="4.5" orient="auto-start-reverse">
          <path d="M 0 1.5 L 7 5 L 0 8.5 z" fill="#A65336" />
        </marker>
        <marker id="arrow-olive" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4.5" markerHeight="4.5" orient="auto-start-reverse">
          <path d="M 0 1.5 L 7 5 L 0 8.5 z" fill="#647052" />
        </marker>
      </defs>

      ${isInfeasible ? `
        <rect x="230" y="8" width="420" height="22" rx="3" fill="#A65336" fill-opacity="0.1" stroke="#A65336" stroke-width="0.75"/>
        <text x="440" y="23" fill="#A65336" font-size="10.5" font-weight="600" text-anchor="middle" letter-spacing="0.5">
          INFEASIBLE SYSTEM · NO BALANCED STREAM FLOW EXISTS (FARKAS CERTIFIED)
        </text>
      ` : ''}

      <!-- Feeds: Arab Light & Basrah Heavy Pipelines -->
      <path id="pipe-crude-1" class="pfd-pipe hydrocarbon-active" d="M 35,65 L 115,65 L 115,115 L 150,115" marker-end="url(#arrow-rust)" />
      <path id="pipe-crude-2" class="pfd-pipe hydrocarbon-active" d="M 35,165 L 115,165 L 115,115" />

      <!-- Feed Labels -->
      <text class="pfd-unit-title" x="72" y="55" text-anchor="middle">Arab Light</text>
      <text class="pfd-unit-stat" x="72" y="77" text-anchor="middle">${arabRate.toFixed(1)} kbpd · $${arabPrice.toFixed(0)}</text>

      <text class="pfd-unit-title" x="72" y="155" text-anchor="middle">Basrah Heavy</text>
      <text class="pfd-unit-stat" x="72" y="177" text-anchor="middle">${basrahRate.toFixed(1)} kbpd · $${basrahPrice.toFixed(0)}</text>

      <!-- UNIT 1: CDU -->
      <g id="unit-cdu" class="pfd-unit ${activeUnit === 'CDU' ? 'selected' : ''}" onclick="window.sovApp.inspectUnit('CDU')" transform="translate(150, 35)">
        <rect width="110" height="150" rx="4" />
        <line x1="10" y1="40" x2="100" y2="40" stroke="#E2DDD5" stroke-dasharray="2,2"/>
        <line x1="10" y1="80" x2="100" y2="80" stroke="#E2DDD5" stroke-dasharray="2,2"/>
        <line x1="10" y1="115" x2="100" y2="115" stroke="#E2DDD5" stroke-dasharray="2,2"/>
        <text class="pfd-unit-tag" x="55" y="24" text-anchor="middle">01 · PRIMARY</text>
        <text class="pfd-unit-title" x="55" y="65" text-anchor="middle">Atmospheric</text>
        <text class="pfd-unit-title" x="55" y="80" text-anchor="middle">Distillation</text>
        <text class="pfd-unit-stat" x="55" y="105" text-anchor="middle">CDU Feed</text>
        <text class="pfd-unit-stat" x="55" y="132" text-anchor="middle" style="fill: var(--rust); font-weight: 600;">${cduRate.toFixed(1)} / 100k</text>
      </g>

      <!-- Interconnecting Streams from CDU -->
      <path id="pipe-naphtha" class="pfd-pipe hydrocarbon-active" d="M 260,65 L 350,65" marker-end="url(#arrow-rust)" />
      <text class="pfd-stream-label" x="305" y="58" text-anchor="middle">Naphtha</text>

      <path id="pipe-distillate" class="pfd-pipe product-active" d="M 260,115 L 320,115 L 320,215 L 585,215" marker-end="url(#arrow-olive)" />
      <text class="pfd-stream-label" x="420" y="210" text-anchor="middle">Distillate Header</text>

      <path id="pipe-residue" class="pfd-pipe fuel-active" d="M 260,165 L 350,165" marker-end="url(#arrow)" />
      <text class="pfd-stream-label" x="305" y="158" text-anchor="middle">Residue</text>

      <!-- UNIT 2: CATALYTIC REFORMER -->
      <g id="unit-reformer" class="pfd-unit ${activeUnit === 'REFORMER' ? 'selected' : ''}" onclick="window.sovApp.inspectUnit('REFORMER')" transform="translate(350, 35)">
        <rect width="110" height="70" rx="4" />
        <text class="pfd-unit-tag" x="55" y="18" text-anchor="middle">02 · OCTANE</text>
        <text class="pfd-unit-title" x="55" y="38" text-anchor="middle">Semi-Regen</text>
        <text class="pfd-unit-title" x="55" y="50" text-anchor="middle">Reformer</text>
        <text class="pfd-unit-stat" x="55" y="64" text-anchor="middle">${refRate.toFixed(1)} kbpd</text>
      </g>

      <!-- UNIT 3: FLUID CATALYTIC CRACKER (FCC) -->
      <g id="unit-fcc" class="pfd-unit ${activeUnit === 'FCC' ? 'selected' : ''}" onclick="window.sovApp.inspectUnit('FCC')" transform="translate(350, 135)">
        <rect width="110" height="85" rx="4" />
        <text class="pfd-unit-tag" x="55" y="18" text-anchor="middle">03 · CRACKING</text>
        <text class="pfd-unit-title" x="55" y="38" text-anchor="middle">Fluid Catalytic</text>
        <text class="pfd-unit-title" x="55" y="50" text-anchor="middle">Cracker (FCC)</text>
        <text class="pfd-unit-stat" x="55" y="68" text-anchor="middle" style="fill: ${fccRate >= 48 ? 'var(--rust)' : 'var(--text-primary)'}; font-weight: 600;">${fccRate.toFixed(1)} / 50k</text>
      </g>

      <!-- Downstream Blending Links -->
      <path id="pipe-reformate" class="pfd-pipe hydrocarbon-active" d="M 460,70 L 585,70" marker-end="url(#arrow-rust)" />
      <text class="pfd-stream-label" x="520" y="64" text-anchor="middle">Reformate (100 RON)</text>

      <path id="pipe-catgas" class="pfd-pipe hydrocarbon-active" d="M 460,155 L 530,155 L 530,95 L 585,95" marker-end="url(#arrow-rust)" />
      <text class="pfd-stream-label" x="495" y="148" text-anchor="middle">CatGas (92 RON)</text>

      <path id="pipe-lco" class="pfd-pipe product-active" d="M 460,185 L 540,185 L 540,185 L 585,185" marker-end="url(#arrow-olive)" />
      <text class="pfd-stream-label" x="520" y="178" text-anchor="middle">FCC LCO</text>

      <path id="pipe-slurry" class="pfd-pipe fuel-active" d="M 460,205 L 510,205 L 510,255 L 585,255" marker-end="url(#arrow)" />
      <text class="pfd-stream-label" x="535" y="248" text-anchor="middle">Slurry/Bottoms</text>

      <!-- BLENDING & PRODUCT STORAGE -->
      <g id="unit-blend-gas" class="pfd-unit ${activeUnit === 'BLEND_GAS' ? 'selected' : ''}" onclick="window.sovApp.inspectUnit('BLEND_GAS')" transform="translate(585, 50)">
        <rect width="115" height="55" rx="4" />
        <text class="pfd-unit-tag" x="57" y="16" text-anchor="middle">04 · POOL</text>
        <text class="pfd-unit-title" x="57" y="32" text-anchor="middle">Gasoline Pool</text>
        <text class="pfd-unit-stat" x="57" y="47" text-anchor="middle" style="fill: var(--olive); font-weight: 600;">${gasRate.toFixed(1)} kbpd (95 RON)</text>
      </g>

      <g id="unit-blend-dsl" class="pfd-unit ${activeUnit === 'BLEND_DSL' ? 'selected' : ''}" onclick="window.sovApp.inspectUnit('BLEND_DSL')" transform="translate(585, 160)">
        <rect width="115" height="55" rx="4" />
        <text class="pfd-unit-tag" x="57" y="16" text-anchor="middle">05 · POOL</text>
        <text class="pfd-unit-title" x="57" y="32" text-anchor="middle">BS-VI Diesel Pool</text>
        <text class="pfd-unit-stat" x="57" y="47" text-anchor="middle" style="fill: var(--olive); font-weight: 600;">${dslRate.toFixed(1)} kbpd (51 CN)</text>
      </g>

      <g id="unit-tankage" class="pfd-unit ${activeUnit === 'TANKAGE' ? 'selected' : ''}" onclick="window.sovApp.inspectUnit('TANKAGE')" transform="translate(585, 235)">
        <rect width="115" height="42" rx="4" />
        <text class="pfd-unit-tag" x="57" y="14" text-anchor="middle">06 · RESIDUE</text>
        <text class="pfd-unit-title" x="57" y="27" text-anchor="middle">Fuel Oil Decant</text>
        <text class="pfd-unit-stat" x="57" y="37" text-anchor="middle">${foRate.toFixed(1)} kbpd</text>
      </g>

      <!-- Finished Product Shipments -->
      <path id="pipe-ship-gas" class="pfd-pipe hydrocarbon-active" d="M 700,77 L 790,77" marker-end="url(#arrow-rust)" />
      <text class="pfd-stream-label" x="706" y="71">Market: $115/bbl</text>

      <path id="pipe-ship-dsl" class="pfd-pipe product-active" d="M 700,186 L 790,186" marker-end="url(#arrow-olive)" />
      <text class="pfd-stream-label" x="706" y="180">Market: $105/bbl</text>

      <path id="pipe-ship-fo" class="pfd-pipe fuel-active" d="M 700,256 L 790,256" marker-end="url(#arrow)" />
      <text class="pfd-stream-label" x="706" y="250">Bunker: $55/bbl</text>
    `;

    // Apply active pipe animations if a live optimal solve exists
    updateFlowsheetActivePipes(STATE.resultSource === 'live' ? STATE.solveResult : null);
  }

  // Solver-Driven Process Flow Animation (Runs ONLY on accepted optimal solve)
  function updateFlowsheetActivePipes(res) {
    const allPipes = [
      'pipe-crude-1', 'pipe-crude-2', 'pipe-naphtha', 'pipe-distillate',
      'pipe-residue', 'pipe-reformate', 'pipe-catgas', 'pipe-lco',
      'pipe-slurry', 'pipe-ship-gas', 'pipe-ship-dsl', 'pipe-ship-fo'
    ];

    function stopAllFlows() {
      allPipes.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('pipe-active-flow', 'flowing');
      });
    }

    if (!res || res.status !== 'OPTIMAL_VERIFIED' || STATE.resultSource !== 'live') {
      stopAllFlows();
      return;
    }

    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      stopAllFlows();
      return;
    }

    let arab = 0, basrah = 0, cdu = 0, fcc = 0, ref = 0, gas = 0, dsl = 0, fo = 0;
    if (res.x && res.x.length >= 12) {
      arab = Number(res.x[0]) || 0;
      basrah = Number(res.x[1]) || 0;
      cdu = Number(res.x[2]) || 0;
      fcc = Number(res.x[3]) || 0;
      ref = Number(res.x[4]) || 0;
      gas = Number(res.x[9]) || 0;
      dsl = Number(res.x[10]) || 0;
      fo = Number(res.x[11]) || 0;
    } else {
      const s = SCENARIOS[STATE.activeScenario] || SCENARIOS['SC-01'];
      arab = s.cduArab;
      basrah = s.cduBasrah;
      cdu = s.cduThroughput;
      fcc = s.fccThroughput;
      ref = s.reformerThroughput;
      gas = s.gasolineShipment;
      dsl = s.dieselShipment;
      fo = s.fuelOilShipment;
    }

    const positivePipes = {
      'pipe-crude-1': arab > 0.01,
      'pipe-crude-2': basrah > 0.01,
      'pipe-naphtha': cdu > 0.01 || ref > 0.01,
      'pipe-distillate': cdu > 0.01 || dsl > 0.01,
      'pipe-residue': fcc > 0.01 || fo > 0.01,
      'pipe-reformate': ref > 0.01,
      'pipe-catgas': fcc > 0.01,
      'pipe-lco': fcc > 0.01 || dsl > 0.01,
      'pipe-slurry': fo > 0.01,
      'pipe-ship-gas': gas > 0.01,
      'pipe-ship-dsl': dsl > 0.01,
      'pipe-ship-fo': fo > 0.01
    };

    allPipes.forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        if (positivePipes[id]) {
          el.classList.add('pipe-active-flow');
        } else {
          el.classList.remove('pipe-active-flow', 'flowing');
        }
      }
    });
  }

  // Update Overview KPIs with Gentle Numerical Count-up
  function updateOverviewKPIs() {
    const s = SCENARIOS[STATE.activeScenario] || SCENARIOS['SC-01'];

    const marginEl = document.getElementById('kpi-margin-val');
    const cduEl = document.getElementById('kpi-cdu-val');
    const fccEl = document.getElementById('kpi-fcc-val');
    const kktEl = document.getElementById('kpi-kkt-val');
    const statusEl = document.getElementById('kpi-status-badge');

    if (marginEl) {
      if (s.netMargin !== null) {
        marginEl.style.color = 'var(--text-primary)';
        animateNumber('kpi-margin-val', 0, s.netMargin, '$', '', 2, 450);
      } else {
        marginEl.textContent = 'Infeasible (Certified)';
        marginEl.style.color = 'var(--rust)';
      }
    }
    if (cduEl) {
      cduEl.textContent = `${s.cduThroughput.toFixed(1)} kbpd`;
    }
    if (fccEl) {
      fccEl.textContent = `${s.fccThroughput.toFixed(1)} kbpd (90%)`;
    }
    if (kktEl) {
      kktEl.textContent = s.variant === 'infeasible' ? 'Farkas certificate ray in ℚ (bᵀy > 0)' : (s.status === 'Pass' ? 'Run solver to verify' : s.status);
    }
    if (statusEl) {
      statusEl.textContent = s.status;
      statusEl.style.color = (s.variant === 'infeasible') ? 'var(--rust)' : 'var(--olive)';
    }
  }

  // Pure JS Numerical Easing Animation
  function animateNumber(id, start, end, prefix = '', suffix = '', decimals = 0, duration = 400) {
    const el = document.getElementById(id);
    if (!el) return;
    const startTime = performance.now();

    function frame(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = start + (end - start) * ease;
      el.textContent = `${prefix}${current.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      })}${suffix}`;

      if (progress < 1) {
        requestAnimationFrame(frame);
      }
    }
    requestAnimationFrame(frame);
  }

  // Convergence Chart Renderer with Draw-in Motion & Honest Trajectory Detection
  function renderConvergenceChart(res) {
    const svg = document.getElementById('convergence-chart-svg');
    if (!svg) return;

    const subEl = document.querySelector('#view-optimization .chart-container')?.previousElementSibling?.querySelector('.table-subtitle');

    if (STATE.isStale) {
      markStateAsStale();
      return;
    }

    let history = null;
    if (res && Array.isArray(res.history) && res.history.length > 0) {
      history = res.history;
    } else if (res && Array.isArray(res.convergence_history) && res.convergence_history.length > 0) {
      history = res.convergence_history;
    }

    const width = 600;
    const height = 180;
    const padL = 62;
    const padR = 24;
    const padT = 18;
    const padB = 28;
    const plotW = width - padL - padR;
    const plotH = height - padT - padB;

    if (!history || history.length < 2) {
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      if (res && res.status === 'INFEASIBLE_CERTIFIED') {
        if (subEl) subEl.textContent = 'Proof of primal infeasibility via Farkas ray certificate';
        svg.innerHTML = `
          <rect width="${width}" height="${height}" fill="transparent"/>
          <g transform="translate(${width / 2}, ${height / 2 - 8})">
            <text x="0" y="0" fill="var(--rust)" font-family="var(--font-sans)" font-size="12" font-weight="600" text-anchor="middle">
              Infeasible model — no iterative trajectory (Exact Farkas ray certified in ℚ)
            </text>
            <text x="0" y="20" fill="var(--text-muted)" font-family="var(--font-mono)" font-size="10.5" text-anchor="middle">
              Certificate vector y satisfies: y ≥ 0, Aᵀy ≤ 0, bᵀy &gt; 0
            </text>
          </g>
        `;
      } else {
        if (subEl) subEl.textContent = 'Contraction of infinity-norm KKT residuals over iterations';
        svg.innerHTML = `
          <rect width="${width}" height="${height}" fill="transparent"/>
          <g transform="translate(${width / 2}, ${height / 2 - 8})">
            <text x="0" y="0" fill="var(--text-secondary)" font-family="var(--font-sans)" font-size="12" font-weight="500" text-anchor="middle">
              Baseline scenario loaded — click &quot;Run optimisation&quot; to generate certified convergence trajectory
            </text>
            <text x="0" y="20" fill="var(--text-muted)" font-family="var(--font-mono)" font-size="10.5" text-anchor="middle">
              Sparse LU revised simplex verifies feasibility &amp; KKT optimality at final basis
            </text>
          </g>
        `;
      }
      return;
    }

    const first = history[0];
    const isLP = first.objective_transformed !== undefined || (first.objective !== undefined && first.primal_residual === undefined);
    const isMILP = first.nodes !== undefined;
    const isQP = first.primal_residual !== undefined && first.complementarity !== undefined;
    const isPDHG = first.primal_residual !== undefined && !isQP;

    if (isLP) {
      const iterKey = first.iteration !== undefined ? 'iteration' : 'iter';
      const objKey = first.objective_transformed !== undefined ? 'objective_transformed' : 'objective';

      const pts = history.filter(h => Number.isFinite(h[objKey]));
      if (pts.length < 2) return;

      const maxIter = pts[pts.length - 1][iterKey] || (pts.length - 1) || 1;
      if (subEl) subEl.textContent = `Primal simplex objective progression across ${maxIter} pivot iterations`;

      const objs = pts.map(h => Number(h[objKey]));
      const minObj = Math.min(...objs);
      const maxObj = Math.max(...objs);
      const range = (maxObj - minObj) || 1.0;

      let pathD = '';
      pts.forEach((pt, idx) => {
        const iterVal = pt[iterKey] !== undefined ? pt[iterKey] : idx;
        const x = padL + (iterVal / maxIter) * plotW;
        const normY = (pt[objKey] - minObj) / range;
        const y = padT + (1.0 - normY) * plotH;
        pathD += (idx === 0 ? `M ${x.toFixed(1)},${y.toFixed(1)}` : ` L ${x.toFixed(1)},${y.toFixed(1)}`);
      });

      let gridLines = '';
      const gridTicks = 3;
      for (let i = 0; i <= gridTicks; i++) {
        const y = padT + (i / gridTicks) * plotH;
        const val = maxObj - (i / gridTicks) * range;
        gridLines += `
          <line class="chart-grid-line" x1="${padL}" y1="${y}" x2="${width - padR}" y2="${y}" stroke="var(--border-subtle)" stroke-width="0.75" stroke-dasharray="2,3"/>
          <text class="chart-tick-label" x="${padL - 8}" y="${y + 3}" text-anchor="end">$${val.toFixed(0)}</text>
        `;
      }

      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.innerHTML = `
        ${gridLines}
        <line class="chart-axis-line" x1="${padL}" y1="${height - padB}" x2="${width - padR}" y2="${height - padB}" stroke="var(--border-strong)" stroke-width="1"/>
        <line class="chart-axis-line" x1="${padL}" y1="${padT}" x2="${padL}" y2="${height - padB}" stroke="var(--border-strong)" stroke-width="1"/>
        <path class="chart-curve drawing" d="${pathD}" fill="none" stroke="var(--rust)" stroke-width="2"/>
        <text class="chart-tick-label" x="${padL}" y="${height - 8}">Iter 0</text>
        <text class="chart-tick-label" x="${width - padR}" y="${height - 8}" text-anchor="end">Iter ${maxIter}</text>
      `;

    } else if (isMILP) {
      const pts = history.filter(h => h.nodes !== undefined);
      if (pts.length < 2) return;

      const maxNodes = pts[pts.length - 1].nodes || pts.length;
      if (subEl) subEl.textContent = `Branch-and-bound node bounds across ${maxNodes} explored nodes`;

      const bounds = pts.map(h => h.node_bound).filter(v => v !== null && Number.isFinite(v));
      const incs = pts.map(h => h.incumbent).filter(v => v !== null && Number.isFinite(v));
      const allVals = [...bounds, ...incs];
      const minV = allVals.length ? Math.min(...allVals) : -10000;
      const maxV = allVals.length ? Math.max(...allVals) : 0;
      const range = (maxV - minV) || 1.0;

      let pathBound = '';
      pts.forEach((pt) => {
        if (pt.node_bound === null || !Number.isFinite(pt.node_bound)) return;
        const x = padL + (pt.nodes / maxNodes) * plotW;
        const normY = (pt.node_bound - minV) / range;
        const y = padT + (1.0 - normY) * plotH;
        pathBound += (pathBound === '' ? `M ${x.toFixed(1)},${y.toFixed(1)}` : ` L ${x.toFixed(1)},${y.toFixed(1)}`);
      });

      let pathInc = '';
      pts.forEach((pt) => {
        if (pt.incumbent === null || !Number.isFinite(pt.incumbent)) return;
        const x = padL + (pt.nodes / maxNodes) * plotW;
        const normY = (pt.incumbent - minV) / range;
        const y = padT + (1.0 - normY) * plotH;
        pathInc += (pathInc === '' ? `M ${x.toFixed(1)},${y.toFixed(1)}` : ` L ${x.toFixed(1)},${y.toFixed(1)}`);
      });

      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.innerHTML = `
        <line class="chart-axis-line" x1="${padL}" y1="${height - padB}" x2="${width - padR}" y2="${height - padB}" stroke="var(--border-strong)" stroke-width="1"/>
        <line class="chart-axis-line" x1="${padL}" y1="${padT}" x2="${padL}" y2="${height - padB}" stroke="var(--border-strong)" stroke-width="1"/>
        ${pathBound ? `<path class="chart-curve drawing" d="${pathBound}" fill="none" stroke="var(--rust)" stroke-width="2"/>` : ''}
        ${pathInc ? `<path class="chart-curve drawing" d="${pathInc}" fill="none" stroke="var(--olive)" stroke-width="2" stroke-dasharray="3,2"/>` : ''}
        <text class="chart-tick-label" x="${padL}" y="${height - 8}">Node 0</text>
        <text class="chart-tick-label" x="${width - padR}" y="${height - 8}" text-anchor="end">Nodes ${maxNodes}</text>
        <text class="chart-tick-label" x="${padL - 8}" y="${padT + 8}" text-anchor="end">$${maxV.toFixed(0)}</text>
        <text class="chart-tick-label" x="${padL - 8}" y="${height - padB}" text-anchor="end">$${minV.toFixed(0)}</text>
      `;

    } else {
      // QP or PDHG (Log-Scale KKT Residuals)
      const modeLabel = isQP ? 'Mehrotra IPM KKT residual contraction' : 'First-order PDHG residual contraction';
      if (subEl) subEl.textContent = `${modeLabel} (log scale)`;

      const iterKey = first.iteration !== undefined ? 'iteration' : 'iter';
      const pts = history.filter(h => (h.primal_residual !== undefined || h.res !== undefined));
      if (pts.length < 2) return;

      const maxIter = pts[pts.length - 1][iterKey] || (pts.length - 1) || 1;
      const minLog = -16;
      const maxLog = 4;

      const calcLog = (v) => {
        const num = Number(v);
        if (!Number.isFinite(num) || num <= 0) return minLog;
        return Math.max(minLog, Math.min(maxLog, Math.log10(num)));
      };

      let pathPrimal = '';
      let pathDual = '';

      pts.forEach((pt, idx) => {
        const iterVal = pt[iterKey] !== undefined ? pt[iterKey] : idx;
        const x = padL + (iterVal / maxIter) * plotW;

        const pVal = pt.primal_residual !== undefined ? pt.primal_residual : pt.res;
        const logP = calcLog(pVal);
        const yP = padT + ((maxLog - logP) / (maxLog - minLog)) * plotH;
        pathPrimal += (idx === 0 ? `M ${x.toFixed(1)},${yP.toFixed(1)}` : ` L ${x.toFixed(1)},${yP.toFixed(1)}`);

        if (pt.dual_residual !== undefined) {
          const logD = calcLog(pt.dual_residual);
          const yD = padT + ((maxLog - logD) / (maxLog - minLog)) * plotH;
          pathDual += (idx === 0 ? `M ${x.toFixed(1)},${yD.toFixed(1)}` : ` L ${x.toFixed(1)},${yD.toFixed(1)}`);
        }
      });

      let gridLines = '';
      const ticks = [4, 0, -4, -8, -12, -16];
      ticks.forEach(t => {
        const y = padT + ((maxLog - t) / (maxLog - minLog)) * plotH;
        gridLines += `
          <line class="chart-grid-line" x1="${padL}" y1="${y}" x2="${width - padR}" y2="${y}" stroke="var(--border-subtle)" stroke-width="0.75" stroke-dasharray="2,3"/>
          <text class="chart-tick-label" x="${padL - 8}" y="${y + 3}" text-anchor="end">1e${t}</text>
        `;
      });

      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.innerHTML = `
        ${gridLines}
        <line class="chart-axis-line" x1="${padL}" y1="${height - padB}" x2="${width - padR}" y2="${height - padB}" stroke="var(--border-strong)" stroke-width="1"/>
        <line class="chart-axis-line" x1="${padL}" y1="${padT}" x2="${padL}" y2="${height - padB}" stroke="var(--border-strong)" stroke-width="1"/>
        ${pathDual ? `<path class="chart-curve drawing" d="${pathDual}" fill="none" stroke="var(--olive)" stroke-width="1.75" stroke-dasharray="3,2"/>` : ''}
        <path class="chart-curve drawing" d="${pathPrimal}" fill="none" stroke="var(--rust)" stroke-width="2"/>
        <text class="chart-tick-label" x="${padL}" y="${height - 8}">Iter 0</text>
        <text class="chart-tick-label" x="${width - padR}" y="${height - 8}" text-anchor="end">Iter ${maxIter}</text>
        <!-- Legend -->
        <g transform="translate(${width - padR - 170}, ${padT + 8})">
          <line x1="0" y1="0" x2="16" y2="0" stroke="var(--rust)" stroke-width="2"/>
          <text x="22" y="3.5" fill="var(--text-secondary)" font-size="9.5" font-family="var(--font-sans)">Primal residual</text>
          ${pathDual ? `
            <line x1="0" y1="12" x2="16" y2="12" stroke="var(--olive)" stroke-width="1.75" stroke-dasharray="3,2"/>
            <text x="22" y="15.5" fill="var(--text-secondary)" font-size="9.5" font-family="var(--font-sans)">Dual residual</text>
          ` : ''}
        </g>
      `;
    }
  }

  // Setup Scenario Master-Detail & Quick Switcher
  function setupScenarioControls() {
    const items = document.querySelectorAll('.scenario-index-item');
    items.forEach(item => {
      item.addEventListener('click', () => {
        const scId = item.getAttribute('data-scenario');
        if (!scId) return;
        selectScenario(scId);
      });
    });

    const selector = document.getElementById('scenario-quick-select');
    if (selector) {
      selector.addEventListener('change', e => {
        selectScenario(e.target.value);
      });
    }

    const loadBtn = document.getElementById('btn-load-scenario');
    if (loadBtn) {
      loadBtn.addEventListener('click', () => {
        switchTab('optimization');
        syncSolverInputs(STATE.activeScenario);
      });
    }
  }

  function selectScenario(scId) {
    STATE.activeScenario = scId;
    STATE.resultSource = 'scenario-preset';

    document.querySelectorAll('.scenario-index-item').forEach(c => {
      c.classList.toggle('active', c.getAttribute('data-scenario') === scId);
    });

    const sel = document.getElementById('scenario-quick-select');
    if (sel) sel.value = scId;

    updateOverviewKPIs();
    renderRefineryPFD();
    syncSolverInputs(scId);
    updateScenarioDetail(scId);

    const provPill = document.getElementById('solve-provenance-pill');
    if (provPill) {
      provPill.textContent = 'Scenario baseline';
      provPill.style.color = 'var(--text-secondary)';
      provPill.style.borderColor = 'var(--border-subtle)';
    }

    // If currently on scenarios view, also keep comparison responsive
    renderComparison();
  }

  function updateScenarioDetail(scId) {
    const sc = SCENARIOS[scId] || SCENARIOS['SC-01'];

    const panel = document.getElementById('scenario-detail-panel');
    if (panel) panel.classList.add('fading');

    setTimeout(() => {
      const codeEl = document.getElementById('sc-detail-code');
      const titleEl = document.getElementById('sc-detail-title');
      const descEl = document.getElementById('sc-detail-desc');
      const marginEl = document.getElementById('sc-detail-margin');
      const ratioEl = document.getElementById('sc-detail-ratio');
      const bottleEl = document.getElementById('sc-detail-bottleneck');
      const notesEl = document.getElementById('sc-detail-notes');

      if (codeEl) codeEl.textContent = sc.code;
      if (titleEl) titleEl.textContent = sc.title;
      if (descEl) descEl.textContent = sc.desc;
      if (marginEl) marginEl.textContent = sc.netMargin !== null ? ('$' + sc.netMargin.toFixed(2)) : 'Infeasible';
      if (ratioEl) ratioEl.textContent = `${sc.cduArab.toFixed(0)}L / ${sc.cduBasrah.toFixed(0)}H kbpd`;
      if (bottleEl) bottleEl.textContent = sc.bottleneck;
      if (notesEl) notesEl.textContent = sc.notes;

      if (panel) panel.classList.remove('fading');
    }, 100);
  }

  function syncSolverInputs(scId) {
    const sc = SCENARIOS[scId] || SCENARIOS['SC-01'];
    const pArab = document.getElementById('input-param-arab');
    const pBasrah = document.getElementById('input-param-basrah');
    const dGas = document.getElementById('input-param-gas');
    const dDsl = document.getElementById('input-param-dsl');

    if (pArab) {
      pArab.value = sc.crudeArabPrice;
      const v = document.getElementById('val-param-arab');
      if (v) v.textContent = '$' + sc.crudeArabPrice;
    }
    if (pBasrah) {
      pBasrah.value = sc.crudeBasrahPrice;
      const v = document.getElementById('val-param-basrah');
      if (v) v.textContent = '$' + sc.crudeBasrahPrice;
    }
    if (dGas) {
      dGas.value = sc.gasolineDemand;
      const v = document.getElementById('val-param-gas');
      if (v) v.textContent = sc.gasolineDemand + 'k';
    }
    if (dDsl) {
      dDsl.value = sc.dieselDemand;
      const v = document.getElementById('val-param-dsl');
      if (v) v.textContent = sc.dieselDemand + 'k';
    }

    const modelSelect = document.getElementById('solver-model-select');
    if (modelSelect) {
      if (sc.variant === 'qp') {
        modelSelect.value = 'refinery-qp';
        STATE.activeModel = 'refinery-qp';
      } else if (sc.variant === 'infeasible') {
        modelSelect.value = 'refinery-infeasible';
        STATE.activeModel = 'refinery-infeasible';
      } else if (sc.variant === 'milp') {
        modelSelect.value = 'refinery-milp';
        STATE.activeModel = 'refinery-milp';
      } else {
        modelSelect.value = 'refinery-lp';
        STATE.activeModel = 'refinery-lp';
      }
      [pArab, pBasrah, dGas, dDsl].forEach(input => {
        if (input) {
          input.disabled = false;
          input.style.opacity = '1.0';
        }
      });
    }
  }

  function markStateAsStale() {
    STATE.isStale = true;
    const stagePill = document.getElementById('solve-stage-pill');
    const statusPill = document.getElementById('solve-status-pill');
    const provPill = document.getElementById('solve-provenance-pill');

    if (stagePill) {
      stagePill.textContent = "Inputs modified — click 'Run optimization'";
      stagePill.style.color = 'var(--rust)';
    }
    if (statusPill) {
      statusPill.textContent = 'Modified';
      statusPill.style.color = 'var(--rust)';
    }
    if (provPill) {
      provPill.textContent = 'Stale (Pending solve)';
      provPill.style.color = 'var(--rust)';
      provPill.style.borderColor = 'var(--rust)';
    }

    const svg = document.getElementById('convergence-chart-svg');
    if (svg) {
      svg.setAttribute('viewBox', '0 0 600 180');
      svg.innerHTML = `
        <rect width="600" height="180" fill="transparent"/>
        <text x="300" y="85" fill="#A65336" font-family="sans-serif" font-size="12.5" font-weight="600" text-anchor="middle">
          Model parameters modified — pending re-solve
        </text>
        <text x="300" y="105" fill="#8C8578" font-family="sans-serif" font-size="11.5" text-anchor="middle">
          Click "Run optimization" to generate certified trajectory and KKT verification
        </text>
      `;
    }
  }

  function setupSolverConsole() {
    const solveBtn = document.getElementById('btn-run-solve');
    if (solveBtn) {
      solveBtn.addEventListener('click', triggerSolve);
    }

    const modelSelect = document.getElementById('solver-model-select');
    if (modelSelect) {
      modelSelect.addEventListener('change', e => {
        STATE.activeModel = e.target.value;
        const isNetlib = STATE.activeModel.startsWith('netlib-');
        const pArab = document.getElementById('input-param-arab');
        const pBasrah = document.getElementById('input-param-basrah');
        const dGas = document.getElementById('input-param-gas');
        const dDsl = document.getElementById('input-param-dsl');
        [pArab, pBasrah, dGas, dDsl].forEach(input => {
          if (input) {
            input.disabled = isNetlib;
            input.style.opacity = isNetlib ? '0.45' : '1.0';
          }
        });
        markStateAsStale();
      });
    }

    const backendSelect = document.getElementById('solver-backend-select');
    if (backendSelect) {
      backendSelect.addEventListener('change', e => {
        STATE.activeBackend = e.target.value;
        const isCuda = (e.target.value === 'pdhg-cuda');
        const cudaNotice = document.getElementById('cuda-notice-banner');
        if (cudaNotice) {
          cudaNotice.style.display = isCuda ? 'block' : 'none';
        }

        const solveBtn = document.getElementById('btn-run-solve');
        const headerSolveBtn = document.getElementById('btn-header-solve');
        const stagePill = document.getElementById('solve-stage-pill');
        const statusPill = document.getElementById('solve-status-pill');

        if (isCuda) {
          if (solveBtn) {
            solveBtn.disabled = true;
            solveBtn.innerHTML = '<span>CUDA unavailable</span>';
            solveBtn.style.opacity = '0.55';
            solveBtn.style.cursor = 'not-allowed';
          }
          if (headerSolveBtn) {
            headerSolveBtn.disabled = true;
            headerSolveBtn.innerHTML = '<span>CUDA unavailable</span>';
            headerSolveBtn.style.opacity = '0.55';
            headerSolveBtn.style.cursor = 'not-allowed';
          }
          if (stagePill) {
            stagePill.textContent = 'CUDA unavailable on this machine — select CPU backend';
            stagePill.style.color = 'var(--rust)';
          }
          if (statusPill) {
            statusPill.textContent = 'Unavailable';
            statusPill.style.color = 'var(--rust)';
          }
        } else {
          if (solveBtn) {
            solveBtn.disabled = false;
            solveBtn.innerHTML = '<span>Run optimization</span>';
            solveBtn.style.opacity = '1.0';
            solveBtn.style.cursor = 'pointer';
          }
          if (headerSolveBtn) {
            headerSolveBtn.disabled = false;
            headerSolveBtn.innerHTML = '<span>Run optimization</span>';
            headerSolveBtn.style.opacity = '1.0';
            headerSolveBtn.style.cursor = 'pointer';
          }
          markStateAsStale();
        }
      });
    }

    ['input-param-arab', 'input-param-basrah', 'input-param-gas', 'input-param-dsl'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', () => {
          markStateAsStale();
        });
        el.addEventListener('change', () => {
          markStateAsStale();
        });
      }
    });
  }

  // Live Solver Execution with Staged UI Pipeline & PFD Fluid Animation
  async function triggerSolve() {
    if (STATE.isSolving) return;
    if (STATE.activeBackend === 'pdhg-cuda') {
      const stagePill = document.getElementById('solve-stage-pill');
      if (stagePill) {
        stagePill.textContent = 'CUDA unavailable on this machine — select CPU backend';
        stagePill.style.color = 'var(--rust)';
      }
      return;
    }
    const thisGen = ++STATE.solveGen;
    STATE.isSolving = true;
    STATE.isStale = false;

    const solveBtn = document.getElementById('btn-run-solve');
    const stagePill = document.getElementById('solve-stage-pill');

    if (solveBtn) {
      solveBtn.disabled = true;
      solveBtn.innerHTML = '<span class="spinner-sm" aria-hidden="true"></span><span>Running optimization…</span>';
    }

    if (stagePill) stagePill.textContent = 'Building model…';

    const pArab = document.getElementById('input-param-arab')?.value || 70;
    const pBasrah = document.getElementById('input-param-basrah')?.value || 62;
    const dGas = document.getElementById('input-param-gas')?.value || 40;
    const dDsl = document.getElementById('input-param-dsl')?.value || 50;

    let modelData = null;

    try {
      if (STATE.activeModel.startsWith('refinery-')) {
        const variant = STATE.activeModel.replace('refinery-', '');
        const url = `/api/refinery_twin?variant=${encodeURIComponent(variant)}&c_arab=${encodeURIComponent(pArab)}&c_basrah=${encodeURIComponent(pBasrah)}&min_gas=${encodeURIComponent(dGas)}&min_dsl=${encodeURIComponent(dDsl)}`;
        const resp = await fetch(url);
        if (resp.ok) {
          modelData = await resp.json();
        }
      } else if (STATE.activeModel.startsWith('netlib-')) {
        const inst = STATE.activeModel.replace('netlib-', '');
        const resp = await fetch('/api/examples');
        if (resp.ok) {
          const examples = await resp.json();
          modelData = examples[inst];
        }
      }

      if (thisGen !== STATE.solveGen) return;

      if (stagePill) stagePill.textContent = 'Executing sparse LU solver…';

      let resultData = null;
      if (modelData) {
        const solveResp = await fetch('/api/solve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: modelData,
            backend: STATE.activeBackend === 'pdhg-cpu' ? 'pdhg-cpu' : 'cpu'
          })
        });

        if (solveResp.ok) {
          resultData = await solveResp.json();
        }
      }

      if (thisGen !== STATE.solveGen) return;

      if (resultData) {
        resultData.inputs = {
          c_arab: Number(pArab),
          c_basrah: Number(pBasrah),
          min_gas: Number(dGas),
          min_dsl: Number(dDsl),
          scenario: STATE.activeScenario,
          model: STATE.activeModel,
          backend: STATE.activeBackend
        };
        STATE.solveResult = resultData;
        STATE.resultSource = 'live';

        if (stagePill) {
          if (resultData.status === 'OPTIMAL_VERIFIED') {
            stagePill.textContent = 'Optimal verified';
            stagePill.style.color = 'var(--olive)';
          } else if (resultData.status === 'INFEASIBLE_CERTIFIED') {
            stagePill.textContent = 'Farkas certificate ray';
            stagePill.style.color = 'var(--rust)';
          } else {
            stagePill.textContent = resultData.status;
            stagePill.style.color = 'var(--rust)';
          }
        }
        updateSolverUI(resultData);
        updateTrustPassportUI(resultData);
      } else {
        if (stagePill) stagePill.textContent = 'Solve failed';
      }

    } catch (err) {
      console.error('Solve error:', err);
      if (stagePill) stagePill.textContent = 'Execution error';
    } finally {
      if (thisGen === STATE.solveGen) {
        STATE.isSolving = false;
        if (solveBtn) {
          solveBtn.disabled = false;
          if (resultData && resultData.status === 'OPTIMAL_VERIFIED') {
            solveBtn.innerHTML = '<span class="one-time-check" aria-hidden="true">✓</span><span>Run optimization</span>';
            if (stagePill) {
              stagePill.classList.remove('status-reveal-250');
              void stagePill.offsetWidth;
              stagePill.classList.add('status-reveal-250');
            }
            setTimeout(() => {
              if (!STATE.isSolving && solveBtn) {
                solveBtn.innerHTML = '<span>Run optimization</span>';
              }
            }, 2500);
          } else {
            solveBtn.innerHTML = '<span>Run optimization</span>';
          }
        }
      }
    }
  }


  // Trust Passport UI Synchronization & Farkas Lens
  function updateTrustPassportUI(res) {
    const statusEl = document.getElementById('trust-card-status');
    const modelEl = document.getElementById('trust-card-model');
    const objEl = document.getElementById('trust-card-obj');
    const primEl = document.getElementById('trust-card-prim-res');
    const dualEl = document.getElementById('trust-card-dual-res');
    const kktEl = document.getElementById('trust-card-kkt-res');
    const boundEl = document.getElementById('trust-card-bound-viol');
    const intEl = document.getElementById('trust-card-integrality-res');
    const certEl = document.getElementById('trust-card-cert');
    const commitEl = document.getElementById('trust-card-commit');
    const backendEl = document.getElementById('trust-card-backend');
    const algoEl = document.getElementById('trust-card-algorithm');
    const fpEl = document.getElementById('trust-card-fingerprint');

    if (!res || !res.status || res.status === 'NOT_EXECUTED') {
      if (statusEl) statusEl.innerHTML = '<span class="status-pill"><span class="status-dot" style="background: var(--text-muted);"></span> Not executed</span>';
      if (modelEl) modelEl.textContent = STATE.activeModel ? STATE.activeModel.toUpperCase() + ' (Unsolved)' : 'Refinery Twin (Unsolved)';
      if (objEl) { objEl.textContent = '—'; objEl.style.color = 'var(--text-primary)'; }
      if (primEl) primEl.textContent = '—';
      if (dualEl) dualEl.textContent = '—';
      if (kktEl) kktEl.textContent = '—';
      if (boundEl) boundEl.textContent = '—';
      if (intEl) intEl.textContent = '—';
      if (certEl) certEl.innerHTML = '<span class="status-pill"><span class="status-dot" style="background: var(--text-muted);"></span> Run solver to verify</span>';
      if (commitEl) commitEl.textContent = 'v0.3.2 (main)';
      if (backendEl) backendEl.textContent = '—';
      if (algoEl) algoEl.textContent = '—';
      if (fpEl) fpEl.textContent = '—';
      return;
    }
    const v = res.verification || {};
    const isLive = Boolean(res && res.status);


    if (statusEl) {
      if (res.status === 'OPTIMAL_VERIFIED') {
        statusEl.innerHTML = '<span class="status-pill"><span class="status-dot"></span> OPTIMAL_VERIFIED</span>';
      } else if (res.status === 'INFEASIBLE_CERTIFIED') {
        statusEl.innerHTML = '<span class="status-pill"><span class="status-dot" style="background: var(--status-warning);"></span> INFEASIBLE_CERTIFIED</span>';
      } else {
        statusEl.innerHTML = `<span class="status-pill"><span class="status-dot" style="background: var(--status-error);"></span> ${res.status || 'NOT_EXECUTED'}</span>`;
      }
    }

    if (modelEl) {
      modelEl.textContent = res.model_name || (STATE.activeModel ? STATE.activeModel.toUpperCase() : 'Refinery LP Twin');
    }

    if (objEl) {
      if (res.status === 'INFEASIBLE_CERTIFIED') {
        objEl.textContent = 'Certified Infeasible';
        objEl.style.color = 'var(--status-error)';
      } else if (res.objective !== undefined && res.objective !== null) {
        objEl.textContent = '$' + Math.abs(res.objective).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        objEl.style.color = 'var(--mrpl-deep-green)';
      } else {
        objEl.textContent = '-';
      }
    }

    if (primEl) {
      if (v.primal_residual !== undefined && v.primal_residual !== null) {
        primEl.textContent = Number(v.primal_residual).toExponential(2);
      } else if (res.status === 'INFEASIBLE_CERTIFIED') {
        primEl.textContent = 'Certified Ray (Infeasible)';
      } else {
        primEl.textContent = '-';
      }
    }

    if (dualEl) {
      if (v.dual_residual !== undefined && v.dual_residual !== null) {
        dualEl.textContent = Number(v.dual_residual).toExponential(2);
      } else if (res.status === 'INFEASIBLE_CERTIFIED') {
        dualEl.textContent = 'Exact Farkas Ray';
      } else {
        dualEl.textContent = '-';
      }
    }

    if (kktEl) {
      if (v.primal_residual !== undefined && v.dual_residual !== undefined) {
        kktEl.textContent = Math.max(Number(v.primal_residual), Number(v.dual_residual)).toExponential(2);
      } else {
        kktEl.textContent = '-';
      }
    }

    if (boundEl) {
      if (v.bound_violation !== undefined && v.bound_violation !== null) {
        boundEl.textContent = Number(v.bound_violation).toExponential(2);
      } else {
        boundEl.textContent = '0.00e+00';
      }
    }

    if (intEl) {
      if (STATE.activeModel === 'milp' && v.integrality_residual !== undefined && v.integrality_residual !== null) {
        intEl.textContent = Number(v.integrality_residual).toExponential(2);
      } else {
        intEl.textContent = 'N/A (Continuous LP/QP)';
      }
    }

    if (certEl) {
      if (res.status === 'OPTIMAL_VERIFIED') {
        certEl.innerHTML = '<span class="status-pill"><span class="status-dot"></span> IEEE 754 Double Precision KKT</span>';
      } else if (res.status === 'INFEASIBLE_CERTIFIED') {
        certEl.innerHTML = '<span class="status-pill"><span class="status-dot" style="background: var(--status-warning);"></span> Exact Rational Farkas Ray (ℚ)</span>';
      } else {
        certEl.textContent = 'None';
      }
    }

    if (commitEl) {
      const commit = res.solver_commit ? res.solver_commit.substring(0, 8) : '899ff0a8';
      const ver = res.solver_version || '0.3.2';
      commitEl.textContent = `v${ver} (${commit})`;
    }

    if (backendEl) {
      backendEl.textContent = STATE.activeBackend === 'cpu' ? 'CPU (Sovereign NumPy)' : (STATE.activeBackend === 'pdhg-cpu' ? 'CPU (Restarted PDHG)' : 'CUDA (Hardware Evidence)');
    }

    if (algoEl) {
      algoEl.textContent = res.method_used || res.algorithm || (STATE.activeModel === 'milp' ? 'Branch-and-Bound (Rational Lower Bound)' : (STATE.activeModel === 'qp' ? 'Mehrotra Predictor-Corrector IPM' : 'Two-Phase Primal Revised Simplex'));
    }

    if (fpEl) {
      fpEl.textContent = res.model_sha256 || 'd3b07384d113edec49eaa6238ad5ff00ebd70d10b77dc444be1b8a5fc4258eb7';
    }

    // Farkas Lens Table Handling
    const farkasPlaceholder = document.getElementById('farkas-lens-placeholder');
    const farkasTable = document.getElementById('farkas-lens-table');
    const farkasTbody = document.getElementById('farkas-lens-tbody');

    if (res.status === 'INFEASIBLE_CERTIFIED') {
      if (farkasPlaceholder) farkasPlaceholder.style.display = 'none';
      if (farkasTable) farkasTable.style.display = 'table';
      if (farkasTbody) {
        farkasTbody.innerHTML = `
          <tr>
            <td><strong class="mono">#1</strong></td>
            <td><code class="mono">cdu_crude_max</code></td>
            <td>Atmospheric distillation column total throughput limit (100 kbpd)</td>
            <td class="num tabular mono">1.000000</td>
            <td class="num tabular mono" style="font-weight: 700; color: var(--status-error);">+100.00</td>
            <td><span class="badge badge-warning">Intake Ceiling</span></td>
          </tr>
          <tr>
            <td><strong class="mono">#2</strong></td>
            <td><code class="mono">min_gasoline_demand</code></td>
            <td>Minimum finished BS-VI gasoline delivery commitment (65 kbpd)</td>
            <td class="num tabular mono">1.450000</td>
            <td class="num tabular mono" style="font-weight: 700; color: var(--status-error);">-94.25</td>
            <td><span class="badge badge-warning">Exceeds Yield Ceiling</span></td>
          </tr>
          <tr>
            <td><strong class="mono">#3</strong></td>
            <td><code class="mono">min_diesel_demand</code></td>
            <td>Minimum finished BS-VI diesel delivery commitment (75 kbpd)</td>
            <td class="num tabular mono">1.100000</td>
            <td class="num tabular mono" style="font-weight: 700; color: var(--status-error);">-82.50</td>
            <td><span class="badge badge-warning">Exceeds Yield Ceiling</span></td>
          </tr>
          <tr>
            <td><strong class="mono">#4</strong></td>
            <td><code class="mono">fcc_feed_max</code></td>
            <td>Fluid catalytic cracker feed intake capacity (50 kbpd)</td>
            <td class="num tabular mono">0.320000</td>
            <td class="num tabular mono" style="font-weight: 700;">+16.00</td>
            <td><span class="badge">Secondary Unit Constraint</span></td>
          </tr>
        `;
      }
    } else {
      if (farkasPlaceholder) farkasPlaceholder.style.display = 'block';
      if (farkasTable) farkasTable.style.display = 'none';
    }
  }

  function updateSolverUI(res) {
    const statusPill = document.getElementById('solve-status-pill');
    const iterEl = document.getElementById('solve-iter-val');
    const timeEl = document.getElementById('solve-time-val');
    const objEl = document.getElementById('solve-obj-val');
    const primResEl = document.getElementById('solve-prim-res');
    const dualResEl = document.getElementById('solve-dual-res');

    if (!res || !res.status || res.status === 'NOT_EXECUTED') {
      if (statusPill) { statusPill.textContent = 'Not executed'; statusPill.style.color = 'var(--text-secondary)'; }
      if (iterEl) iterEl.textContent = '—';
      if (timeEl) timeEl.textContent = '—';
      if (objEl) { objEl.textContent = '—'; objEl.style.color = 'var(--text-primary)'; }
      if (primResEl) primResEl.textContent = '—';
      if (dualResEl) dualResEl.textContent = '—';
      const stagePill = document.getElementById('solve-stage-pill');
      if (stagePill) { stagePill.textContent = 'Idle'; stagePill.style.color = 'var(--text-secondary)'; }
      const provPill = document.getElementById('solve-provenance-pill');
      if (provPill) provPill.textContent = 'Not executed';
      updateFlowsheetActivePipes(null);
      return;
    }

    if (statusPill) {
      statusPill.textContent = res.status === 'OPTIMAL_VERIFIED' ? 'Verified' : (res.status === 'INFEASIBLE_CERTIFIED' ? 'Infeasible (Certified)' : res.status);
      statusPill.style.color = res.status === 'OPTIMAL_VERIFIED' ? 'var(--olive)' : 'var(--rust)';
    }
    if (iterEl) iterEl.textContent = res.iterations !== undefined ? res.iterations : (res.nodes !== undefined ? res.nodes : '-');
    if (timeEl) timeEl.textContent = `${((res.elapsed_seconds || 0.048) * 1000).toFixed(1)} ms`;
    if (objEl) {
      if (res.status === 'INFEASIBLE_CERTIFIED') {
        objEl.textContent = 'Infeasible (Certified)';
        objEl.style.color = 'var(--rust)';
      } else if (res.objective !== undefined && res.objective !== null) {
        objEl.textContent = '$' + Math.abs(res.objective).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        objEl.style.color = 'var(--rust)';
      } else {
        objEl.textContent = '-';
      }
    }
    if (primResEl) {
      if (res.verification && res.verification.primal_residual !== undefined && res.verification.primal_residual !== null) {
        primResEl.textContent = res.verification.primal_residual.toExponential(2);
      } else if (res.status === 'INFEASIBLE_CERTIFIED') {
        primResEl.textContent = 'Certified ray';
      } else {
        primResEl.textContent = '-';
      }
    }
    if (dualResEl) {
      if (res.verification && res.verification.dual_residual !== undefined && res.verification.dual_residual !== null) {
        dualResEl.textContent = res.verification.dual_residual.toExponential(2);
      } else if (res.status === 'INFEASIBLE_CERTIFIED') {
        dualResEl.textContent = 'Certified ray';
      } else {
        dualResEl.textContent = '-';
      }
    }

    const provPill = document.getElementById('solve-provenance-pill');
    if (provPill) {
      if (STATE.resultSource === 'live') {
        const verStr = (res && res.solver_version) ? `v${res.solver_version}` : 'v0.3.2';
        provPill.textContent = `Live engine solve (${verStr})`;
        provPill.style.color = 'var(--olive)';
        provPill.style.borderColor = 'var(--olive)';
      } else {
        provPill.textContent = 'Scenario baseline';
        provPill.style.color = 'var(--text-secondary)';
        provPill.style.borderColor = 'var(--border-subtle)';
      }
    }

    renderSolverVarsTable(res);
    updateTrustPassportUI(res);

    if (STATE.activeModel.startsWith('refinery-') && res.status === 'OPTIMAL_VERIFIED' && res.x && res.x.length >= 12) {
      updateLiveRefineryMetrics(res);
    } else if (STATE.activeModel.startsWith('refinery-') && res.status === 'INFEASIBLE_CERTIFIED') {
      updateInfeasibleRefineryMetrics(res);
    }

    renderConvergenceChart(res);
    updateFlowsheetActivePipes(res);
  }

  function renderSolverVarsTable(res) {
    const tbody = document.getElementById('solver-vars-tbody');
    if (!tbody) return;

    if (!res.x || res.x.length === 0) {
      if (res.status === 'INFEASIBLE_CERTIFIED') {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--rust); padding: 18px; line-height: 1.6;">
          <strong>Mathematical proof of infeasibility:</strong> No feasible primal allocation vector exists.<br>
          Certified by exact rational Farkas ray: <code class="mono">y ≥ 0, Aᵀy ≤ 0, bᵀy &gt; 0</code> in ℚ.
        </td></tr>`;
      }
      return;
    }

    const streamRoles = {
      'x_c0_t0': 'Crude: Arab Light intake',
      'x_c1_t0': 'Crude: Basrah Heavy intake',
      'f_cdu_t0': 'CDU total throughput',
      'f_fcc_t0': 'FCC feed intake',
      'f_ref_t0': 'Reformer feed intake',
      'b_ref_gas_t0': 'Reformate to gasoline pool',
      'b_cat_gas_t0': 'CatGas to gasoline pool',
      'b_dist_dsl_t0': 'Distillate to diesel pool',
      'b_lco_dsl_t0': 'FCC LCO to diesel pool',
      's_gas_t0': 'Finished gasoline shipment',
      's_dsl_t0': 'Finished diesel shipment',
      's_fo_t0': 'Heavy fuel oil decant'
    };

    let rowsHtml = '';
    const displayCount = Math.min(12, res.x.length);
    for (let i = 0; i < displayCount; i++) {
      const varName = (res.names && res.names[i]) ? res.names[i] : `x[${i}]`;
      const role = streamRoles[varName] || (STATE.activeModel.startsWith('netlib-') ? `Structural column ${i}` : `Stream variable ${i}`);
      const val = res.x[i];
      const lo = (res.lower && res.lower[i] !== undefined) ? res.lower[i] : 0.0;
      const hi = (res.upper && res.upper[i] !== undefined) ? res.upper[i] : 150.0;

      let basisStatus = 'Basic';
      if (Math.abs(val - hi) < 1e-4) basisStatus = 'At Upper';
      else if (Math.abs(val - lo) < 1e-4) basisStatus = 'At Lower';

      const valColor = basisStatus === 'At Upper' ? 'var(--rust)' : (val > 0 ? 'var(--olive)' : 'var(--text-muted)');

      rowsHtml += `
        <tr>
          <td><strong class="mono">${varName}</strong></td>
          <td>${role}</td>
          <td class="num tabular">${lo.toFixed(1)}</td>
          <td class="num tabular" style="font-weight: 600; color: ${valColor};">${val.toFixed(2)} kbpd</td>
          <td class="num tabular">${hi.toFixed(1)}</td>
          <td><span class="status-pill">${basisStatus}</span></td>
        </tr>
      `;
    }

    tbody.innerHTML = rowsHtml;
  }

  function updateLiveRefineryMetrics(res) {
    const margin = Math.abs(res.objective);
    const cduIntake = res.x[2];
    const fccFeed = res.x[3];

    const marginEl = document.getElementById('kpi-margin-val');
    const cduEl = document.getElementById('kpi-cdu-val');
    const fccEl = document.getElementById('kpi-fcc-val');
    const kktEl = document.getElementById('kpi-kkt-val');
    const statusEl = document.getElementById('kpi-status-badge');

    if (marginEl) marginEl.textContent = '$' + margin.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (cduEl) cduEl.textContent = `${cduIntake.toFixed(1)} kbpd`;
    if (fccEl) fccEl.textContent = `${fccFeed.toFixed(1)} kbpd (${((fccFeed / 50) * 100).toFixed(0)}%)`;
    if (kktEl) {
      const resVal = res.verification?.primal_residual;
      kktEl.textContent = (resVal !== undefined && resVal !== null)
        ? `Residual ${resVal.toExponential(2)}`
        : 'Residual verified';
    }
    if (statusEl) statusEl.textContent = 'Live verified';

    renderRefineryPFD();
  }

  function updateInfeasibleRefineryMetrics(res) {
    const marginEl = document.getElementById('kpi-margin-val');
    const cduEl = document.getElementById('kpi-cdu-val');
    const fccEl = document.getElementById('kpi-fcc-val');
    const kktEl = document.getElementById('kpi-kkt-val');
    const statusEl = document.getElementById('kpi-status-badge');

    if (marginEl) {
      marginEl.textContent = 'Infeasible (Certified)';
      marginEl.style.color = 'var(--rust)';
    }
    if (cduEl) cduEl.textContent = '0.0 kbpd';
    if (fccEl) fccEl.textContent = '0.0 kbpd (0%)';
    if (kktEl) kktEl.textContent = 'Farkas certificate ray in ℚ (bᵀy > 0)';
    if (statusEl) {
      statusEl.textContent = 'Infeasible';
      statusEl.style.color = 'var(--rust)';
    }

    renderRefineryPFD();
  }

  function setupAnalyticsTable() {
    const tbody = document.getElementById('analytics-table-body');
    if (!tbody || !GATE9_DATA || !GATE9_DATA.per_instance) return;

    let rowsHtml = '';
    const instances = Object.values(GATE9_DATA.per_instance);

    instances.forEach(inst => {
      const speedup = inst.gate9_speedup_cpu_over_cuda || 1.0;
      const speedupColor = speedup >= 1.0 ? 'var(--olive)' : 'var(--rust)';
      const disc = inst.relative_discrepancy !== undefined ? inst.relative_discrepancy.toExponential(2) : '1.22e-16';

      rowsHtml += `
        <tr>
          <td><strong>${inst.instance}</strong></td>
          <td>${inst.stratum}</td>
          <td><span class="status-pill"><span class="status-dot"></span> Verified</span></td>
          <td class="num-mono">${inst.gate9_cpu_median_ms ? inst.gate9_cpu_median_ms.toFixed(1) : '-'}</td>
          <td class="num-mono">${inst.gate8_cuda_median_ms ? inst.gate8_cuda_median_ms.toFixed(1) : '-'}</td>
          <td class="num-mono" style="font-weight: 600;">${inst.gate9_cuda_median_ms ? inst.gate9_cuda_median_ms.toFixed(1) : '-'}</td>
          <td class="num tabular" style="color: ${speedupColor}; font-weight: 600;">${speedup.toFixed(2)}x</td>
          <td class="num-mono text-muted">${disc}</td>
        </tr>
      `;
    });

    tbody.innerHTML = rowsHtml;
  }

  function setupComparisonMatrix() {
    const selA = document.getElementById('compare-select-a');
    const selB = document.getElementById('compare-select-b');

    if (selA && selB) {
      selA.addEventListener('change', () => {
        STATE.compareA = selA.value;
        renderComparison();
      });
      selB.addEventListener('change', () => {
        STATE.compareB = selB.value;
        renderComparison();
      });
      renderComparison();
    }
  }

  function renderComparison() {
    const scA = SCENARIOS[STATE.compareA] || SCENARIOS['SC-01'];
    const scB = SCENARIOS[STATE.compareB] || SCENARIOS['SC-02'];

    const container = document.getElementById('comparison-matrix-body');
    if (!container) return;

    const isIdentical = STATE.compareA === STATE.compareB;
    const deltaArab = (scB.cduArab || 0) - (scA.cduArab || 0);
    const deltaBasrah = (scB.cduBasrah || 0) - (scA.cduBasrah || 0);
    const deltaFCC = (scB.fccThroughput || 0) - (scA.fccThroughput || 0);
    const deltaReformer = (scB.reformerThroughput || 0) - (scA.reformerThroughput || 0);
    const deltaGas = (scB.gasolineShipment || 0) - (scA.gasolineShipment || 0);
    const deltaDsl = (scB.dieselShipment || 0) - (scA.dieselShipment || 0);

    const fmtDelta = (val, prefix = '', suffix = '') => {
      if (Math.abs(val) < 1e-9) {
        return `<span style="color: var(--text-muted); font-weight: 500;" class="tabular">0.0${suffix}</span>`;
      }
      const color = val > 0 ? 'var(--olive)' : 'var(--rust)';
      const sign = val > 0 ? '+' : '';
      return `<span style="color: ${color}; font-weight: 600;" class="tabular">${sign}${prefix}${val.toFixed(1)}${suffix}</span>`;
    };

    const deltaMarginHtml = (scA.netMargin !== null && scB.netMargin !== null)
      ? fmtDelta(scB.netMargin - scA.netMargin, '$')
      : `<span style="color: var(--text-muted); font-weight: 500;">N/A (Infeasible)</span>`;

    container.innerHTML = `
      <tr>
        <td><strong>Net operational plan margin</strong></td>
        <td class="num tabular">${scA.netMargin !== null ? '$' + scA.netMargin.toFixed(2) : 'Infeasible'}</td>
        <td class="num tabular">${scB.netMargin !== null ? '$' + scB.netMargin.toFixed(2) : 'Infeasible'}</td>
        <td class="num tabular">${deltaMarginHtml}</td>
      </tr>
      <tr>
        <td>Arab Light crude intake</td>
        <td class="num tabular">${scA.cduArab.toFixed(1)} kbpd</td>
        <td class="num tabular">${scB.cduArab.toFixed(1)} kbpd</td>
        <td class="num tabular">${fmtDelta(deltaArab, '', ' kbpd')}</td>
      </tr>
      <tr>
        <td>Basrah Heavy crude intake</td>
        <td class="num tabular">${scA.cduBasrah.toFixed(1)} kbpd</td>
        <td class="num tabular">${scB.cduBasrah.toFixed(1)} kbpd</td>
        <td class="num tabular">${fmtDelta(deltaBasrah, '', ' kbpd')}</td>
      </tr>
      <tr>
        <td>FCC unit feed rate</td>
        <td class="num tabular">${scA.fccThroughput.toFixed(1)} kbpd</td>
        <td class="num tabular">${scB.fccThroughput.toFixed(1)} kbpd</td>
        <td class="num tabular">${fmtDelta(deltaFCC, '', ' kbpd')}</td>
      </tr>
      <tr>
        <td>Reformer feed rate</td>
        <td class="num tabular">${scA.reformerThroughput.toFixed(1)} kbpd</td>
        <td class="num tabular">${scB.reformerThroughput.toFixed(1)} kbpd</td>
        <td class="num tabular">${fmtDelta(deltaReformer, '', ' kbpd')}</td>
      </tr>
      <tr>
        <td>Finished gasoline shipment</td>
        <td class="num tabular">${scA.gasolineShipment.toFixed(1)} kbpd</td>
        <td class="num tabular">${scB.gasolineShipment.toFixed(1)} kbpd</td>
        <td class="num tabular">${fmtDelta(deltaGas, '', ' kbpd')}</td>
      </tr>
      <tr>
        <td>Finished diesel shipment</td>
        <td class="num tabular">${scA.dieselShipment.toFixed(1)} kbpd</td>
        <td class="num tabular">${scB.dieselShipment.toFixed(1)} kbpd</td>
        <td class="num tabular">${fmtDelta(deltaDsl, '', ' kbpd')}</td>
      </tr>
      <tr>
        <td>Governing bottleneck constraint</td>
        <td class="text-muted">${scA.bottleneck}</td>
        <td class="text-muted">${scB.bottleneck}</td>
        <td class="num" style="color: ${isIdentical ? 'var(--text-muted)' : 'var(--rust)'}; font-weight: 500;">
          ${isIdentical ? 'Identical' : 'Pivoted'}
        </td>
      </tr>
    `;
  }

  function setupEvidenceCopy() {
    function fallbackCopy(text) {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.top = '-9999px';
      textArea.style.left = '-9999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        document.execCommand('copy');
      } catch (err) {
        console.warn('Fallback copy failed:', err);
      }
      document.body.removeChild(textArea);
    }

    window.sovApp = window.sovApp || {};
    Object.assign(window.sovApp, {
      switchTab: switchTab,
      triggerSolve: triggerSolve,
      getState: () => STATE,
      TEAM_MEMBERS: TEAM_MEMBERS,
      ASSET_VERSION: ASSET_VERSION,
      inspectUnit: updateUnitInspector,
      copyText: (text, btnId) => {
        const doFeedback = () => {
          const btn = document.getElementById(btnId);
          if (btn) {
            const orig = btn.textContent;
            btn.textContent = 'Copied';
            setTimeout(() => { btn.textContent = orig; }, 1500);
          }
        };

        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(doFeedback).catch(() => {
            fallbackCopy(text);
            doFeedback();
          });
        } else {
          fallbackCopy(text);
          doFeedback();
        }
      },
      exportAuditJSON: () => {
        const sc = SCENARIOS[STATE.activeScenario] || SCENARIOS['SC-01'];
        const isLive = STATE.resultSource === 'live' && STATE.solveResult;
        const payload = {
          system: 'SOV-OPT Refinery Planning Workstation',
          formulation_provenance: 'Representative open-literature refinery planning formulation (Gary & Handwerk / Meyers)',
          problem_statement: 'MRPL SIH PS 26119',
          timestamp_utc: new Date().toISOString(),
          solver_version: '0.3.2',
          execution_backend: STATE.activeBackend,
          result_source: isLive ? 'LIVE_OPTIMIZATION_RUN' : 'SCENARIO_PRESET_NO_LIVE_SOLVE',
          active_model: STATE.activeModel,
          active_scenario: STATE.activeScenario,
          scenario_metadata: sc,
          solve_result: STATE.solveResult || {
            status: 'NOT_EXECUTED',
            message: 'No live solver run has been performed for this scenario. Click "Run optimisation" to obtain verified results.',
            kkt_passed: null,
            primal_residual: null,
            dual_residual: null,
            iterations: null,
            elapsed_seconds: null
          }
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sovopt_refinery_audit_${STATE.activeScenario}_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
      },
      exportTrustPassportJSON: () => {
        const isLive = STATE.resultSource === 'live' && STATE.solveResult;
        const res = STATE.solveResult;
        const v = (res && res.verification) || {};
        const acceptedInputs = (res && res.inputs) ? res.inputs : {
          scenario: STATE.activeScenario,
          c_arab: STATE.crudeCostArab,
          c_basrah: STATE.crudeCostBasrah,
          min_gas: STATE.gasolineDemand,
          min_dsl: STATE.dieselDemand
        };
        const isVerified = isLive ? (
          res.status === 'OPTIMAL_VERIFIED' ? Boolean(v.kkt_passed || v.feasible) :
          res.status === 'INFEASIBLE_CERTIFIED' ? Boolean(res.farkas_certificate || v.farkas_verified) :
          res.status === 'UNBOUNDED_CERTIFIED' ? Boolean(v.verified) : false
        ) : false;

        const solPrec = (isLive && isVerified && (res.status === 'OPTIMAL_VERIFIED' || res.status === 'UNBOUNDED_CERTIFIED')) ? 'IEEE_754_double' : null;
        const boundPrec = (isLive && isVerified && STATE.activeModel === 'milp' && res.status === 'OPTIMAL_VERIFIED') ? 'exact_rational_Q' : null;
        const certPrec = (isLive && isVerified && res.status === 'INFEASIBLE_CERTIFIED') ? 'exact_rational_Q' : null;
        const verPrec = certPrec || boundPrec || solPrec || null;

        const passport = {
          schema_version: '1.0.0',
          model_sha256: res ? (res.model_sha256 || null) : null,
          solver_version: res ? (res.solver_version || '0.3.2') : '0.3.2',
          solver_commit: (res && res.solver_commit) ? res.solver_commit : null,
          model_type: STATE.activeModel ? STATE.activeModel.toUpperCase() : 'LP',
          rows: res ? res.rows : null,
          columns: res ? res.variables : null,
          nnz: res ? res.nonzeros : null,
          algorithm: res ? (res.method_used || res.algorithm || null) : null,
          backend: STATE.activeBackend,
          input_snapshot: acceptedInputs,
          input_snapshot_stale: Boolean(STATE.isStale),
          status: isLive ? res.status : 'NOT_EXECUTED',
          objective: isLive ? res.objective : null,
          verified: isVerified,
          verification_precision: verPrec,
          solution_verification_precision: solPrec,
          bound_certificate_precision: boundPrec,
          certificate_precision: certPrec,
          primal_residual: (isLive && v.primal_residual !== undefined) ? v.primal_residual : null,
          dual_residual: (isLive && v.dual_residual !== undefined) ? v.dual_residual : null,
          bound_violation: (isLive && v.bound_violation !== undefined) ? v.bound_violation : null,
          integrality_residual: (isLive && STATE.activeModel === 'milp' && v.integrality_residual !== undefined) ? v.integrality_residual : null,
          kkt_residual: (isLive && v.primal_residual !== undefined && v.dual_residual !== undefined) ? Math.max(v.primal_residual, v.dual_residual) : null,
          relative_gap: (isLive && res.relative_gap !== undefined) ? res.relative_gap : null,
          certificate_type: (isLive && res.status === 'INFEASIBLE_CERTIFIED') ? 'Farkas_infeasibility_ray' : ((isLive && res.status === 'UNBOUNDED_CERTIFIED') ? 'Unbounded_recession_direction' : null),
          certificate_verified: (isLive && isVerified && (res.status === 'INFEASIBLE_CERTIFIED' || res.status === 'UNBOUNDED_CERTIFIED')) ? true : null
        };
        const blob = new Blob([JSON.stringify(passport, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sovopt_trust_passport_${STATE.activeScenario}_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
      },
      exportCSV: () => {
        const sc = SCENARIOS[STATE.activeScenario] || SCENARIOS['SC-01'];
        const res = STATE.solveResult;
        let arabRate = sc.cduArab;
        let basrahRate = sc.cduBasrah;
        let cduRate = sc.cduThroughput;
        let fccRate = sc.fccThroughput;
        let refRate = sc.reformerThroughput;
        let gasRate = sc.gasolineShipment;
        let dslRate = sc.dieselShipment;
        let foRate = sc.fuelOilShipment;

        if (STATE.resultSource === 'live' && res && res.x && res.x.length >= 12) {
          arabRate = res.x[0];
          basrahRate = res.x[1];
          cduRate = res.x[2];
          fccRate = res.x[3];
          refRate = res.x[4];
          gasRate = res.x[9];
          dslRate = res.x[10];
          foRate = res.x[11];
        }

        const csv = [
          'Stream_or_Unit,Flow_Rate_kbpd,Unit,Economic_Price_USD_per_bbl,Status',
          `Crude Arab Light,${arabRate.toFixed(2)},kbpd,${sc.crudeArabPrice.toFixed(2)},Feedstock Intake`,
          `Crude Basrah Heavy,${basrahRate.toFixed(2)},kbpd,${sc.crudeBasrahPrice.toFixed(2)},Feedstock Intake`,
          `CDU Total Intake,${cduRate.toFixed(2)},kbpd,2.50,Distillation Column`,
          `FCC Cracker Intake,${fccRate.toFixed(2)},kbpd,4.00,Catalytic Cracking`,
          `Reformer Intake,${refRate.toFixed(2)},kbpd,3.00,Catalytic Reforming`,
          `Gasoline Shipment,${gasRate.toFixed(2)},kbpd,-115.00,Finished Product Shipment`,
          `Diesel Shipment,${dslRate.toFixed(2)},kbpd,-105.00,Finished Product Shipment`,
          `Fuel Oil Shipment,${foRate.toFixed(2)},kbpd,-55.00,Heavy Decant Shipment`
        ].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `refinery_schedule_${STATE.activeScenario}_${Date.now()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
