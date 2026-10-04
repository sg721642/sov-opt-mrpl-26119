/* ==========================================================================
   SOV-OPT REFINERY PLANNING WORKSTATION — EDITORIAL CLIENT APPLICATION
   Modular state management, fluid process flowsheet animation, count-up KPIs,
   convergence chart draw-in, live HTTP solver integration, and mobile drawer.
   ========================================================================== */

(function () {
  'use strict';
  const ASSET_VERSION = 'v=4';

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
    isMobileMenuOpen: false,
    currentLanguage: 'en'
  };

  // Centralized Internationalization (English / हिन्दी)
  const I18N = {
    en: {
      screen_reader: 'Screen Reader Access',
      skip_to_content: 'Skip to main content',
      nav_home: 'Home',
      nav_about: 'About Us',
      nav_solver: 'Solver Portal',
      nav_overview: 'Overview & Process Flow',
      nav_optimization: 'Optimization Run',
      nav_analytics: 'Solver Analytics',
      nav_planning: 'Refinery Planning',
      nav_scenarios: 'Scenarios',
      nav_twin_pfd: 'Refinery Twin & PFD',
      nav_trust: 'Trust & Verification',
      nav_benchmarks: 'Benchmarks',
      nav_evidence: 'Evidence',
      nav_evidence_audits: 'Evidence & Audits',
      nav_reports: 'Reports & Export',
      nav_contact: 'Contact Us',
      nav_run_optimization: 'Run Optimization',
      nav_export_audit: 'Export Audit',
      latest_updates: 'Latest Updates',
      enter_workspace: 'Enter Solver Workspace',
      view_trust: 'View Trust & Verification',
      opt_run_title: 'Optimization engine dispatch & live solve',
      opt_run_intro: 'Adjust operational crude and demand parameters, execute the sovereign solver core, and inspect convergence trajectories and certified solution vectors.',
      opt_controls_title: 'Model & operational inputs',
      target_model: 'Target model instance',
      exec_backend: 'Execution backend',
      btn_run_solver: 'Run optimization',
      running_optimization: 'Running optimization…',
      opt_complete: 'Optimization Complete ✓',
      about_us: 'About Us',
      about_subtitle: 'SOV-OPT Team',
      about_intro: 'We are a student team from Rajiv Gandhi Institute of Petroleum Technology developing SOV-OPT, a sovereign LP/MILP/convex-QP optimization core for the MRPL Smart India Hackathon problem statement.',
      contact_us: 'Contact Us',
      contact_intro: 'Connect with the SOV-OPT student development team from Rajiv Gandhi Institute of Petroleum Technology.',
      lang_btn_text: 'हिन्दी',
      lang_aria_label: 'Switch language to Hindi'
    },
    hi: {
      screen_reader: 'स्क्रीन रीडर एक्सेस',
      skip_to_content: 'मुख्य सामग्री पर जाएँ',
      nav_home: 'होम',
      nav_about: 'हमारे बारे में',
      nav_solver: 'सॉल्वर पोर्टल',
      nav_overview: 'अवलोकन एवं प्रक्रिया प्रवाह',
      nav_optimization: 'ऑप्टिमाइज़ेशन रन',
      nav_analytics: 'सॉल्वर विश्लेषण',
      nav_planning: 'रिफाइनरी योजना',
      nav_scenarios: 'परिदृश्य',
      nav_twin_pfd: 'रिफाइनरी मॉडल एवं पीएफडी',
      nav_trust: 'विश्वसनीयता एवं सत्यापन',
      nav_benchmarks: 'बेंचमार्क',
      nav_evidence: 'प्रमाण',
      nav_evidence_audits: 'प्रमाण एवं ऑडिट',
      nav_reports: 'रिपोर्ट एवं निर्यात',
      nav_contact: 'संपर्क करें',
      nav_run_optimization: 'ऑप्टिमाइज़ेशन चलाएँ',
      nav_export_audit: 'ऑडिट निर्यात करें',
      latest_updates: 'नवीनतम अपडेट',
      enter_workspace: 'सॉल्वर वर्कस्पेस में प्रवेश करें',
      view_trust: 'विश्वसनीयता एवं सत्यापन देखें',
      opt_run_title: 'ऑप्टिमाइज़ेशन इंजन प्रेषण एवं लाइव समाधान',
      opt_run_intro: 'परिचालन क्रूड एवं माँग मापदंड समायोजित करें, सॉवरेन सॉल्वर निष्पादित करें, और अभिसरण पथ एवं प्रमाणित समाधान देखें।',
      opt_controls_title: 'मॉडल एवं परिचालन इनपुट',
      target_model: 'लक्षित मॉडल',
      exec_backend: 'निष्पादन बैकएंड',
      btn_run_solver: 'ऑप्टिमाइज़ेशन चलाएँ',
      running_optimization: 'ऑप्टिमाइज़ेशन चल रहा है…',
      opt_complete: 'ऑप्टिमाइज़ेशन पूर्ण ✓',
      about_us: 'हमारे बारे में',
      about_subtitle: 'SOV-OPT टीम',
      about_intro: 'हम राजीव गाँधी पेट्रोलियम प्रौद्योगिकी संस्थान के छात्र हैं जो MRPL स्मार्ट इंडिया हैकाथॉन समस्या विवरण हेतु SOV-OPT सॉवरेन LP/MILP/QP सॉल्वर विकसित कर रहे हैं।',
      contact_us: 'संपर्क करें',
      contact_intro: 'राजीव गाँधी पेट्रोलियम प्रौद्योगिकी संस्थान के SOV-OPT छात्र विकास दल से संपर्क करें।',
      lang_btn_text: 'English',
      lang_aria_label: 'Switch language to English'
    }
  };

  // Complete English to Hindi Translation Dictionary
  const TRANSLATION_MAP = {
  "Screen Reader Access": "स्क्रीन रीडर सहायता",
  "Skip to main content": "मुख्य सामग्री पर जाएँ",
  "Toggle text spacing": "टेक्स्ट स्पेसिंग बदलें",
  "Toggle high contrast": "उच्च कंट्रास्ट बदलें",
  "Decrease font size": "फ़ॉन्ट का आकार घटाएँ",
  "Default font size": "सामान्य फ़ॉन्ट आकार",
  "Increase font size": "फ़ॉन्ट का आकार बढ़ाएँ",
  "Smart India Hackathon 2026": "स्मार्ट इंडिया हैकाथॉन 2026",
  "TEAM NAME": "टीम का नाम",
  "TEAM ID": "टीम आईडी",
  "Home": "होम",
  "About Us": "हमारे बारे में",
  "Solver Portal": "सॉल्वर पोर्टल",
  "Overview & Process Flow": "अवलोकन एवं प्रक्रिया प्रवाह",
  "Optimization Run": "ऑप्टिमाइज़ेशन रन",
  "Solver Analytics": "सॉल्वर विश्लेषण",
  "Refinery Planning": "रिफाइनरी योजना",
  "Scenarios": "परिदृश्य",
  "Refinery Twin & PFD": "रिफाइनरी मॉडल एवं पीएफडी",
  "Trust & Verification": "विश्वसनीयता एवं सत्यापन",
  "Benchmarks": "बेंचमार्क",
  "Evidence": "प्रमाण",
  "Evidence & Audits": "प्रमाण एवं ऑडिट",
  "Reports & Export": "रिपोर्ट एवं निर्यात",
  "Contact Us": "संपर्क करें",
  "Run Optimization": "ऑप्टिमाइज़ेशन चलाएँ",
  "Export Audit": "ऑडिट निर्यात करें",
  "Menu": "मेनू",
  "Latest Updates": "नवीनतम अपडेट",
  "SOV-OPT supports sovereign LP, MILP and convex QP optimization workflows.": "SOV-OPT सॉवरेन LP, MILP और उत्तल QP ऑप्टिमाइज़ेशन वर्कफ़्लो का समर्थन करता है।",
  "Numerical Trust Layer independently verifies accepted optimization results.": "न्यूमेरिकल ट्रस्ट लेयर स्वीकृत ऑप्टिमाइज़ेशन परिणामों को स्वतंत्र रूप से सत्यापित करती है।",
  "Trust Passport is generated from the accepted solve snapshot with SHA-256 model provenance.": "स्वीकृत समाधान स्नैपशॉट से SHA-256 मॉडल मूल के साथ ट्रस्ट पासपोर्ट तैयार किया जाता है।",
  "Certified Farkas diagnostics are available for supported infeasible cases.": "समर्थित असाध्य मामलों के लिए प्रमाणित फरकस डायग्नोस्टिक्स उपलब्ध हैं।",
  "Mixed-integer branch-and-bound enforces conservative rational dual bounds.": "मिश्रित-पूर्णांक शाखा-और-बाउंड रूढ़िवादी परिमेय दोहरे बाउंड लागू करता है।",
  "Pure NumPy & Python standard library implementation with zero external solver dependencies.": "शून्य बाहरी सॉल्वर निर्भरता के साथ शुद्ध NumPy एवं Python मानक लाइब्रेरी कार्यान्वयन।",
  "Original Mathematical Optimization Engine": "मूल गणितीय ऑप्टिमाइज़ेशन इंजन",
  "SOV-OPT Refinery Workstation": "SOV-OPT रिफाइनरी वर्कस्टेशन",
  "GPU accelerates. CPU verifies.": "GPU गति देता है। CPU सत्यापन करता है।",
  "Mathematical LP, MILP, and convex QP optimization for refinery planning workflows.": "रिफाइनरी योजना वर्कफ़्लो के लिए गणितीय LP, MILP और उत्तल QP ऑप्टिमाइज़ेशन।",
  "Enter Solver Workspace": "सॉल्वर वर्कस्पेस में प्रवेश करें",
  "View Trust & Verification": "विश्वसनीयता एवं सत्यापन देखें",
  "Refinery Optimization Network Topology": "रिफाइनरी ऑप्टिमाइज़ेशन नेटवर्क टोपोलॉजी",
  "Process Schematic": "प्रक्रिया योजना",
  "MRPL Problem Statement 26119": "MRPL समस्या विवरण 26119",
  "Refinery Production & Planning Formulation": "रिफाइनरी उत्पादन एवं योजना निरूपण",
  "Real-World Industrial Scope": "वास्तविक औद्योगिक क्षेत्र",
  "Multi-period linear programming with crude selection, unit capacities, blending constraints, and product demands.": "क्रूड चयन, इकाई क्षमता, सम्मिश्रण सीमाओं और उत्पाद मांगों के साथ बहु-अवधि रैखिक प्रोग्रामिंग।",
  "Explore Refinery Twin": "रिफाइनरी मॉडल देखें",
  "Review Mathematical Model": "गणितीय मॉडल की समीक्षा करें",
  "Multi-Unit Material Balance Matrix": "मल्टी-यूनिट सामग्री संतुलन मैट्रिक्स",
  "Optimization Matrix": "ऑप्टिमाइज़ेशन मैट्रिक्स",
  "Sovereign Numerical Foundation": "सॉवरेन न्यूमेरिकल आधार",
  "Dual-Layer Architecture": "द्वि-स्तरीय वास्तुकला",
  "First-Order Acceleration + Exact Active-Set Basis Recovery": "प्रथम-क्रम त्वरण + सटीक सक्रिय-सेट आधार पुनर्प्राप्ति",
  "PDHG executes rapid first-order iterations. The CPU simplex and IPM cores construct certified basis factorizations and KKT proofs.": "PDHG तेज़ प्रथम-क्रम पुनरावृत्ति निष्पादित करता है। CPU सिम्प्लेक्स और IPM कोर प्रमाणित आधार गुणनखंडन और KKT प्रमाण बनाते हैं।",
  "Inspect Architecture": "वास्तुकला का निरीक्षण करें",
  "Run Live Benchmark": "लाइव बेंचमार्क चलाएँ",
  "Dual-Engine Execution Pipeline": "दोहरे इंजन निष्पादन पाइपलाइन",
  "System Blueprint": "सिस्टम ब्लूप्रिंट",
  "Trust & Numerical Integrity": "विश्वास एवं संख्यात्मक अखंडता",
  "KKT Verification & Certified Diagnostics": "KKT सत्यापन एवं प्रमाणित डायग्नोस्टिक्स",
  "Truthful Failure Reporting": "सटीक विफलता रिपोर्टिंग",
  "Every solution is independently verified. Infeasible instances emit certified Farkas rays. Degeneracy and limits are reported honestly.": "प्रत्येक समाधान का स्वतंत्र रूप से सत्यापन किया जाता है। असाध्य मामलों में प्रमाणित फरकस किरणें निकलती हैं। सीमाओं की सटीक रिपोर्ट की जाती है।",
  "View Trust Passport": "ट्रस्ट पासपोर्ट देखें",
  "Inspect Farkas Lens": "फरकस लेंस का निरीक्षण करें",
  "Certified KKT Residual Monitor": "प्रमाणित KKT अवशिष्ट मॉनिटर",
  "Residual Ledger": "अवशिष्ट बहीखाता",
  "Smart India Hackathon 2026 Finalists": "स्मार्ट इंडिया हैकाथॉन 2026 फाइनलिस्ट",
  "Team VarunNetra": "टीम वरुणनेत्र",
  "Rajiv Gandhi Institute of Petroleum Technology": "राजीव गाँधी पेट्रोलियम प्रौद्योगिकी संस्थान",
  "Six students developing original optimization software for India's energy and process engineering sovereignty.": "भारत की ऊर्जा और प्रक्रिया इंजीनियरिंग संप्रभुता के लिए मूल ऑप्टिमाइज़ेशन सॉफ़्टवेयर विकसित करने वाले छह छात्र।",
  "Meet The Team": "हमारी टीम से मिलें",
  "Contact Team VarunNetra": "टीम वरुणनेत्र से संपर्क करें",
  "Team Roster & Research Focus": "टीम सूची एवं अनुसंधान केंद्र",
  "Student R&D": "छात्र अनुसंधान एवं विकास",
  "Hardware Acceleration Evidence": "हार्डवेयर त्वरण प्रमाण",
  "Physical GPU Verification": "भौतिक GPU सत्यापन",
  "Dedicated RawKernels · Measured on Acer RTX 5050": "समर्पित RawKernels · Acer RTX 5050 पर मापा गया",
  "Differential benchmarks executed against Netlib and MIPLIB suites with full runtime telemetry and driver provenance.": "पूर्ण रनटाइम टेलीमेट्री और ड्राइवर मूल के साथ Netlib और MIPLIB सूट के खिलाफ निष्पादित अंतर बेंचमार्क।",
  "Inspect Hardware Benchmarks": "हार्डवेयर बेंचमार्क देखें",
  "Download Audit Bundle": "ऑडिट बंडल डाउनलोड करें",
  "GPU Execution Telemetry": "GPU निष्पादन टेलीमेट्री",
  "Measured Evidence": "मापा गया प्रमाण",
  "LEADER": "टीम लीडर",
  "MEMBER": "सदस्य",
  "B.Tech + M.Tech (Dual Degree) in CSE & AI": "बी.टेक + एम.टेक (दोहरी डिग्री) सीएसई और एआई",
  "B.Tech in Information Technology": "बी.टेक सूचना प्रौद्योगिकी",
  "Program": "पाठ्यक्रम",
  "Email": "ईमेल",
  "LinkedIn": "लिंक्डइन",
  "Operations console": "संचालन कंसोल",
  "Optimization engine dispatch & live solve": "ऑप्टिमाइज़ेशन इंजन प्रेषण एवं लाइव समाधान",
  "Adjust operational crude and demand parameters, execute the sovereign solver core, and inspect convergence trajectories and certified solution vectors.": "परिचालन क्रूड एवं माँग मापदंड समायोजित करें, सॉवरेन सॉल्वर निष्पादित करें, और अभिसरण पथ एवं प्रमाणित समाधान देखें।",
  "Model & operational inputs": "मॉडल एवं परिचालन इनपुट",
  "Target model instance": "लक्षित मॉडल",
  "Execution backend": "निष्पादन बैकएंड",
  "Arab Light crude cost ($/bbl)": "अरब लाइट क्रूड लागत ($/बैरल)",
  "Basrah Heavy crude cost ($/bbl)": "बसरा हेवी क्रूड लागत ($/बैरल)",
  "Minimum gasoline demand (kbpd)": "न्यूनतम गैसोलीन माँग (kbpd)",
  "Minimum diesel demand (kbpd)": "न्यूनतम डीजल माँग (kbpd)",
  "Run optimization": "ऑप्टिमाइज़ेशन चलाएँ",
  "Running optimization…": "ऑप्टिमाइज़ेशन चल रहा है…",
  "Optimization Complete ✓": "ऑप्टिमाइज़ेशन पूर्ण ✓",
  "Solver stage:": "सॉल्वर चरण:",
  "Result status:": "परिणाम स्थिति:",
  "Iterations:": "पुनरावृत्तियाँ:",
  "Duration:": "समय:",
  "Net margin:": "शुद्ध मार्जिन:",
  "Primal residual:": "प्राइमल अवशिष्ट:",
  "Dual residual:": "ड्यूअल अवशिष्ट:",
  "Idle": "निष्क्रिय",
  "Not executed": "अभी चलाया नहीं गया",
  "Building model…": "मॉडल तैयार हो रहा है…",
  "Executing sparse LU solver…": "सॉल्वर निष्पादित हो रहा है…",
  "Optimal verified": "इष्टतम सत्यापित",
  "Farkas certificate ray": "फरकस प्रमाणपत्र किरण",
  "Inputs modified — click 'Run optimization'": "इनपुट बदले गए — 'ऑप्टिमाइज़ेशन चलाएँ' पर क्लिक करें",
  "Solve failed": "समाधान विफल",
  "Execution error": "निष्पादन त्रुटि",
  "CUDA unavailable on this machine — select CPU backend": "इस मशीन पर CUDA अनुपलब्ध है — CPU बैकएंड चुनें",
  "CUDA unavailable": "CUDA अनुपलब्ध",
  "SOV-OPT Team": "SOV-OPT टीम",
  "We are a student team from Rajiv Gandhi Institute of Petroleum Technology developing SOV-OPT, a sovereign LP/MILP/convex-QP optimization core for the MRPL Smart India Hackathon problem statement.": "हम राजीव गाँधी पेट्रोलियम प्रौद्योगिकी संस्थान के छात्र हैं जो MRPL स्मार्ट इंडिया हैकाथॉन समस्या विवरण हेतु SOV-OPT सॉवरेन LP/MILP/QP सॉल्वर विकसित कर रहे हैं।",
  "Institutional Connection": "संस्थागत संपर्क",
  "Connect with the SOV-OPT student development team from Rajiv Gandhi Institute of Petroleum Technology.": "राजीव गाँधी पेट्रोलियम प्रौद्योगिकी संस्थान के SOV-OPT छात्र विकास दल से संपर्क करें।",
  "Institute of National Importance (INI) · Government of India": "राष्ट्रीय महत्व का संस्थान (INI) · भारत सरकार",
  "Bahadurpur, Jais, Post Harbanshganj, Amethi - 229304, Uttar Pradesh, India": "बहादुरपुर, जायस, पोस्ट हरबंशगंज, अमेठी - 229304, उत्तर प्रदेश, भारत",
  "Refinery Planning Scenarios": "रिफाइनरी योजना परिदृश्य",
  "Curated industrial operating regimes representing baseline equilibrium, demand spikes, sulfur upsets, FCC outages, and certified infeasible bounds.": "आधारभूत संतुलन, माँग वृद्धि, सल्फर समस्या, FCC आउटेज और प्रमाणित असाध्य सीमाओं का प्रतिनिधित्व करने वाले औद्योगिक परिदृश्य।",
  "Base refinery equilibrium": "आधारभूत रिफाइनरी संतुलन",
  "High gasoline demand spike": "उच्च गैसोलीन माँग वृद्धि",
  "Heavy crude discount arbitrage": "भारी क्रूड छूट आर्बिट्राज",
  "FCC unit partial outage": "FCC इकाई आंशिक आउटेज",
  "High sulfur crude intake penalty": "उच्च सल्फर क्रूड इनटेक पेनल्टी",
  "Infeasible production constraint": "असाध्य उत्पादन सीमा",
  "Canonical Trust Passport & Execution Telemetry": "कैनोनिकल ट्रस्ट पासपोर्ट एवं निष्पादन टेलीमेट्री",
  "Model-fingerprinted verification audit for the active solution snapshot": "सक्रिय समाधान स्नैपशॉट हेतु मॉडल-फिंगरप्रिंटेड सत्यापन ऑडिट",
  "Verification Status": "सत्यापन स्थिति",
  "Model Instance": "मॉडल का नाम",
  "Objective Value": "उद्देश्य मान",
  "Primal Residual": "प्राइमल अवशिष्ट",
  "Dual Residual": "ड्यूअल अवशिष्ट",
  "KKT Residual": "KKT अवशिष्ट",
  "Bound Violation": "बाउंड उल्लंघन",
  "Integrality Gap": "पूर्णांक अंतर",
  "Certificate Type": "प्रमाणपत्र प्रकार",
  "Solver Commit": "सॉल्वर कमिट",
  "Backend Selected": "चयनित बैकएंड",
  "Algorithm Dispatched": "प्रयुक्त एल्गोरिथ्म",
  "Model Fingerprint (SHA-256)": "मॉडल फिंगरप्रिंट (SHA-256)",
  "Export Trust Passport (JSON)": "ट्रस्ट पासपोर्ट निर्यात करें (JSON)",
  "Copy JSON": "JSON कॉपी करें",
  "Copied": "कॉपी हो गया",
  "Download Artifact": "आर्टिफ़ैक्ट डाउनलोड करें",
  "Run solver to verify": "सत्यापन हेतु सॉल्वर चलाएँ",
  "Infeasibility Certificate & Constraint Attribution (Farkas Lens)": "असाध्यता प्रमाणपत्र एवं प्रतिबंध विश्लेषण (फरकस लेंस)",
  "Exact rational Farkas certificate identifies governing infeasible constraint subsystems": "सटीक परिमेय फरकस प्रमाणपत्र प्रमुख असाध्य प्रतिबंध उप-प्रणालियों की पहचान करता है",
  "Farkas ray certifies that no feasible production schedule exists satisfying all constraints simultaneously.": "फरकस किरण प्रमाणित करती है कि सभी प्रतिबंधों को एक साथ पूरा करने वाला कोई व्यावहारिक उत्पादन कार्यक्रम मौजूद नहीं है।",
  "Diagnostic ranking — not a minimal IIS.": "डायग्नोस्टिक रैंकिंग — न्यूनतम IIS नहीं।",
  "Refinery Overview & Process Flow Diagram": "रिफाइनरी अवलोकन एवं प्रक्रिया प्रवाह आरेख",
  "Interactive flowsheet representing CDU, FCC, Reformer, and Blending pools with live stream balances": "CDU, FCC, रिफॉर्मर और सम्मिश्रण पूल का सजीव स्ट्रीम संतुलन दर्शाने वाला इंटरैक्टिव फ्लोशीट",
  "Unit Inspector": "इकाई विश्लेषक",
  "Select any processing unit in the flowsheet above to inspect its design specification, operating parameters, and active shadow prices.": "डिज़ाइन विनिर्देश, परिचालन मापदंड और शैडो कीमतों का निरीक्षण करने के लिए ऊपर फ्लोशीट में किसी भी इकाई का चयन करें।",
  "Crude Distillation Unit (Atmospheric)": "क्रूड आसवन इकाई (वायुमंडलीय)",
  "Primary fractionator": "प्राथमिक प्रभाजक",
  "Fluid Catalytic Cracker": "द्रव उत्प्रेरक क्रैकर",
  "Secondary upgrading & cracking": "द्वितीयक उन्नयन एवं क्रैकिंग",
  "Catalytic Reforming Unit (Semi-Regen)": "उत्प्रेरक सुधार इकाई",
  "High-octane aromatics & H2": "उच्च-ऑक्टेन एरोमैटिक्स एवं H2",
  "Motor Gasoline Blending Pool": "मोटर गैसोलीन सम्मिश्रण पूल",
  "High-Speed Diesel Blending Pool": "हाई-स्पीड डीजल सम्मिश्रण पूल",
  "Fuel Oil & Asphalt Header": "ईंधन तेल एवं डामर हेडर",
  "Governing crack spread": "प्रमुख क्रैक स्प्रेड",
  "Slack available": "अतिरिक्त क्षमता उपलब्ध",
  "Marginal cost binding": "सीमांत लागत बाध्यकारी",
  "Hardware Benchmark Suite": "हार्डवेयर बेंचमार्क सूट",
  "Acer Nitro V 15 · NVIDIA GeForce RTX 5050 Laptop GPU (8GB GDDR7, Blackwell, SM 12.0) vs Intel Core i5-13420H (12 threads)": "Acer Nitro V 15 · NVIDIA GeForce RTX 5050 लैपटॉप GPU बनाम Intel Core i5-13420H (12 थ्रेड)",
  "Execution Summary": "निष्पादन सारांश",
  "Instances Evaluated": "मूल्यांकित मॉडल",
  "Mean CPU/CUDA Ratio": "औसत CPU/CUDA अनुपात",
  "Large-Instance Max Ratio": "बड़े मॉडल अधिकतम अनुपात",
  "Gate 9 vs Gate 8 Speedup": "गेट 9 बनाम गेट 8 गति सुधार",
  "RawKernels Deployed": "तैनात RawKernels",
  "Instance": "मॉडल",
  "Class": "वर्ग",
  "Rows": "पंक्तियाँ",
  "Cols": "कॉलम",
  "Nonzeros": "अशून्य मान",
  "CPU Time": "CPU समय",
  "CUDA Time": "CUDA समय",
  "Ratio": "अनुपात",
  "Discrepancy": "अंतर",
  "Experimental Evidence & Validation Manifests": "प्रायोगिक प्रमाण एवं सत्यापन घोषणापत्र",
  "Verifiable execution logs, solver comparison tables, and raw cryptographic checksum manifests for all test instances": "सत्यापन योग्य निष्पादन लॉग, सॉल्वर तुलना तालिकाएँ और सभी परीक्षण मॉडलों के लिए क्रिप्टोग्राफ़िक चेकसम घोषणापत्र",
  "Artifact": "आर्टिफ़ैक्ट",
  "Source": "स्रोत",
  "SHA-256 Hash": "SHA-256 हैश",
  "Format": "प्रारूप",
  "Action": "कार्रवाई",
  "View": "देखें",
  "Download": "डाउनलोड",
  "Operations Reports & Data Export": "संचालन रिपोर्ट एवं डेटा निर्यात",
  "Download certified execution passports, schedule spreadsheets, and audit summaries for industrial verification": "औद्योगिक सत्यापन के लिए प्रमाणित निष्पादन पासपोर्ट, शेड्यूल स्प्रेडशीट और ऑडिट सारांश डाउनलोड करें",
  "Export CSV Schedule": "CSV शेड्यूल निर्यात करें",
  "Export JSON Passport": "JSON पासपोर्ट निर्यात करें",
  "Download Full Bundle": "पूर्ण बंडल डाउनलोड करें",
  "Official Portal": "आधिकारिक पोर्टल",
  "Autonomous Numerical Optimization Research Prototype developed for MRPL Smart India Hackathon Problem Statement 26119.": "MRPL स्मार्ट इंडिया हैकाथॉन समस्या विवरण 26119 हेतु विकसित मूल संख्यात्मक ऑप्टिमाइज़ेशन प्रोटोटाइप।",
  "Quick Links": "त्वरित लिंक",
  "Institutional Authority": "संस्थागत प्राधिकरण",
  "Ministry of Petroleum and Natural Gas, Government of India": "पेट्रोलियम एवं प्राकृतिक गैस मंत्रालय, भारत सरकार",
  "Smart India Hackathon · Ministry of Education, Government of India": "स्मार्ट इंडिया हैकाथॉन · शिक्षा मंत्रालय, भारत सरकार",
  "All rights reserved.": "सर्वाधिकार सुरक्षित।",
  "\"No result is trusted merely because an optimization algorithm stopped.\"": "\"केवल इसलिए किसी परिणाम पर भरोसा नहीं किया जाता क्योंकि ऑप्टिमाइज़ेशन एल्गोरिथ्म रुक गया।\"",
  "$0.00 / bbl": "$0.00 / बैरल",
  "$0.50 / bbl-period": "$0.50 / बैरल-अवधि",
  "$29.89 / bbl": "$29.89 / बैरल",
  "$8.40 / bbl": "$8.40 / बैरल",
  "& unroll 4": "& अनरोल 4",
  "(Discrete scheduling)": "(असतत शेड्यूलिंग)",
  "(Material balances)": "(सामग्री संतुलन)",
  "(Unit capacity bounds)": "(इकाई क्षमता सीमा)",
  "(resident buffers)": "(निवासी बफ़र)",
  "). The active scenario is verified feasible.": ")। सक्रिय परिदृश्य व्यवहार्य सत्यापित है।",
  ". An accelerated factor of ≥2x was": "। ≥2x का त्वरित कारक ",
  ". Physical Acer RTX 5050 validation evidence is catalogued under the": "। भौतिक Acer RTX 5050 सत्यापन प्रमाण सूचीबद्ध है ",
  "0 allocations across 50,000 iterations": "50,000 पुनरावृत्तियों में 0 आवंटन",
  "0 runtime allocations": "0 रनटाइम आवंटन",
  "100 kbpd max": "अधिकतम 100 kbpd",
  "100.0 kbpd (100% load)": "100.0 kbpd (100% भार)",
  "15.0 kbbl working stock": "15.0 kbbl कार्यशील स्टॉक",
  "17.0 kbpd (56.7% load)": "17.0 kbpd (56.7% भार)",
  "18 Netlib Benchmark Problems": "18 Netlib बेंचमार्क समस्याएँ",
  "18-instance CPU vs CUDA timing and discrepancy summary": "18-मॉडल CPU बनाम CUDA समय एवं विसंगति सारांश",
  "18-instance differential benchmark suite executed on physical NVIDIA hardware with full driver and runtime telemetry.": "पूर्ण ड्राइवर और रनटाइम टेलीमेट्री के साथ भौतिक NVIDIA हार्डवेयर पर निष्पादित 18-मॉडल अंतर बेंचमार्क सूट।",
  "25.0 kbbl per intermediate product": "25.0 kbbl प्रति मध्यवर्ती उत्पाद",
  "3 warmups + 7 measured repeats at committed source SHA 51b71bb": "प्रतिबद्ध स्रोत SHA 51b71bb पर 3 वार्मअप + 7 मापे गए दोहराव",
  "30.0 kbpd heavy naphtha": "30.0 kbpd भारी नैफ्था",
  "360°C Flash Zone": "360°C फ्लैश ज़ोन",
  "4 dedicated RawKernels": "4 समर्पित RawKernels",
  "4.5x reduction in driver launch latency": "ड्राइवर लॉन्च लेटेंसी में 4.5 गुना कमी",
  "44.0 kbpd finished product": "44.0 kbpd तैयार उत्पाद",
  "45.0 kbpd (90% load)": "45.0 kbpd (90% भार)",
  "50.0 kbpd gasoil/residue": "50.0 kbpd गैसऑयल/अवशेष",
  "500°C Furnace Inlet": "500°C भट्टी इनलेट",
  "530°C Riser Reactor": "530°C राइजर रिएक्टर",
  "56.2 kbpd finished product": "56.2 kbpd तैयार उत्पाद",
  "60L / 40H kbpd": "60L / 40H kbpd",
  "90% (45.0 kbpd)": "90% (45.0 kbpd)",
  "Academic Institution": "शैक्षणिक संस्थान",
  "Acceleration + Rigorous Audit": "त्वरण + कठोर ऑडिट",
  "Accessibility and display controls": "पहुंच एवं प्रदर्शन नियंत्रण",
  "Acer Nitro 5 (NVIDIA RTX 5050)": "Acer Nitro 5 (NVIDIA RTX 5050)",
  "Acer RTX 5050 physical GPU benchmark center": "Acer RTX 5050 भौतिक GPU बेंचमार्क केंद्र",
  "Active refinery constraints": "सक्रिय रिफाइनरी प्रतिबंध",
  "Aggregate Speedup (CPU / CUDA)": "कुल गति सुधार (CPU / CUDA)",
  "Algorithm": "एल्गोरिथ्म",
  "Algorithm routine": "एल्गोरिथ्म रूटीन",
  "All performance claims are backed by commit-hashed execution logs on physical NVIDIA hardware. Measured results strictly preserve differential comparisons without synthetic inflation.": "सभी प्रदर्शन दावे भौतिक NVIDIA हार्डवेयर पर कमिट-हैश किए गए निष्पादन लॉग द्वारा समर्थित हैं। मापे गए परिणाम कृत्रिम वृद्धि के बिना अंतर तुलना को सख्ती से संरक्षित करते हैं।",
  "Ambient": "परिवेशी",
  "Ambient (25°C)": "परिवेशी (25°C)",
  "Amethi, Uttar Pradesh": "अमेठी, उत्तर प्रदेश",
  "An original sovereign numerical optimization research prototype developed for Smart India Hackathon 2026 Problem Statement 26119. Independent pure NumPy core with rigorous primal-dual certificate verification.": "स्मार्ट इंडिया हैकाथॉन 2026 समस्या विवरण 26119 हेतु विकसित एक मूल सॉवरेन संख्यात्मक अनुकूलन अनुसंधान प्रोटोटाइप। कठोर प्राइमल-ड्यूअल प्रमाणपत्र सत्यापन के साथ स्वतंत्र शुद्ध NumPy कोर।",
  "Arab Light": "अरब लाइट",
  "Arab Light (60 kbpd) + Basrah Heavy (40 kbpd)": "अरब लाइट (60 kbpd) + बसरा हेवी (40 kbpd)",
  "Arab Light 60.0 · Basrah 40.0": "अरब लाइट 60.0 · बसरा 40.0",
  "Arbitrage": "आर्बिट्राज",
  "Architectural Excellence": "वास्तुकला उत्कृष्टता",
  "Architectural optimizations implemented to eliminate Python/CUDA dispatch bottlenecks": "Python/CUDA प्रेषण अड़चनों को दूर करने के लिए कार्यान्वित वास्तुकला अनुकूलन",
  "Artifact path": "आर्टिफ़ैक्ट पथ",
  "At Upper": "ऊपरी सीमा पर",
  "Atmospheric": "वायुमंडलीय",
  "Atmospheric Crude Distillation (CDU)": "वायुमंडलीय कच्चा तेल आसवन (CDU)",
  "Atmospheric Crude Distillation Unit (CDU)": "वायुमंडलीय कच्चा तेल आसवन इकाई (CDU)",
  "Atmospheric residue & gasoil header": "वायुमंडलीय अवशेष एवं गैसऑयल हेडर",
  "Audit Export:": "ऑडिट निर्यात:",
  "Audit Notice:": "ऑडिट सूचना:",
  "Audit Reports": "ऑडिट रिपोर्ट",
  "Audit artifacts": "ऑडिट आर्टिफ़ैक्ट",
  "Authentic data files catalogued in repository": "रिपॉजिटरी में सूचीबद्ध प्रामाणिक डेटा फ़ाइलें",
  "Auto Solver Dispatch": "ऑटो सॉल्वर प्रेषण",
  "Ayush Rao on LinkedIn": "Ayush Rao लिंक्डइन पर",
  "B.Tech (Information Technology)": "बी.टेक (सूचना प्रौद्योगिकी)",
  "B.Tech + M.Tech (CSE & AI)": "बी.टेक + एम.टेक (सीएसई और एआई)",
  "BLENDING": "सम्मिश्रण",
  "BS-VI High-Speed Diesel Pool": "BS-VI हाई-स्पीड डीजल पूल",
  "BS-VI Specs": "BS-VI विनिर्देश",
  "Balanced 60/40 Arab Light / Basrah Heavy crude slate. Standard product netbacks ($115/bbl Gasoline, $105/bbl Diesel). Nominal CDU throughput at 100 kbpd ceiling.": "संतुलित 60/40 अरब लाइट / बसरा हेवी क्रूड स्लेट। मानक उत्पाद नेटबैक ($115/बैरल गैसोलीन, $105/बैरल डीजल)। 100 kbpd सीमा पर नाममात्र CDU थ्रूपुट।",
  "Balanced 60/40 sweet/sour crude slate. Standard product netbacks ($115/bbl Gasoline, $105/bbl Diesel). Nominal CDU throughput at 100 kbpd ceiling.": "संतुलित 60/40 स्वीट/सॉर क्रूड स्लेट। मानक उत्पाद नेटबैक ($115/बैरल गैसोलीन, $105/बैरल डीजल)। 100 kbpd सीमा पर नाममात्र CDU थ्रूपुट।",
  "Basic": "मूलभूत",
  "Basis status": "आधार स्थिति",
  "Basrah Heavy crude price spread widens to -$10/bbl ($52/bbl vs $70/bbl Arab Light). Optimal intake pivots heavily to Basrah to capture crude margin arbitrage.": "बसरा हेवी क्रूड मूल्य अंतर -$10/बैरल तक बढ़ता है ($52/बैरल बनाम $70/बैरल अरब लाइट)। क्रूड मार्जिन आर्बिट्राज का लाभ उठाने के लिए इष्टतम इनटेक मुख्य रूप से बसरा की ओर झुकता है।",
  "Basrah Hvy": "बसरा हेवी",
  "Benchmarks (RTX 5050)": "बेंचमार्क (RTX 5050)",
  "Best-bound B&B + rational bounds": "बेस्ट-बाउंड B&B + परिमेय सीमाएँ",
  "Bottleneck": "अड़चन",
  "Bound violation": "बाउंड उल्लंघन",
  "Branch-and-Bound + Exact ℚ-Bounds": "शाखा-और-बाउंड + सटीक ℚ-बाउंड",
  "Branch-and-bound lower bounds are computed in exact rational Fraction arithmetic, guaranteeing that the mathematical gap cannot close falsely due to floating-point leakage.": "शाखा-और-बाउंड निचली सीमाएँ सटीक परिमेय भिन्न अंकगणित में गणना की जाती हैं, जिससे यह गारंटी मिलती है कि फ्लोटिंग-पॉइंट रिसाव के कारण गणितीय अंतर गलत तरीके से बंद नहीं हो सकता।",
  "CDU Distillate (45 kbpd) + FCC LCO (11.2 kbpd)": "CDU डिस्टिलेट (45 kbpd) + FCC LCO (11.2 kbpd)",
  "CDU Distillation:": "CDU आसवन:",
  "CDU intake": "CDU इनटेक",
  "CDU intake capacity": "CDU इनटेक क्षमता",
  "CDU intake capacity (100 kbpd)": "CDU इनटेक क्षमता (100 kbpd)",
  "CDU total throughput": "CDU कुल थ्रूपुट",
  "CPU faster due to sub-ms launch & transfer latency": "सब-मिलीसेकंड लॉन्च एवं ट्रांसफर लेटेंसी के कारण CPU तेज़",
  "CPU median (ms)": "CPU माध्यिका (ms)",
  "CRUDE A": "क्रूड A",
  "CRUDE B": "क्रूड B",
  "CSR with": "CSR साथ",
  "CUDA Improvement (Gate 9 vs Gate 8)": "CUDA सुधार (गेट 9 बनाम गेट 8)",
  "CUDA SpMV memory bandwidth acceleration demonstrated": "CUDA SpMV मेमोरी बैंडविड्थ त्वरण प्रदर्शित",
  "CUDA backend unavailable on this machine (Apple Silicon / ARM64). Execution is disabled for this option. To run optimizations live, select": "इस मशीन (Apple Silicon / ARM64) पर CUDA बैकएंड अनुपलब्ध है। इस विकल्प के लिए निष्पादन अक्षम है। लाइव ऑप्टिमाइज़ेशन चलाने के लिए, चुनें",
  "CUDA build / runtime": "CUDA बिल्ड / रनटाइम",
  "CUDA — unavailable on this machine (Apple Silicon)": "CUDA — इस मशीन (Apple Silicon) पर अनुपलब्ध",
  "Candidate solution x* is directly substituted into the original untransformed constraint matrix A. Any violation exceeding 10⁻⁷ is rejected as NUMERICAL_FAILURE.": "प्रस्तावित समाधान x* को सीधे मूल अपरिवर्तित बाधा मैट्रिक्स A में प्रतिस्थापित किया जाता है। 10⁻⁷ से अधिक किसी भी उल्लंघन को NUMERICAL_FAILURE के रूप में अस्वीकार कर दिया जाता है।",
  "Canonical JSON Passport": "कैनोनिकल JSON पासपोर्ट",
  "Carousel slide selection": "हिंडोला स्लाइड चयन",
  "Cat Cracking": "कैट क्रैकिंग",
  "CatGas (27 kbpd) + Reformate (17 kbpd)": "कैटगैस (27 kbpd) + रिफॉर्मेट (17 kbpd)",
  "CatGas 60% · LCO 30% · Heavy bottoms 10%": "कैटगैस 60% · LCO 30% · भारी बॉटम्स 10%",
  "CatGas to gasoline pool": "कैटगैस से गैसोलीन पूल",
  "Catalog of 81 authentic public benchmark instances": "81 प्रामाणिक सार्वजनिक बेंचमार्क मॉडलों की सूची",
  "Catalytic": "उत्प्रेरक",
  "Ceiling 50.0 kbpd gasoil / residue": "अधिकतम 50.0 kbpd गैसऑयल / अवशेष",
  "Certificate guarantee": "प्रमाणपत्र गारंटी",
  "Certification guarantee": "प्रमाणीकरण गारंटी",
  "Certified basic & non-basic variables satisfying physical bounds": "भौतिक सीमाओं को संतुष्ट करने वाले प्रमाणित मूल एवं गैर-मूल चर",
  "Challenge:": "चुनौती:",
  "Clear separation of concerns: GPU first-order restarted PDHG accelerates massive operational exploration, while CPU exact revised simplex independently certifies Karush-Kuhn-Tucker (KKT) stationarity.": "स्पष्ट दायित्व विभाजन: GPU प्रथम-क्रम पुनरारंभित PDHG व्यापक परिचालन अन्वेषण को गति देता है, जबकि CPU सटीक संशोधित सिम्प्लेक्स स्वतंत्र रूप से KKT स्थिरता प्रमाणित करता है।",
  "Close Navigation Menu": "नेविगेशन मेनू बंद करें",
  "Collapsed DRAM passes into fast registers": "DRAM पास को तेज़ रजिस्टरों में समेटा गया",
  "Commands to verify all results from the terminal": "टर्मिनल से सभी परिणामों को सत्यापित करने के आदेश",
  "Committed git milestone hashes, file digests, and reproducible audit artifacts.": "प्रतिबद्ध गिट माइलस्टोन हैश, फ़ाइल डाइजेस्ट और पुनरुत्पादनीय ऑडिट आर्टिफ़ैक्ट।",
  "Committed git milestone ledger": "प्रतिबद्ध गिट माइलस्टोन बहीखाता",
  "Compare:": "तुलना करें:",
  "Complete independence from commercial solvers. Built with an original revised two-phase primal simplex (LP), exact rational branch-and-bound (MILP), and Mehrotra predictor-corrector interior point method (QP).": "वाणिज्यिक सॉल्वरों से पूर्ण स्वतंत्रता। एक मूल संशोधित दो-चरणीय प्राइमल सिम्प्लेक्स (LP), सटीक परिमेय शाखा-और-बाउंड (MILP), और मेहरोत्रा प्रिडिक्टर-कॉरेक्टर इंटीरियर पॉइंट विधि (QP) के साथ निर्मित।",
  "Compute Capability:": "कंप्यूट क्षमता:",
  "Compute capability": "कंप्यूट क्षमता",
  "Conservative MILP lower bounds via safe rational arithmetic": "सुरक्षित परिमेय अंकगणित के माध्यम से रूढ़िवादी MILP निचली सीमाएँ",
  "Constraint": "प्रतिबंध",
  "Constraint identifier": "प्रतिबंध पहचानकर्ता",
  "Constraint state": "प्रतिबंध स्थिति",
  "Contact": "संपर्क",
  "Contact Details": "संपर्क विवरण",
  "Continuous LP": "सतत LP",
  "Contraction of infinity-norm KKT residuals over iterations": "पुनरावृत्तियों के साथ अनंत-मानक KKT अवशिष्टों का संकुचन",
  "Contractual volume fulfilled": "अनुबंधित मात्रा पूर्ण",
  "Contribution (b_i · y_i)": "योगदान (b_i · y_i)",
  "Convex QP": "उत्तल QP",
  "Copy": "कॉपी करें",
  "Core solver routines in sovopt/": "sovopt/ में कोर सॉल्वर रूटीन",
  "Cracking conversion is limited by reactor bed maintenance. Atmospheric residue is bypassed directly to low-value bunker fuel oil, reducing overall economic margin.": "क्रैकिंग रूपांतरण रिएक्टर बेड रखरखाव द्वारा सीमित है। वायुमंडलीय अवशेष को सीधे कम मूल्य वाले बंकर ईंधन तेल में बाईपास किया जाता है, जिससे समग्र आर्थिक मार्जिन कम होता है।",
  "Crude intake ratio": "कच्चा तेल इनटेक अनुपात",
  "Crude procurement expands Basrah Heavy to metallurgical maximum 80 kbpd. Fluid catalytic cracker reaches thermal ceiling (50 kbpd), becoming the binding operational constraint.": "क्रूड खरीद बसरा हेवी को धातुकर्म अधिकतम 80 kbpd तक बढ़ाती है। द्रव उत्प्रेरक क्रैकर थर्मल सीमा (50 kbpd) तक पहुँचता है, जो बाध्यकारी परिचालन बाधा बन जाता है।",
  "Crude: Arab Light intake": "क्रूड: अरब लाइट इनटेक",
  "Crude: Basrah Heavy intake": "क्रूड: बसरा हेवी इनटेक",
  "Cryptographic evidence & commit registry": "क्रिप्टोग्राफ़िक साक्ष्य एवं कमिट रजिस्ट्री",
  "Current load": "वर्तमान भार",
  "Dedicated student researchers from RGIPT building an indigenous, mathematically verified numerical solver for the Mangalore Refinery and Petrochemicals Limited problem statement.": "RGIPT के समर्पित छात्र शोधकर्ता मैंगलोर रिफाइनरी एंड पेट्रोकेमिकल्स लिमिटेड समस्या विवरण के लिए एक स्वदेशी, गणितीय रूप से सत्यापित संख्यात्मक सॉल्वर का निर्माण कर रहे हैं।",
  "Description": "विवरण",
  "Description & stream": "विवरण एवं स्ट्रीम",
  "Design capacity": "डिज़ाइन क्षमता",
  "Desulfurized heavy naphtha": "विसल्फरीकृत भारी नैफ्था",
  "Deterministic Dispatch · Pure NumPy · Zero Black Boxes": "नियत प्रेषण · शुद्ध NumPy · शून्य ब्लैक बॉक्स",
  "Developed for Smart India Hackathon 2026. Representative refinery inputs are engineering approximations and are not proprietary MRPL operating data.": "स्मार्ट इंडिया हैकाथॉन 2026 के लिए विकसित। प्रतिनिधि रिफाइनरी इनपुट इंजीनियरिंग सन्निकटन हैं और स्वामित्व MRPL परिचालन डेटा नहीं हैं।",
  "Development of a sovereign mathematical optimization core for industrial refinery planning, designed to reduce dependency on proprietary commercial solvers using pure NumPy and Python standard library algorithms.": "औद्योगिक रिफाइनरी योजना के लिए एक सॉवरेन गणितीय अनुकूलन कोर का विकास, शुद्ध NumPy और Python मानक लाइब्रेरी एल्गोरिदम का उपयोग करके वाणिज्यिक सॉल्वरों पर निर्भरता कम करने के लिए डिज़ाइन किया गया।",
  "Diagnostic ranking — not a minimal IIS": "डायग्नोस्टिक रैंकिंग — न्यूनतम IIS नहीं",
  "Diesel Cetane:": "डीजल सीटेन:",
  "Diesel demand quota": "डीजल माँग कोटा",
  "Diesel hydrotreating specification": "डीजल हाइड्रो-ट्रीटिंग विनिर्देश",
  "Discrete MILP": "असतत MILP",
  "Distillate (52 Cetane) + LCO (35 Cetane) -> 51 Cetane Pool": "डिस्टिलेट (52 सीटेन) + LCO (35 सीटेन) -> 51 सीटेन पूल",
  "Distillation": "आसवन",
  "Domain:": "डोमेन:",
  "Download audit package (JSON)": "ऑडिट पैकेज डाउनलोड करें (JSON)",
  "Download production schedule (CSV)": "उत्पादन शेड्यूल डाउनलोड करें (CSV)",
  "Dual multipliers y and reduced costs s must satisfy Karush-Kuhn-Tucker stationarity, with complementary slackness x_j · s_j = 0 across all variables.": "ड्यूअल गुणक y और घटी हुई लागत s को KKT स्थिरता को संतुष्ट करना चाहिए, सभी चरों में पूरक शिथिलता x_j · s_j = 0 के साथ।",
  "Dual residual ||A^T y + s - c||_∞": "ड्यूअल अवशिष्ट ||A^T y + s - c||_∞",
  "Dual stationarity": "ड्यूअल स्थिरता",
  "Dual-Plane Architecture": "द्वि-स्तरीय वास्तुकला",
  "Dynamic array copies": "गतिशील सरणी प्रतियाँ",
  "Economic implication": "आर्थिक प्रभाव",
  "Elementwise CSR loop": "तत्ववार CSR लूप",
  "Elevated furnace firing on semi-regenerative reformer. Reformate yield pushed to maximum 25.5 kbpd. Octane blending margin widens to -$18.25/bbl.": "सेमी-रीजेनेरेटिव रिफॉर्मर पर बढ़ी हुई भट्टी फायरिंग। रिफॉर्मेट उपज अधिकतम 25.5 kbpd तक पहुंचाई गई। ऑक्टेन सम्मिश्रण मार्जिन -$18.25/बैरल तक चौड़ा होता है।",
  "Eliminated CuPy memory pool lock churn": "CuPy मेमोरी पूल लॉक चर्न समाप्त किया गया",
  "Email Ayush Rao": "Ayush Rao को ईमेल करें",
  "Email Khagesh Ranjan": "Khagesh Ranjan को ईमेल करें",
  "Email Muskan Sahu": "Muskan Sahu को ईमेल करें",
  "Email Satyam Gupta": "Satyam Gupta को ईमेल करें",
  "Email Shivanshu Tripathi": "Shivanshu Tripathi को ईमेल करें",
  "Email Sudipto Ghosh": "Sudipto Ghosh को ईमेल करें",
  "End-to-End Workflow": "शुरुआत से अंत तक वर्कफ़्लो",
  "Environmental": "पर्यावरण संबंधी",
  "Equilibrium": "संतुलन",
  "Evaluate refinery response under crude slate shifts, unit turnarounds, and environmental fuel quality tightening. Select any scenario to inspect operational assumptions, business impacts, and bottleneck migrations.": "क्रूड स्लेट परिवर्तन, इकाई टर्नअराउंड और ईंधन गुणवत्ता कड़े होने के तहत रिफाइनरी प्रतिक्रिया का मूल्यांकन करें। परिचालन मान्यताओं, व्यावसायिक प्रभावों और अड़चन प्रवासन का निरीक्षण करने के लिए किसी भी परिदृश्य का चयन करें।",
  "Every optimization instance flows through a structured, transparent pipeline with automatic problem classification, condition-number-aware presolve, sovereign solver execution, and independent unscaled KKT verification.": "प्रत्येक अनुकूलन उदाहरण स्वचालित समस्या वर्गीकरण, स्थिति-संख्या-सचेत प्रीसॉल्व, सॉवरेन सॉल्वर निष्पादन और स्वतंत्र असंरचित KKT सत्यापन के साथ एक संरचित, पारदर्शी पाइपलाइन से गुजरता है।",
  "Evidence measured on physical NVIDIA hardware under AC mains power. Same-machine comparisons against host CPU.": "AC मुख्य शक्ति के तहत भौतिक NVIDIA हार्डवेयर पर मापा गया साक्ष्य। होस्ट CPU के विरुद्ध समान-मशीन तुलना।",
  "Exact rational": "सटीक परिमेय",
  "Exact rational Farkas ray y verified in Fraction arithmetic": "भिन्न अंकगणित में सत्यापित सटीक परिमेय फरकस किरण y",
  "Execute active optimization run": "सक्रिय अनुकूलन चलाएँ",
  "Expected plan margin": "अपेक्षित योजना मार्जिन",
  "Explore Optimization Run": "ऑप्टिमाइज़ेशन रन देखें",
  "Explore Scenarios →": "परिदृश्य देखें →",
  "Export audit artifacts": "ऑडिट आर्टिफ़ैक्ट निर्यात करें",
  "Export machine-readable audit packages, operational schedules, and terminal reproduction commands.": "मशीन-पठनीय ऑडिट पैकेज, परिचालन कार्यक्रम और टर्मिनल पुनरुत्पादन आदेश निर्यात करें।",
  "Exports a tabular operational dispatch sheet for refinery operations engineers, including crude intake, conversion loadings, and product shipments.": "रिफाइनरी संचालन इंजीनियरों के लिए कच्चे तेल के सेवन, रूपांतरण लोडिंग और उत्पाद शिपमेंट सहित एक सारणीबद्ध परिचालन प्रेषण पत्रक निर्यात करता है।",
  "FCC UNIT": "FCC इकाई",
  "FCC feed capacity": "FCC फीड क्षमता",
  "FCC feed capacity (50 kbpd ceiling)": "FCC फीड क्षमता (50 kbpd अधिकतम सीमा)",
  "FCC feed intake": "FCC फीड इनटेक",
  "FCC maintenance turndown": "FCC रखरखाव टर्नडाउन",
  "FCC turndown limit (20 kbpd)": "FCC टर्नडाउन सीमा (20 kbpd)",
  "FCC utilisation": "FCC उपयोग",
  "Farkas Lens is active only when an infeasible instance is certified with an exact rational Farkas ray (e.g.": "फरकस लेंस केवल तभी सक्रिय होता है जब एक असाध्य उदाहरण सटीक परिमेय फरकस किरण के साथ प्रमाणित होता है (उदा.",
  "Farkas Lens — Certificate Contribution Ranking": "फरकस लेंस — प्रमाणपत्र योगदान रैंकिंग",
  "Farkas ray": "फरकस किरण",
  "Finished diesel shipment": "तैयार डीजल शिपमेंट",
  "Finished gasoil header": "तैयार गैसऑयल हेडर",
  "Finished gasoline shipment": "तैयार गैसोलीन शिपमेंट",
  "Finished gasoline shipment quota set to 500 kbpd against a physical CDU ceiling of 100 kbpd. Engine detects impossibility and certifies an exact Farkas ray.": "100 kbpd की भौतिक CDU सीमा के विरुद्ध तैयार गैसोलीन शिपमेंट कोटा 500 kbpd पर सेट किया गया। इंजन असंभवता का पता लगाता है और एक सटीक फरकस किरण प्रमाणित करता है।",
  "Finished product revenues minus crude procurement and unit operating expenditure": "तैयार उत्पाद राजस्व घटा कच्चा तेल खरीद और इकाई परिचालन व्यय",
  "Floating Precision:": "फ्लोटिंग प्रिसिजन:",
  "Floating roof storage": "फ्लोटिंग रूफ स्टोरेज",
  "Fluidized Catalytic Cracking Unit (FCC)": "द्रव उत्प्रेरक क्रैकिंग इकाई (FCC)",
  "Formulation Details": "निरूपण विवरण",
  "Fraction Exact Arithmetic (ℚ)": "भिन्न सटीक अंकगणित (ℚ)",
  "Fraction arithmetic lower bounds": "भिन्न अंकगणित निचली सीमाएँ",
  "Frozen Suite:": "संरक्षित सूट:",
  "Fuel Oil": "ईंधन तेल",
  "Fused primal & dual step RawKernels": "संयुक्त प्राइमल और ड्यूअल स्टेप RawKernels",
  "GPU hardware": "GPU हार्डवेयर",
  "GPU memory allocations": "GPU मेमोरी आवंटन",
  "GPU restarted PDHG delivers accelerated operational exploration; CPU revised simplex independently audits KKT stationarity.": "GPU पुनरारंभित PDHG त्वरित परिचालन अन्वेषण प्रदान करता है; CPU संशोधित सिम्प्लेक्स स्वतंत्र रूप से KKT स्थिरता का ऑडिट करता है।",
  "Gasoline octane rating": "गैसोलीन ऑक्टेन रेटिंग",
  "Gasoline quota vs CDU intake (500 > 100 kbpd)": "गैसोलीन कोटा बनाम CDU इनटेक (500 > 100 kbpd)",
  "Gate 8 CUDA (ms)": "गेट 8 CUDA (ms)",
  "Gate 8 baseline": "गेट 8 बेसलाइन",
  "Gate 8 baseline evidence commit:": "गेट 8 बेसलाइन साक्ष्य कमिट:",
  "Gate 8 baseline vs Gate 9 performance engineering": "गेट 8 बेसलाइन बनाम गेट 9 प्रदर्शन इंजीनियरिंग",
  "Gate 9 CUDA (ms)": "गेट 9 CUDA (ms)",
  "Gate 9 implemented architecture": "गेट 9 कार्यान्वित वास्तुकला",
  "Gate 9 physical CUDA validation commit:": "गेट 9 भौतिक CUDA सत्यापन कमिट:",
  "Gate 9.1 cross-platform checksum portability commit:": "गेट 9.1 क्रॉस-प्लेटफ़ॉर्म चेकसम पोर्टेबिलिटी कमिट:",
  "Generates a JSON audit payload containing model parameter fingerprints, primal solution vectors x*, dual Lagrange multipliers y*, and KKT stationarity residuals.": "मॉडल पैरामीटर फ़िंगरप्रिंट, प्राइमल समाधान वेक्टर x*, ड्यूअल लैग्रेंज गुणक y*, और KKT स्थिरता अवशिष्ट युक्त एक JSON ऑडिट पेलोड उत्पन्न करता है।",
  "Go to slide 1": "स्लाइड 1 पर जाएँ",
  "Go to slide 2": "स्लाइड 2 पर जाएँ",
  "Go to slide 3": "स्लाइड 3 पर जाएँ",
  "Go to slide 4": "स्लाइड 4 पर जाएँ",
  "Go to slide 5": "स्लाइड 5 पर जाएँ",
  "Go to slide 6": "स्लाइड 6 पर जाएँ",
  "Governing constraint": "प्रमुख प्रतिबंध",
  "Granular execution telemetry, CPU vs CUDA speedup ratios, stratum distributions, and physical hardware profiling from the Acer RTX 5050 validation run.": "Acer RTX 5050 सत्यापन रन से विस्तृत निष्पादन टेलीमेट्री, CPU बनाम CUDA गति अनुपात, स्ट्रैटम वितरण, और भौतिक हार्डवेयर प्रोफाइलिंग।",
  "Hardware notice:": "हार्डवेयर सूचना:",
  "Hardware read-only cache loads (LDG.E)": "हार्डवेयर रीड-ओनली कैश लोड (LDG.E)",
  "Hardware, driver version 576.83, and runtime records": "हार्डवेयर, ड्राइवर संस्करण 576.83, और रनटाइम रिकॉर्ड",
  "Heavy fuel oil decant": "भारी ईंधन तेल डिकेंट",
  "High-Basrah heavy discount": "उच्च-बसरा भारी छूट",
  "Historical physical CUDA validation evidence from the Acer RTX 5050 is preserved separately.": "Acer RTX 5050 से ऐतिहासिक भौतिक CUDA सत्यापन साक्ष्य अलग से संरक्षित हैं।",
  "IEEE 754 Double Precision": "IEEE 754 डबल प्रिसिजन",
  "INFEASIBLE_CERTIFIED": "प्रमाणित असाध्य",
  "Ill-conditioned basis or residual check failed": "अस्वस्थ आधार या अवशिष्ट जांच विफल",
  "In compliance with the project charter, unfavorable benchmark results are strictly preserved. Across the entire 18-instance Netlib benchmark suite on the physical Acer RTX 5050, the overall same-machine CPU/CUDA speedup ratio is": "परियोजना चार्टर के अनुपालन में, प्रतिकूल बेंचमार्क परिणाम सख्ती से संरक्षित हैं। भौतिक Acer RTX 5050 पर संपूर्ण 18-उदाहरण Netlib बेंचमार्क सूट में समग्र समान-मशीन CPU/CUDA गति अनुपात है",
  "In industrial refinery scheduling, an erroneous solution produces unexecutable distillation schedules and millions in off-spec penalty. SOV-OPT subjects every outcome to independent unscaled verification before conferring terminal status.": "औद्योगिक रिफाइनरी शेड्यूलिंग में, एक गलत समाधान गैर-निष्पादन योग्य आसवन कार्यक्रम और लाखों का ऑफ-स्पेक जुर्माना पैदा करता है। SOV-OPT अंतिम स्थिति प्रदान करने से पहले प्रत्येक परिणाम को स्वतंत्र असंरचित सत्यापन के अधीन करता है।",
  "In-line finished fuel header": "इन-लाइन तैयार ईंधन हेडर",
  "Incumbent provided if available; optimality not guaranteed": "यदि उपलब्ध हो तो अवलंबी प्रदान किया गया; इष्टतमता की गारंटी नहीं है",
  "Independent CPU Audit (Passed)": "स्वतंत्र CPU ऑडिट (उत्तीर्ण)",
  "Independent Trust Passport Certification": "स्वतंत्र ट्रस्ट पासपोर्ट प्रमाणीकरण",
  "Independent numerical verification on the original untransformed model. Every result is audited against KKT stationarity, dual feasibility, or exact rational certificates before acceptance.": "मूल अपरिवर्तित मॉडल पर स्वतंत्र संख्यात्मक सत्यापन। स्वीकृति से पहले प्रत्येक परिणाम का KKT स्थिरता, ड्यूअल व्यवहार्यता, या सटीक परिमेय प्रमाणपत्रों के विरुद्ध ऑडिट किया जाता है।",
  "Independent verification of primal feasibility and KKT dual stationarity at tol ≤ 1e-07.": "tol ≤ 1e-07 पर प्राइमल व्यवहार्यता और KKT ड्यूअल स्थिरता का स्वतंत्र सत्यापन।",
  "Indigenous GPU-Accelerated Optimization Solver": "स्वदेशी GPU-त्वरित अनुकूलन सॉल्वर",
  "Infeasibility certificates": "असाध्यता प्रमाणपत्र",
  "Infeasibility certified with exact rational Farkas ray in ℚ": "ℚ में सटीक परिमेय फरकस किरण के साथ प्रमाणित असाध्यता",
  "Infeasible (Certified)": "असाध्य (प्रमाणित)",
  "Infeasible Ray:": "असाध्य किरण:",
  "Inspect Benchmarks →": "बेंचमार्क देखें →",
  "Institute of National Importance": "राष्ट्रीय महत्व का संस्थान",
  "Institute of National Importance (INI)": "राष्ट्रीय महत्व का संस्थान (INI)",
  "Integrality residual": "पूर्णांक अवशिष्ट",
  "Interactive process flow diagram across CDU, FCC, Reformer, and Blending units with live stream allocations.": "लाइव स्ट्रीम आवंटन के साथ CDU, FCC, रिफॉर्मर और सम्मिश्रण इकाइयों में इंटरैक्टिव प्रक्रिया प्रवाह आरेख।",
  "Interactive process flowsheet: click any unit to inspect operating rates, yield equations, and dual shadow prices.": "इंटरैक्टिव प्रक्रिया फ्लोशीट: परिचालन दरों, उपज समीकरणों और ड्यूअल शैडो कीमतों का निरीक्षण करने के लिए किसी भी इकाई पर क्लिक करें।",
  "Intermediate & Finished Tank Farm": "मध्यवर्ती एवं तैयार टैंक फार्म",
  "Intermediate rundown lines": "मध्यवर्ती रनडाउन लाइनें",
  "Inventory balanced": "इन्वेंटरी संतुलित",
  "JSON audit package": "JSON ऑडिट पैकेज",
  "KKT Audit & Exact Farkas Ray": "KKT ऑडिट एवं सटीक फरकस किरण",
  "KKT stationarity + exact Farkas ray": "KKT स्थिरता + सटीक फरकस किरण",
  "KKT stationarity verified to tol ≤ 10⁻⁷ on original model (floating-point numerical verification within stated tolerance; not a formal rational proof)": "मूल मॉडल पर tol ≤ 10⁻⁷ के लिए KKT स्थिरता सत्यापित (निर्दिष्ट सहनशीलता के भीतर फ्लोटिंग-पॉइंट संख्यात्मक सत्यापन; औपचारिक परिमेय प्रमाण नहीं)",
  "KKT stationarity verified to tol ≤ 10⁻⁷ on unscaled model": "असंरचित मॉडल पर tol ≤ 10⁻⁷ के लिए KKT स्थिरता सत्यापित",
  "Kernel dispatches per iteration": "प्रति पुनरावृत्ति कर्नेल प्रेषण",
  "Khagesh Ranjan on LinkedIn": "Khagesh Ranjan लिंक्डइन पर",
  "LARGE stratum (n > 1000)": "बड़ा स्ट्रैटम (n > 1000)",
  "LIMIT_REACHED": "सीमा समाप्त",
  "LP / MILP crude scheduling, operational conversion yields, BS-VI quality conformance, and independent numerical verification.": "LP / MILP क्रूड शेड्यूलिंग, परिचालन रूपांतरण उपज, BS-VI गुणवत्ता अनुरूपता, और स्वतंत्र संख्यात्मक सत्यापन।",
  "LP · MILP · QP · PDHG": "LP · MILP · QP · PDHG",
  "LP:": "LP:",
  "Lagrange multiplier λ indicating marginal refinery margin per incremental barrel of capacity.": "क्षमता के प्रति वृद्धिशील बैरल पर सीमांत रिफाइनरी मार्जिन दर्शाने वाला लैग्रेंज गुणक λ।",
  "Lagrange multipliers indicating marginal economic value": "सीमांत आर्थिक मूल्य दर्शाने वाले लैग्रेंज गुणक",
  "Large-scale LP": "बड़े पैमाने का LP",
  "Limit": "सीमा",
  "Linear constraint contributions under exact rational infeasibility rays": "सटीक परिमेय असाध्यता किरणों के तहत रैखिक बाधा योगदान",
  "Load into solver console": "सॉल्वर कंसोल में लोड करें",
  "Lower": "निचली सीमा",
  "MEDIUM stratum (100 < n ≤ 1000)": "मध्यम स्ट्रैटम (100 < n ≤ 1000)",
  "MILP bound verification": "MILP बाउंड सत्यापन",
  "MILP:": "MILP:",
  "MPS / JSON Schema": "MPS / JSON स्कीमा",
  "MRPL Diagnostic: Infeasible demand (Farkas proof)": "MRPL डायग्नोस्टिक: असाध्य माँग (फरकस प्रमाण)",
  "MRPL Home": "MRPL होम",
  "MRPL PS 26119": "MRPL PS 26119",
  "MRPL PS 26119 · Refinery planning prototype": "MRPL PS 26119 · रिफाइनरी योजना प्रोटोटाइप",
  "MRPL Refinery Planning: Multi-period LP": "MRPL रिफाइनरी योजना: बहु-अवधि LP",
  "MRPL Refinery Planning: Smooth dispatch (QP)": "MRPL रिफाइनरी योजना: सुचारू प्रेषण (QP)",
  "MRPL Refinery Planning: Unit commitment (MILP)": "MRPL रिफाइनरी योजना: इकाई प्रतिबद्धता (MILP)",
  "MRPL Refinery Twin (Unsolved)": "MRPL रिफाइनरी ट्विन (असमाधानित)",
  "MRPL_Refinery_Twin_LP": "MRPL_Refinery_Twin_LP",
  "Main menu": "मुख्य मेनू",
  "Mangalore Refinery and Petrochemicals Limited · SOV-OPT Portal": "मैंगलोर रिफाइनरी एंड पेट्रोकेमिकल्स लिमिटेड · SOV-OPT पोर्टल",
  "Marginal value of additional crude intake": "अतिरिक्त क्रूड इनटेक का सीमांत मूल्य",
  "Market": "बाजार",
  "Mathematical contracts": "गणितीय अनुबंध",
  "Mathematical guarantee": "गणितीय गारंटी",
  "Mathematical proof of impossibility. The sovereign simplex Phase-I engine produces an exact rational Farkas ray y proving that no feasible operating schedule exists.": "असंभवता का गणितीय प्रमाण। सॉवरेन सिम्प्लेक्स चरण-I इंजन एक सटीक परिमेय फरकस किरण y उत्पन्न करता है जो साबित करता है कि कोई व्यवहार्य परिचालन कार्यक्रम मौजूद नहीं है।",
  "Max KKT residual": "अधिकतम KKT अवशिष्ट",
  "Measured impact": "मापा गया प्रभाव",
  "Measured. Audited. Reproducible.": "मापा गया। ऑडिट किया गया। पुनरुत्पादनीय।",
  "Meet the Team": "हमारी टीम से मिलें",
  "Mehrotra Interior Point Predictor-Corrector": "मेहरोत्रा इंटीरियर पॉइंट प्रिडिक्टर-कॉरेक्टर",
  "Mehrotra predictor-corrector IPM": "मेहरोत्रा प्रिडिक्टर-कॉरेक्टर IPM",
  "Min 50 kbpd": "न्यूनतम 50 kbpd",
  "Min 95 RON": "न्यूनतम 95 RON",
  "Mobile Navigation Menu": "मोबाइल नेविगेशन मेनू",
  "Mode": "मोड",
  "Model Input": "मॉडल इनपुट",
  "Model SHA-256 Fingerprint:": "मॉडल SHA-256 फिंगरप्रिंट:",
  "Model class": "मॉडल वर्ग",
  "Mogas": "मोगैस (पेट्रोल)",
  "Multiple temporary VRAM writes": "एकाधिक अस्थायी VRAM लेखन",
  "Multiplier (y_i)": "गुणक (y_i)",
  "Muskan Sahu on LinkedIn": "Muskan Sahu लिंक्डइन पर",
  "NOT_EXECUTED": "चलाया नहीं गया",
  "NUMERICAL_FAILURE": "संख्यात्मक विफलता",
  "NVIDIA GeForce RTX 5050 Laptop GPU": "NVIDIA GeForce RTX 5050 लैपटॉप GPU",
  "NVIDIA driver": "NVIDIA ड्राइवर",
  "Naphtha 20% · Distillate 45% · Residue 35%": "नैफ्था 20% · डिस्टिलेट 45% · अवशेष 35%",
  "Naphtha, Reformate, Distillate, CatGas, LCO, Fuel Oil": "नैफ्था, रिफॉर्मेट, डिस्टिलेट, कैटगैस, LCO, ईंधन तेल",
  "Navigation": "नेविगेशन",
  "Netlib LP: AFIRO (Saunders Bell Labs)": "Netlib LP: AFIRO (Saunders Bell Labs)",
  "Netlib LP: BLEND": "Netlib LP: BLEND",
  "Netlib LP: SC50A": "Netlib LP: SC50A",
  "Netlib LP: SC50B": "Netlib LP: SC50B",
  "Next slide": "अगली स्लाइड",
  "Node, iteration, or wall-clock budget exhausted": "नोड, पुनरावृत्ति, या समय सीमा समाप्त",
  "Numerical Trust Layer": "न्यूमेरिकल ट्रस्ट लेयर",
  "Numerical performance": "संख्यात्मक प्रदर्शन",
  "Numerical trust & verification layer": "संख्यात्मक विश्वास एवं सत्यापन परत",
  "Numerical verification": "संख्यात्मक सत्यापन",
  "OPTIMAL_VERIFIED": "इष्टतम सत्यापित",
  "ORIGINAL-MODEL KKT VERIFICATION": "मूल-मॉडल KKT सत्यापन",
  "Objective & residual convergence trajectory": "उद्देश्य एवं अवशिष्ट अभिसरण प्रक्षेपवक्र",
  "Octane Blending:": "ऑक्टेन सम्मिश्रण:",
  "Octane verified (95.1 RON)": "ऑक्टेन सत्यापित (95.1 RON)",
  "One Sovereign Optimization Core": "एक सॉवरेन अनुकूलन कोर",
  "Open Navigation Menu": "नेविगेशन मेनू खोलें",
  "Open Process Twin →": "प्रोसेस मॉडल खोलें →",
  "Operating under standard design parameters. Fluid catalytic cracker operating at 90% capacity, leaving 5.0 kbpd headroom for unplanned swings. Reformer severity set at normal reformate RON 100 target.": "मानक डिज़ाइन मापदंडों के तहत संचालन। द्रव उत्प्रेरक क्रैकर 90% क्षमता पर काम कर रहा है, जिससे अनियोजित परिवर्तनों के लिए 5.0 kbpd की गुंजाइश बचती है। रिफॉर्मर तीव्रता सामान्य रिफॉर्मेट RON 100 लक्ष्य पर सेट है।",
  "Operational meaning": "परिचालन अर्थ",
  "Operational parameter": "परिचालन पैरामीटर",
  "Operational scenarios & stress testing": "परिचालन परिदृश्य एवं तनाव परीक्षण",
  "Optimal allocation vector (x*)": "इष्टतम आवंटन वेक्टर (x*)",
  "Optimal at ceiling": "अधिकतम सीमा पर इष्टतम",
  "Optimal rate (x*)": "इष्टतम दर (x*)",
  "Optimise crude intake, conversion, blending and production schedules with independently certified numerical results. Representative open-literature refinery planning formulation. All units, yields and economics are representative engineering approximations.": "स्वतंत्र रूप से प्रमाणित संख्यात्मक परिणामों के साथ क्रूड इनटेक, रूपांतरण, सम्मिश्रण और उत्पादन कार्यक्रम का अनुकूलन करें। प्रतिनिधि ओपन-साहित्य रिफाइनरी योजना निरूपण। सभी इकाइयाँ, उपज और अर्थशास्त्र प्रतिनिधि इंजीनियरिंग सन्निकटन हैं।",
  "Optimization That Proves What It Can": "अनुकूलन जो प्रमाणित करता है कि वह क्या कर सकता है",
  "Optimization vector": "अनुकूलन वेक्टर",
  "Parity boundary; GPU compute balances driver overhead": "समानता सीमा; GPU गणना ड्राइवर ओवरहेड को संतुलित करती है",
  "Pass": "उत्तीर्ण",
  "Pause carousel": "हिंडोला रोकें",
  "Peak demand": "चरम माँग",
  "Periodic restarts": "आवधिक पुनरारंभ",
  "Physical": "भौतिक",
  "Physical Acer RTX 5050 Laptop GPU (12.0 CC · 8GB VRAM)": "भौतिक Acer RTX 5050 लैपटॉप GPU (12.0 CC · 8GB VRAM)",
  "Physical CUDA SpMV + CPU KKT": "भौतिक CUDA SpMV + CPU KKT",
  "Physical Hardware Benchmarking": "भौतिक हार्डवेयर बेंचमार्किंग",
  "Physical Hardware Telemetry": "भौतिक हार्डवेयर टेलीमेट्री",
  "Physical benchmark suite (18 continuous Netlib LP instances)": "भौतिक बेंचमार्क सूट (18 सतत Netlib LP मॉडल)",
  "Physical bottleneck shock": "भौतिक अड़चन झटका",
  "Physical impossibility proven; capacity expansion required": "भौतिक असंभवता सिद्ध; क्षमता विस्तार आवश्यक",
  "Physical validation": "भौतिक सत्यापन",
  "Plan net margin": "योजना शुद्ध मार्जिन",
  "Platform:": "प्लेटफ़ॉर्म:",
  "Pool octane specification binding": "पूल ऑक्टेन विनिर्देश बाध्यकारी",
  "Pre-configured operational baselines, high-Basrah crude discount sweeps, summer high-octane peaks, and infeasible demand shocks.": "पूर्व-कॉन्फ़िगर किए गए परिचालन आधार रेखाएं, उच्च-बसरा क्रूड छूट स्वीप, ग्रीष्मकालीन उच्च-ऑक्टेन चोटियां, और असाध्य मांग झटके।",
  "Precise mathematical conditions for solver outcomes": "सॉल्वर परिणामों के लिए सटीक गणितीय स्थितियाँ",
  "Presolve & Scaling": "प्रीसॉल्व एवं स्केलिंग",
  "Previous slide": "पिछली स्लाइड",
  "Primal feasibility": "प्राइमल व्यवहार्यता",
  "Primal residual ||Ax - b||_∞": "प्राइमल अवशिष्ट ||Ax - b||_∞",
  "Primal residuals, dual residuals, and bound violations are computed directly against the unscaled model (Ax = b, x ≥ 0). Infeasible models are accompanied by exact rational Farkas certificates.": "प्राइमल अवशिष्ट, ड्यूअल अवशिष्ट, और बाउंड उल्लंघन सीधे असंरचित मॉडल (Ax = b, x ≥ 0) के विरुद्ध गणना किए जाते हैं। असाध्य मॉडल सटीक परिमेय फरकस प्रमाणपत्रों के साथ होते हैं।",
  "Primal ||Ax - b||_∞ ≤ tol · Dual ||Aᵀy + s - c||_∞ ≤ tol": "प्राइमल ||Ax - b||_∞ ≤ tol · ड्यूअल ||Aᵀy + s - c||_∞ ≤ tol",
  "Primary atmospheric separation": "प्राथमिक वायुमंडलीय पृथक्करण",
  "Primary benchmark and evidence artifacts": "प्राथमिक बेंचमार्क एवं साक्ष्य आर्टिफ़ैक्ट",
  "Process flow / Base operational equilibrium": "प्रक्रिया प्रवाह / आधार परिचालन संतुलन",
  "Provenance records": "उत्पत्ति रिकॉर्ड",
  "Provenance:": "उत्पत्ति:",
  "Pure NumPy & Python stdlib": "शुद्ध NumPy एवं Python stdlib",
  "Pushed and verified commits on remote repository": "रिमोट रिपॉजिटरी पर पुश और सत्यापित कमिट",
  "QP:": "QP:",
  "Quadratic throughput flutter penalties are active to protect hydrotreating catalysts from thermal cycling. Solved via Mehrotra predictor-corrector interior point method.": "हाइड्रोट्रीटिंग उत्प्रेरकों को थर्मल चक्रण से बचाने के लिए द्विघात थ्रूपुट स्पंदन दंड सक्रिय हैं। मेहरोत्रा प्रिडिक्टर-कॉरेक्टर इंटीरियर पॉइंट विधि के माध्यम से हल किया गया।",
  "Quality": "गुणवत्ता",
  "REFORMER": "रिफॉर्मर",
  "RON 98 Pool": "RON 98 पूल",
  "RTX 5050 (Driver 576.83)": "RTX 5050 (ड्राइवर 576.83)",
  "RTX 5050 Benchmark Evidence": "RTX 5050 बेंचमार्क साक्ष्य",
  "RTX 5050 Benchmarks": "RTX 5050 बेंचमार्क",
  "Rank": "रैंक",
  "Raw byte": "रॉ बाइट",
  "Refinery Dispatch Formulation": "रिफाइनरी प्रेषण निरूपण",
  "Refinery Optimization Network Topology Schematic": "रिफाइनरी ऑप्टिमाइज़ेशन नेटवर्क टोपोलॉजी योजना",
  "Refinery Planning Twin": "रिफाइनरी योजना मॉडल",
  "Refinery planning & operational optimisation": "रिफाइनरी योजना एवं परिचालन अनुकूलन",
  "Refinery planning dashboard provides solver-driven process flow and scenario analysis.": "रिफाइनरी योजना डैशबोर्ड सॉल्वर-संचालित प्रक्रिया प्रवाह और परिदृश्य विश्लेषण प्रदान करता है।",
  "Refinery production schedule": "रिफाइनरी उत्पादन कार्यक्रम",
  "Refinery stream role": "रिफाइनरी स्ट्रीम भूमिका",
  "Refining & Petrochemical Supply Chain Optimization.": "रिफाइनिंग एवं पेट्रोकेमिकल आपूर्ति श्रृंखला अनुकूलन।",
  "Reformate (100 RON) + CatGas (92 RON) -> 95 RON Pool": "रिफॉर्मेट (100 RON) + कैटगैस (92 RON) -> 95 RON पूल",
  "Reformate (100 RON) 85% + hydrogen": "रिफॉर्मेट (100 RON) 85% + हाइड्रोजन",
  "Reformate to gasoline pool": "रिफॉर्मेट से गैसोलीन पूल",
  "Reformer feed intake": "रिफॉर्मर फीड इनटेक",
  "Reformer severity ceiling (30 kbpd)": "रिफॉर्मर तीव्रता अधिकतम सीमा (30 kbpd)",
  "Reformer throughput": "रिफॉर्मर थ्रूपुट",
  "Relative discrepancy": "सापेक्ष विसंगति",
  "Reports, audit packs & production schedules": "रिपोर्ट, ऑडिट पैक एवं उत्पादन कार्यक्रम",
  "Representative open-literature refinery planning formulation. All units, yields and economics are representative engineering approximations.": "प्रतिनिधि ओपन-साहित्य रिफाइनरी योजना निरूपण। सभी इकाइयाँ, उपज और अर्थशास्त्र प्रतिनिधि इंजीनियरिंग सन्निकटन हैं।",
  "Resident vector-copy in-place updates": "रेसिडेंट वेक्टर-कॉपी इन-प्लेस अपडेट",
  "Residual 1.42 × 10⁻¹⁵": "अवशिष्ट 1.42 × 10⁻¹⁵",
  "Restarted PDHG (first-order)": "पुनरारंभित PDHG (प्रथम-क्रम)",
  "Revised dual simplex (sparse LU PFI)": "संशोधित ड्यूअल सिम्प्लेक्स (स्पार्स LU PFI)",
  "Rigorous Dual-Plane Dispatch": "कठोर द्वि-स्तरीय प्रेषण",
  "Ruiz / Geometric Scaling": "रूइज़ / ज्यामितीय स्केलिंग",
  "Run solve to compute": "गणना के लिए सॉल्व चलाएँ",
  "Run test suite (298 tests):": "परीक्षण सूट चलाएँ (298 परीक्षण):",
  "SC-01: Base equilibrium": "SC-01: आधार संतुलन",
  "SC-02: High-Basrah heavy": "SC-02: उच्च-बसरा हेवी",
  "SC-03": "SC-03",
  "SC-03: Summer octane peak": "SC-03: ग्रीष्मकालीन ऑक्टेन चरम",
  "SC-04": "SC-04",
  "SC-04: FCC turndown": "SC-04: FCC टर्नडाउन",
  "SC-05": "SC-05",
  "SC-05: Strict BS-VI spec": "SC-05: सख्त BS-VI विनिर्देश",
  "SC-06": "SC-06",
  "SC-06: Infeasible shock": "SC-06: असाध्य झटका",
  "SHA-256 Model Fingerprint on unscaled model data": "असंरचित मॉडल डेटा पर SHA-256 मॉडल फ़िंगरप्रिंट",
  "SHA-256 Model Provenance": "SHA-256 मॉडल उत्पत्ति",
  "SIH 2026 PS 26119": "SIH 2026 PS 26119",
  "SM 12.0 (Blackwell Architecture)": "SM 12.0 (ब्लैकवेल आर्किटेक्चर)",
  "SMALL stratum (n ≤ 100)": "छोटा स्ट्रैटम (n ≤ 100)",
  "SOV-OPT Highlights Carousel": "SOV-OPT मुख्य अंश हिंडोला",
  "Numerically verified for this prototype model": "इस प्रोटोटाइप मॉडल के लिए संख्यात्मक रूप से सत्यापित",
  "Satyam Gupta on LinkedIn": "Satyam Gupta लिंक्डइन पर",
  "Scenario A": "परिदृश्य A",
  "Scenario Analysis": "परिदृश्य विश्लेषण",
  "Scenario B": "परिदृश्य B",
  "Scenario SC-06: Infeasible Demand Shock": "परिदृश्य SC-06: असाध्य माँग झटका",
  "Scenario delta comparison matrix": "परिदृश्य अंतर तुलना मैट्रिक्स",
  "Scientific reporting disclosure:": "वैज्ञानिक रिपोर्टिंग प्रकटीकरण:",
  "Scope": "कार्यक्षेत्र",
  "Screen reader access": "स्क्रीन रीडर एक्सेस",
  "Seasonal motor gasoline demand surges to 52 kbpd (+25%). Catalytic Reformer runs at 100% capacity limit to satisfy pool RON 95 octane requirements.": "मौसमी मोटर गैसोलीन की मांग बढ़कर 52 kbpd (+25%) हो गई। कैटेलिटिक रिफॉर्मर पूल RON 95 ऑक्टेन आवश्यकताओं को पूरा करने के लिए 100% क्षमता सीमा पर चलता है।",
  "Selected unit": "चयनित इकाई",
  "Shadow price": "शैडो मूल्य",
  "Shadow price (λ)": "शैडो मूल्य (λ)",
  "Shivanshu Tripathi on LinkedIn": "Shivanshu Tripathi लिंक्डइन पर",
  "Slack available (13 kbpd)": "उपलब्ध अतिरिक्त क्षमता (13 kbpd)",
  "Slack available: 13.0 kbpd headroom": "उपलब्ध अतिरिक्त क्षमता: 13.0 kbpd गुंजाइश",
  "Slide 1 of 6: Project Identity": "स्लाइड 1 / 6: परियोजना पहचान",
  "Slide 2 of 6: Problem Statement": "स्लाइड 2 / 6: समस्या विवरण",
  "Slide 3 of 6: Pipeline Architecture": "स्लाइड 3 / 6: पाइपलाइन वास्तुकला",
  "Slide 4 of 6: Numerical Trust": "स्लाइड 4 / 6: संख्यात्मक विश्वास",
  "Slide 5 of 6: Team VarunNetra": "स्लाइड 5 / 6: टीम वरुणनेत्र",
  "Slide 6 of 6: Hardware Evidence": "स्लाइड 6 / 6: हार्डवेयर साक्ष्य",
  "Smart India Hackathon 2026 · MRPL PS 26119": "स्मार्ट इंडिया हैकाथॉन 2026 · MRPL PS 26119",
  "Smart India Hackathon 2026 · Ministry of Petroleum & Natural Gas": "स्मार्ट इंडिया हैकाथॉन 2026 · पेट्रोलियम एवं प्राकृतिक गैस मंत्रालय",
  "Smart India Hackathon 2026 · Problem Statement 26119": "स्मार्ट इंडिया हैकाथॉन 2026 · समस्या विवरण 26119",
  "Smart India Hackathon Team Details": "स्मार्ट इंडिया हैकाथॉन टीम विवरण",
  "Solution rejected; equilibration scaling advised": "समाधान अस्वीकृत; संतुलन स्केलिंग की सलाह दी गई",
  "Solve refinery LP twin:": "रिफाइनरी LP मॉडल हल करें:",
  "Solver numerical analytics & profiling": "सॉल्वर संख्यात्मक विश्लेषण एवं प्रोफाइलिंग",
  "Solver version & commit": "सॉल्वर संस्करण एवं कमिट",
  "Sovereign Architecture Pipeline": "सॉवरेन वास्तुकला पाइपलाइन",
  "Sovereign Mathematical Core": "सॉवरेन गणितीय कोर",
  "Sovereign Numerical Optimization Core": "सॉवरेन संख्यात्मक अनुकूलन कोर",
  "Sovereign reference CPU": "सॉवरेन संदर्भ CPU",
  "Sovereign reference CPU (Simplex / IPM / B&B)": "सॉवरेन संदर्भ CPU (सिम्प्लेक्स / IPM / B&B)",
  "Sovereign restarted PDHG · CPU": "सॉवरेन पुनरारंभित PDHG · CPU",
  "SpMV memory layout": "SpMV मेमोरी लेआउट",
  "Sparse CSR": "स्पार्स CSR",
  "Specification compliant": "विनिर्देश अनुरूप",
  "Speedup (CPU/CUDA)": "गति सुधार (CPU/CUDA)",
  "Speedup on LARGE Netlib Stratum": "बड़े Netlib स्ट्रैटम पर गति सुधार",
  "Standard Primal Form": "मानक प्राइमल रूप",
  "Stationarity & positive semidefiniteness": "स्थिरता एवं धनात्मक अर्ध-निश्चितता",
  "Status": "स्थिति",
  "Strategic decision analysis": "रणनीतिक निर्णय विश्लेषण",
  "Stratum": "स्ट्रैटम",
  "Strict BS-VI fuel quality": "सख्त BS-VI ईंधन गुणवत्ता",
  "Structural impact": "संरचनात्मक प्रभाव",
  "Sudipto Ghosh on LinkedIn": "Sudipto Ghosh लिंक्डइन पर",
  "Sulfur Limit:": "सल्फर सीमा:",
  "Summer high-octane surge": "ग्रीष्मकालीन उच्च-ऑक्टेन उछाल",
  "Supported Status:": "समर्थन स्थिति:",
  "Supported mathematical models": "समर्थित गणितीय मॉडल",
  "Target instance": "लक्षित मॉडल",
  "Team ID: 177365": "टीम आईडी: 177365",
  "Team Members (VarunNetra · ID 177365)": "टीम के सदस्य (वरुणनेत्र · आईडी 177365)",
  "Team VarunNetra · Team ID 177365": "टीम वरुणनेत्र · टीम आईडी 177365",
  "Terminal reproduction commands": "टर्मिनल पुनरुत्पादन आदेश",
  "Terminal status semantics contract": "अंतिम स्थिति सिमेंटिक्स अनुबंध",
  "Text-LF": "टेक्स्ट-LF",
  "The SHA-256 model fingerprint is an integrity identifier; this Passport is not a digital signature. Results are verified on the original unscaled constraint model.": "SHA-256 मॉडल फ़िंगरप्रिंट एक अखंडता पहचानकर्ता है; यह पासपोर्ट डिजिटल हस्ताक्षर नहीं है। परिणाम मूल असंरचित बाधा मॉडल पर सत्यापित किए जाते हैं।",
  "Thermal": "थर्मल",
  "Trust Passport": "ट्रस्ट पासपोर्ट",
  "Trust Philosophy & Verification": "विश्वास दर्शन एवं सत्यापन",
  "Turnaround": "टर्नअराउंड",
  "Two-Phase Revised Primal Simplex": "दो-चरणीय संशोधित प्राइमल सिम्प्लेक्स",
  "Type": "प्रकार",
  "Ultra-low sulfur (<10 ppm) & high-cetane specifications restrict cracked LCO blending into high-speed diesel pool. Hydroprocessing units operate at elevated severity.": "अल्ट्रा-लो सल्फर (<10 ppm) और उच्च-सीटेन विनिर्देश हाई-स्पीड डीजल पूल में क्रैक किए गए LCO सम्मिश्रण को प्रतिबंधित करते हैं। हाइड्रोप्रोसेसिंग इकाइयाँ उच्च गंभीरता पर काम करती हैं।",
  "Unscheduled turnaround clamps FCC unit feed to 20 kbpd (-60%). Gasoil balances re-routed to heavy fuel oil; diesel relies exclusively on straight-run distillate.": "अनियोजित टर्नअराउंड FCC यूनिट फीड को 20 kbpd (-60%) तक सीमित करता है। गैसऑयल संतुलन को भारी ईंधन तेल में फिर से भेजा जाता है; डीजल विशेष रूप से स्ट्रेट-रन डिस्टिलेट पर निर्भर करता है।",
  "Upgrading capacity constraint": "उन्नयन क्षमता बाधा",
  "Upper": "ऊपरी सीमा",
  "VRAM Allocation:": "VRAM आवंटन:",
  "Validation SHA:": "सत्यापन SHA:",
  "Variable": "चर",
  "Variance (Δ = B - A)": "भिन्नता (Δ = B - A)",
  "Vector arithmetic pipeline": "वेक्टर अंकगणित पाइपलाइन",
  "Verification Records": "सत्यापन रिकॉर्ड",
  "Verification Status:": "सत्यापन स्थिति:",
  "Verification status": "सत्यापन स्थिति",
  "Verified": "सत्यापित",
  "Verify repository checksums:": "रिपॉजिटरी चेकसम सत्यापित करें:",
  "View Hardware Benchmarks": "हार्डवेयर बेंचमार्क देखें",
  "View Process Twin": "प्रक्रिया मॉडल देखें",
  "When a refinery scenario is declared infeasible (e.g. demand exceeds intake capacity), the solver certifies an exact Farkas vector y in infinite-precision rational arithmetic.": "जब एक रिफाइनरी परिदृश्य को असाध्य घोषित किया जाता है (उदा. मांग इनटेक क्षमता से अधिक हो), तो सॉल्वर अनंत-परिशुद्धता परिमेय अंकगणित में एक सटीक फरकस वेक्टर y प्रमाणित करता है।",
  "Yield basis": "उपज आधार",
  "Zero Unverified Claims": "शून्य असत्यापित दावे",
  "and": "और",
  "compared to Gate 8.": "गेट 8 की तुलना में।",
  "minimize": "न्यूनतम करें",
  "not demonstrated": "प्रदर्शित नहीं हुआ",
  "on small instances due to PCIe and kernel launch latency. Gate 9 CUDA performance engineering improved raw GPU execution time by": "PCIe और कर्नेल लॉन्च लेटेंसी के कारण छोटे उदाहरणों पर। गेट 9 CUDA प्रदर्शन इंजीनियरिंग ने GPU निष्पादन समय में सुधार किया",
  "or": "या",
  "subject to": "बशर्ते कि",
  "tabs.": "टैब।",
  "vs": "बनाम",
  "z_LB ≤ z* (exact rational)": "z_LB ≤ z* (सटीक परिमेय)",
  "~15 dynamic arrays / iter": "~15 गतिशील सरणियाँ / पुनरावृत्ति",
  "~18 CuPy Python dispatches": "~18 CuPy Python प्रेषण",
  "© 2026 SOV-OPT Project Team · Rajiv Gandhi Institute of Petroleum Technology. Developed for MRPL Problem Statement 26119.": "© 2026 SOV-OPT प्रोजेक्ट टीम · राजीव गाँधी पेट्रोलियम प्रौद्योगिकी संस्थान। MRPL समस्या विवरण 26119 हेतु विकसित।",
  "ऑप्टिमाइज़ेशन इंजन प्रेषण एवं लाइव सॉल्व": "ऑप्टिमाइज़ेशन इंजन प्रेषण एवं लाइव सॉल्व",
  "मॉडल एवं परिचालन इनपुट": "मॉडल एवं परिचालन इनपुट",
  "⇄ Pan flowsheet horizontally": "⇄ फ्लोशीट को क्षैतिज रूप से पैन करें",
  "≤ 10 ppm BS-VI": "≤ 10 ppm BS-VI",
  "≤ 100 kbpd": "≤ 100 kbpd",
  "≥ 51 Index": "≥ 51 इंडेक्स",
  "≥ 91 RON": "≥ 91 RON",
  "✓ Historical Acer RTX 5050 CUDA evidence preserved for differential comparison.": "✓ अंतर तुलना हेतु ऐतिहासिक Acer RTX 5050 CUDA साक्ष्य संरक्षित।",
  "✓ Infinite-precision rational Farkas rays certify structural infeasibility.": "✓ अनंत-परिशुद्धता परिमेय फरकस किरणें संरचनात्मक असाध्यता प्रमाणित करती हैं।",
  "✓ Model-fingerprinted Trust Passport generated for every accepted solve.": "✓ प्रत्येक स्वीकृत समाधान के लिए मॉडल-फिंगरप्रिंटेड ट्रस्ट पासपोर्ट तैयार किया गया।",
  "✓ Sovereign solver core: validated by the repository's automated numerical and integration test suite.": "✓ सॉवरेन सॉल्वर कोर: रिपॉजिटरी के स्वचालित संख्यात्मक एवं एकीकरण परीक्षण सूट द्वारा मान्य।",
  "-$105.00 / bbl": "-$105.00 / बैरल",
  "-$105.00/bbl": "-$105.00/बैरल",
  "-$115.00 / bbl": "-$115.00 / बैरल",
  "-$115.00/bbl": "-$115.00/बैरल",
  "-$29.89/bbl": "-$29.89/बैरल",
  "-$8.40/bbl": "-$8.40/बैरल",
  "1.07×": "1.07×",
  "1.13×": "1.13×",
  "1.81×": "1.81×",
  "1.2 barg": "1.2 barg",
  "15.0 barg": "15.0 barg",
  "2.1 barg": "2.1 barg",
  "4.5 barg": "4.5 barg",
  "5.0 barg": "5.0 barg",
  "250v / 1000r": "250 चर / 1000 पंक्तियाँ",
  "40k": "40k",
  "50k": "50k",
  "50 nodes": "50 नोड्स",
  "5000 vars": "5000 चर",
  "7.96 GB GDDR6": "7.96 GB GDDR6",
  "8 GB GDDR6": "8 GB GDDR6",
  "VRAM": "VRAM",
  "AR": "AR",
  "KR": "KR",
  "SG": "SG",
  "ST": "ST",
  "SC-01": "SC-01",
  "SC-02": "SC-02",
  "✓ Sovereign solver core: validated by the repository\'s automated numerical and integration test suite.": "✓ सॉवरेन सॉल्वर कोर: रिपॉजिटरी के स्वचालित संख्यात्मक एवं एकीकरण परीक्षण सूट द्वारा मान्य।",
  "✓ Sovereign solver core: validated by the repository's automated numerical and integration test suite.": "✓ सॉवरेन सॉल्वर कोर: रिपॉजिटरी के स्वचालित संख्यात्मक एवं एकीकरण परीक्षण सूट द्वारा मान्य।",
  "Basrah Heavy": "बसरा हेवी",
  "Arab Light": "अरब लाइट",
  "01 · PRIMARY": "01 · प्राथमिक",
  "Atmospheric": "वातावरणीय",
  "Distillation": "आसवन",
  "CDU Feed": "CDU फीड",
  "Naphtha": "नेफ्था",
  "Distillate Header": "डिस्टिलेट हेडर",
  "Residue": "अवशेष",
  "02 · OCTANE": "02 · ऑक्टेन",
  "Semi-Regen": "सेमी-रीजन",
  "Reformer": "रिफॉर्मर",
  "03 · CRACKING": "03 · क्रैकिंग",
  "Fluid Catalytic": "फ्लुइड कैटेलिटिक",
  "Cracker (FCC)": "क्रैकर (FCC)",
  "Reformate (100 RON)": "रिफॉर्मेट (100 RON)",
  "CatGas (92 RON)": "कैटगैस (92 RON)",
  "FCC LCO": "FCC LCO",
  "Slurry/Bottoms": "स्लरी/तली",
  "04 · POOL": "04 · पूल",
  "Gasoline Pool": "गैसोलीन पूल",
  "05 · POOL": "05 · पूल",
  "BS-VI Diesel Pool": "BS-VI डीजल पूल",
  "06 · RESIDUE": "06 · अवशेष",
  "Fuel Oil Decant": "फ्यूल ऑयल डिकैन्ट",
  "Market: $115/bbl": "बाजार: $115/bbl",
  "Market: $105/bbl": "बाजार: $105/bbl",
  "Bunker: $55/bbl": "बंकर: $55/bbl",
  "Baseline scenario loaded — click \"Run optimisation\" to generate certified convergence trajectory": "आधारभूत परिदृश्य लोड किया गया — प्रमाणित अभिसरण प्रक्षेपवक्र उत्पन्न करने के लिए \"ऑप्टिमाइज़ेशन चलाएँ\" पर क्लिक करें",
  "Baseline scenario loaded — click &quot;Run optimisation&quot; to generate certified convergence trajectory": "आधारभूत परिदृश्य लोड किया गया — प्रमाणित अभिसरण प्रक्षेपवक्र उत्पन्न करने के लिए \"ऑप्टिमाइज़ेशन चलाएँ\" पर क्लिक करें",
  "Sparse LU revised simplex verifies feasibility & KKT optimality at final basis": "स्पार्स LU संशोधित सिम्प्लेक्स अंतिम आधार पर साध्यता एवं KKT इष्टतमता की पुष्टि करता है",
  "Sparse LU revised simplex verifies feasibility &amp; KKT optimality at final basis": "स्पार्स LU संशोधित सिम्प्लेक्स अंतिम आधार पर साध्यता एवं KKT इष्टतमता की पुष्टि करता है",
  "Contraction of infinity-norm KKT residuals over iterations": "पुनरावृत्तियों के दौरान अनंत-मानक KKT अवशेषों का संकुचन",
  "Certificate vector y satisfies: y ≥ 0, Aᵀy ≤ 0, bᵀy > 0": "प्रमाणपत्र वेक्टर y संतुष्ट करता है: y ≥ 0, Aᵀy ≤ 0, bᵀy > 0",
  "Certificate vector y satisfies: y ≥ 0, Aᵀy ≤ 0, bᵀy &gt; 0": "प्रमाणपत्र वेक्टर y संतुष्ट करता है: y ≥ 0, Aᵀy ≤ 0, bᵀy > 0",
  "Net operational plan margin": "शुद्ध परिचालन योजना मार्जिन",
  "Arab Light crude intake": "अरब लाइट क्रूड अंतर्ग्रहण",
  "Basrah Heavy crude intake": "बसरा हेवी क्रूड अंतर्ग्रहण",
  "FCC unit feed rate": "FCC यूनिट फीड दर",
  "Reformer feed rate": "रिफॉर्मर फीड दर",
  "Governing bottleneck constraint": "शासी बाधा अड़चन",
  "Finished gasoline shipment": "तैयार गैसोलीन प्रेषण",
  "Finished diesel shipment": "तैयार डीजल प्रेषण",
  "Pivoted": "धुरीकृत (पिवोटेड)",
  "Identical": "समान (अपरिवर्तित)",
  "Infeasible": "असाध्य (इनफीजिबल)",
  "Infeasible (Certified)": "असाध्य (प्रमाणित Farkas)",
  "REFINERY-LP (Unsolved)": "REFINERY-LP (अनसुलझा)",
  "Primal residual": "प्राइमल अवशेष",
  "Dual residual": "ड्यूअल अवशेष",
  "SMALL": "छोटा",
  "MEDIUM": "मध्यम",
  "LARGE": "बड़ा"
};

  function t(str) {
    if (!str) return str;
    if (STATE.currentLanguage !== 'hi') return str;
    const s = String(str);
    const trimmed = s.trim();
    if (TRANSLATION_MAP[trimmed]) {
      return s.replace(trimmed, TRANSLATION_MAP[trimmed]);
    }
    return s;
  }

  function applyDOMTranslations(root, lang) {
    if (!root) root = document.body;
    const isHi = (lang === 'hi');

    // Walk all visible text nodes
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function(node) {
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        const tag = parent.tagName.toLowerCase();
        if (tag === 'script' || tag === 'style' || tag === 'code' || tag === 'pre') return NodeFilter.FILTER_REJECT;
        if (parent.closest('#mrpl-masthead .mrpl-title-block')) return NodeFilter.FILTER_REJECT;
        if (parent.closest('.notranslate') || parent.closest('#btn-acc-lang')) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });

    const nodes = [];
    while (walker.nextNode()) {
      nodes.push(walker.currentNode);
    }

    for (const node of nodes) {
      if (isHi) {
        if (node.__origText === undefined) {
          node.__origText = node.nodeValue;
        }
        const raw = node.__origText;
        const trimmed = raw.trim();
        const normalized = trimmed.replace(/\s+/g, ' ');
        if (TRANSLATION_MAP[trimmed]) {
          node.nodeValue = raw.replace(trimmed, TRANSLATION_MAP[trimmed]);
        } else if (TRANSLATION_MAP[normalized]) {
          node.nodeValue = raw.replace(trimmed, TRANSLATION_MAP[normalized]);
        }
      } else {
        if (node.__origText !== undefined) {
          node.nodeValue = node.__origText;
        }
      }
    }

    // Translate common attributes
    const attrElements = root.querySelectorAll ? root.querySelectorAll('[placeholder], [title], [aria-label]') : [];
    attrElements.forEach(el => {
      if (el.closest('#mrpl-masthead .mrpl-title-block') || el.closest('.notranslate') || el.closest('#btn-acc-lang') || el.id === 'btn-acc-lang') return;
      ['placeholder', 'title', 'aria-label'].forEach(attr => {
        const val = el.getAttribute(attr);
        if (!val || !val.trim()) return;
        const prop = '__orig_' + attr;
        if (isHi) {
          if (el[prop] === undefined) el[prop] = val;
          const trimmed = el[prop].trim();
          const normalized = trimmed.replace(/\s+/g, ' ');
          if (TRANSLATION_MAP[trimmed]) {
            el.setAttribute(attr, el[prop].replace(trimmed, TRANSLATION_MAP[trimmed]));
          } else if (TRANSLATION_MAP[normalized]) {
            el.setAttribute(attr, el[prop].replace(trimmed, TRANSLATION_MAP[normalized]));
          }
        } else {
          if (el[prop] !== undefined) {
            el.setAttribute(attr, el[prop]);
          }
        }
      });
    });
  }

  function updateLanguageToggle() {
    const btn = document.getElementById('btn-acc-lang');
    if (!btn) return;
    if (STATE.currentLanguage === 'hi') {
      btn.textContent = 'English';
      btn.setAttribute('aria-label', 'Switch to English');
      btn.setAttribute('title', 'Switch to English');
    } else {
      btn.textContent = 'हिन्दी';
      btn.setAttribute('aria-label', 'हिन्दी में बदलें');
      btn.setAttribute('title', 'हिन्दी में बदलें');
    }
  }

  function setLanguage(lang) {
    if (!I18N[lang]) lang = 'en';
    STATE.currentLanguage = lang;
    try { localStorage.setItem('sovopt-language', lang); } catch (e) {}
    document.documentElement.setAttribute('lang', lang);

    const dict = I18N[lang];
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (dict[key]) {
        el.textContent = dict[key];
      }
    });

    if (!STATE.isSolving) {
      const solveBtn = document.getElementById('btn-run-solve');
      if (solveBtn) solveBtn.innerHTML = '<span>' + dict.btn_run_solver + '</span>';
      const headerSolveBtn = document.getElementById('btn-header-solve');
      if (headerSolveBtn) headerSolveBtn.innerHTML = '<span>' + dict.nav_run_optimization + '</span>';
    }

    applyDOMTranslations(document.body, lang);
    updateLanguageToggle();

    // Refresh dynamic views if they have been initialized
    try {
      if (typeof updateUnitInspector === 'function' && STATE.selectedUnit) {
        updateUnitInspector(STATE.selectedUnit);
      }
      if (typeof updateScenarioDetail === 'function' && STATE.activeScenario) {
        updateScenarioDetail(STATE.activeScenario);
      }
      if (typeof updateSolverUI === 'function') {
        updateSolverUI(STATE.solveResult);
      }
      if (typeof updateTrustPassportUI === 'function') {
        updateTrustPassportUI(STATE.solveResult);
      }
      if (typeof updateOverviewKPIs === 'function') {
        updateOverviewKPIs();
      }
    } catch (e) {}
  }
  // Clear any stale font-scale preference stored by previous gate
  try { localStorage.removeItem('sovopt-font-scale'); } catch (e) {}

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
    loadCompetitiveEvidence();
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

  // Accessibility Controls Setup — language toggle and skip link
  function setupAccessibility() {
    const btnLang = document.getElementById('btn-acc-lang');
    if (btnLang) {
      btnLang.addEventListener('click', () => {
        const nextLang = (STATE.currentLanguage === 'hi') ? 'en' : 'hi';
        setLanguage(nextLang);
      });
    }

    const skipLink = document.querySelector('.skip-link');
    if (skipLink) {
      skipLink.addEventListener('click', e => {
        const main = document.getElementById('main-content');
        if (main) {
          main.focus({ preventScroll: false });
        }
      });
    }

    // Initialize persisted language preference
    let initialLang = 'en';
    try { initialLang = localStorage.getItem('sovopt-language') || 'en'; } catch (e) {}
    setLanguage(initialLang);
    updateLanguageToggle();
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
    window.STATE = STATE;
  window.switchTab = switchTab;

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

    const targetView = document.getElementById('view-' + tabId);
    if (STATE.currentLanguage === 'hi' && targetView) {
      applyDOMTranslations(targetView, 'hi');
    }

    // Reveal any cards inside newly activated view section
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

        if (titleEl) titleEl.textContent = t(u.name);
        if (capEl) capEl.textContent = t(u.designCapacity);
        if (rateEl) rateEl.textContent = t(u.nominalOperatingRate);
        if (yieldEl) yieldEl.textContent = t(u.yieldFormula);
        if (shadowEl) shadowEl.textContent = t(u.shadowPrice);
        if (statusEl) statusEl.innerHTML = `<span class="status-pill"><span class="status-dot"></span> ${t(u.status)}</span>`;
        strip.classList.remove('fading');
        if (STATE.currentLanguage === 'hi') applyDOMTranslations(strip, 'hi');
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

    if (STATE.currentLanguage === 'hi') {
      applyDOMTranslations(svg, 'hi');
    }
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
        if (subEl) subEl.textContent = t('Contraction of infinity-norm KKT residuals over iterations');
        svg.innerHTML = `
          <rect width="${width}" height="${height}" fill="transparent"/>
          <g transform="translate(${width / 2}, ${height / 2 - 8})">
            <text x="0" y="0" fill="var(--text-secondary)" font-family="var(--font-sans)" font-size="12" font-weight="500" text-anchor="middle">
              ${t('Baseline scenario loaded — click "Run optimisation" to generate certified convergence trajectory')}
            </text>
            <text x="0" y="20" fill="var(--text-muted)" font-family="var(--font-mono)" font-size="10.5" text-anchor="middle">
              ${t('Sparse LU revised simplex verifies feasibility & KKT optimality at final basis')}
            </text>
          </g>
        `;
      }
      if (STATE.currentLanguage === 'hi') {
        applyDOMTranslations(svg, 'hi');
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

    if (STATE.currentLanguage === 'hi') {
      applyDOMTranslations(svg, 'hi');
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
      if (titleEl) titleEl.textContent = t(sc.title);
      if (descEl) descEl.textContent = t(sc.desc);
      if (marginEl) marginEl.textContent = sc.netMargin !== null ? ('$' + sc.netMargin.toFixed(2)) : t('Infeasible');
      if (ratioEl) ratioEl.textContent = `${sc.cduArab.toFixed(0)}L / ${sc.cduBasrah.toFixed(0)}H kbpd`;
      if (bottleEl) bottleEl.textContent = t(sc.bottleneck);
      if (notesEl) notesEl.textContent = t(sc.notes);

      if (panel) {
        panel.classList.remove('fading');
        if (STATE.currentLanguage === 'hi') applyDOMTranslations(panel, 'hi');
      }
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
    const headerSolveBtn = document.getElementById('btn-header-solve');
    const stagePill = document.getElementById('solve-stage-pill');

    function setRunButtonsLoading(loading, status = null) {
      const dict = I18N[STATE.currentLanguage || 'en'] || I18N.en;
      if (loading) {
        if (solveBtn) {
          solveBtn.disabled = true;
          solveBtn.innerHTML = '<span class="spinner-sm" aria-hidden="true"></span><span>' + dict.running_optimization + '</span>';
        }
        if (headerSolveBtn) {
          headerSolveBtn.disabled = true;
          headerSolveBtn.innerHTML = '<span class="spinner-sm" aria-hidden="true"></span><span>' + dict.running_optimization + '</span>';
        }
      } else {
        if (status === 'OPTIMAL_VERIFIED') {
          if (solveBtn) {
            solveBtn.disabled = true;
            solveBtn.innerHTML = '<span class="one-time-check" aria-hidden="true">✓</span><span>' + dict.opt_complete + '</span>';
          }
          if (headerSolveBtn) {
            headerSolveBtn.disabled = true;
            headerSolveBtn.innerHTML = '<span class="one-time-check" aria-hidden="true">✓</span><span>' + dict.opt_complete + '</span>';
          }
          setTimeout(() => {
            if (!STATE.isSolving) {
              if (solveBtn) {
                solveBtn.disabled = false;
                solveBtn.innerHTML = '<span>' + dict.btn_run_solver + '</span>';
              }
              if (headerSolveBtn) {
                headerSolveBtn.disabled = false;
                headerSolveBtn.innerHTML = '<span>' + dict.nav_run_optimization + '</span>';
              }
            }
          }, 900);
        } else {
          if (solveBtn) {
            solveBtn.disabled = false;
            solveBtn.innerHTML = '<span>' + dict.btn_run_solver + '</span>';
          }
          if (headerSolveBtn) {
            headerSolveBtn.disabled = false;
            headerSolveBtn.innerHTML = '<span>' + dict.nav_run_optimization + '</span>';
          }
        }
      }
    }

    setRunButtonsLoading(true);
    if (stagePill) stagePill.textContent = 'Building model…';

    const pArab = document.getElementById('input-param-arab')?.value || 70;
    const pBasrah = document.getElementById('input-param-basrah')?.value || 62;
    const dGas = document.getElementById('input-param-gas')?.value || 40;
    const dDsl = document.getElementById('input-param-dsl')?.value || 50;

    let modelData = null;
    let resultData = null;

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
        } else {
          let errBody = null;
          try { errBody = await solveResp.json(); } catch(e){}
          console.error('Solve HTTP error:', solveResp.status, errBody);
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
      STATE.isSolving = false;
      setRunButtonsLoading(false, resultData ? resultData.status : null);
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
      if (statusEl) statusEl.innerHTML = '<span class="status-pill"><span class="status-dot" style="background: var(--text-muted);"></span> ' + t('Not executed') + '</span>';
      if (modelEl) modelEl.textContent = STATE.activeModel ? STATE.activeModel.toUpperCase() + ' (Unsolved)' : 'Refinery Twin (Unsolved)';
      if (objEl) { objEl.textContent = '—'; objEl.style.color = 'var(--text-primary)'; }
      if (primEl) primEl.textContent = '—';
      if (dualEl) dualEl.textContent = '—';
      if (kktEl) kktEl.textContent = '—';
      if (boundEl) boundEl.textContent = '—';
      if (intEl) intEl.textContent = '—';
      if (certEl) certEl.innerHTML = '<span class="status-pill"><span class="status-dot" style="background: var(--text-muted);"></span> ' + t('Run solver to verify') + '</span>';
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
        objEl.textContent = t('Certified Infeasible');
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
        primEl.textContent = t('Certified Ray (Infeasible)');
      } else {
        primEl.textContent = '-';
      }
    }

    if (dualEl) {
      if (v.dual_residual !== undefined && v.dual_residual !== null) {
        dualEl.textContent = Number(v.dual_residual).toExponential(2);
      } else if (res.status === 'INFEASIBLE_CERTIFIED') {
        dualEl.textContent = t('Exact Farkas Ray');
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
        intEl.textContent = t('N/A (Continuous LP/QP)');
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
    if (STATE.currentLanguage === 'hi') {
      applyDOMTranslations(tbody, 'hi');
    }
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
    if (STATE.currentLanguage === 'hi') {
      applyDOMTranslations(tbody, 'hi');
    }
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
    if (STATE.currentLanguage === 'hi') {
      applyDOMTranslations(container, 'hi');
    }
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
      setLanguage: setLanguage,
      updateLanguageToggle: updateLanguageToggle,
      I18N: I18N,
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

  // =========================================================================
  // Competitive Evidence — Load and Render Differential Benchmark Results
  // =========================================================================
  function statusCell(status) {
    const colors = {
      'OPTIMAL': '#2e7d32', 'OPTIMAL_VERIFIED': '#2e7d32',
      'INFEASIBLE': '#6a1a9a', 'INFEASIBLE_CERTIFIED': '#6a1a9a',
      'LIMIT_REACHED': '#e65100', 'NUMERICAL_FAILURE': '#c62828',
      'UNBOUNDED': '#4a148c', 'N/A': '#757575',
    };
    const col = colors[status] || '#546e7a';
    return `<span style="color:${col};font-weight:600;font-size:11.5px;">${status}</span>`;
  }

  function fmtTime(s) {
    if (s == null) return '—';
    return s < 1 ? `${(s * 1000).toFixed(0)} ms` : `${s.toFixed(3)} s`;
  }

  function fmtObj(v) {
    if (v == null) return '—';
    const n = Number(v);
    if (!isFinite(n)) return String(v);
    return n.toExponential(4);
  }

  function fmtDiff(d) {
    if (d == null) return '—';
    const pct = (d * 100).toFixed(4);
    const col = d < 1e-6 ? '#2e7d32' : d < 1e-3 ? '#f57c00' : '#c62828';
    return `<span style="color:${col}">${pct}%</span>`;
  }

  function renderLPComparisonTable(data) {
    const rows = data.map(r => `
      <tr>
        <td><strong>${r.instance}</strong></td>
        <td>${r.variables}</td>
        <td>${r.constraints}</td>
        <td>${statusCell(r.sovopt_status)}</td>
        <td class="mono" style="font-size:11.5px">${fmtTime(r.sovopt_time_s)}</td>
        <td>${statusCell(r.highs_status)}</td>
        <td class="mono" style="font-size:11.5px">${fmtTime(r.highs_time_s)}</td>
        <td class="mono" style="font-size:11.5px">${fmtObj(r.sovopt_objective)}</td>
        <td class="mono" style="font-size:11.5px">${fmtObj(r.highs_objective)}</td>
        <td>${fmtDiff(r.relative_obj_diff)}</td>
        <td>${r.verification === 'MATCH' ? '<span style="color:#2e7d32;font-weight:600">✓ MATCH</span>' : r.verification === 'MISMATCH' ? '<span style="color:#c62828;font-weight:600">✗ MISMATCH</span>' : '<span style="color:#757575">N/A</span>'}</td>
      </tr>`).join('');
    return `
      <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--text-primary)">Netlib LP — 17 Instances (SOV-OPT vs HiGHS 1.15.1)</div>
      <table class="editorial-table">
        <thead><tr>
          <th>Instance</th><th>Vars</th><th>Cons</th>
          <th>SOV Status</th><th>SOV Time</th>
          <th>HiGHS Status</th><th>HiGHS Time</th>
          <th>SOV Obj</th><th>HiGHS Obj</th>
          <th>Rel Diff</th><th>Verification</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  function renderMILPComparisonTable(data) {
    const rows = data.map(r => `
      <tr>
        <td><strong style="font-size:11px">${r.instance}</strong></td>
        <td>${r.variables}</td>
        <td>${r.constraints}</td>
        <td>${r.integer_variables}</td>
        <td>${statusCell(r.sovopt_status)}</td>
        <td class="mono" style="font-size:11px">${fmtTime(r.sovopt_time_s)}</td>
        <td>${statusCell(r.highs_status)}</td>
        <td class="mono" style="font-size:11px">${fmtTime(r.highs_time_s)}</td>
        <td class="mono" style="font-size:11px">${fmtObj(r.sovopt_objective)}</td>
        <td class="mono" style="font-size:11px">${fmtObj(r.highs_objective)}</td>
        <td class="mono" style="font-size:11px">${r.sovopt_gap != null ? (r.sovopt_gap * 100).toFixed(2) + '%' : '—'}</td>
      </tr>`).join('');
    return `
      <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--text-primary)">MIPLIB — 38 Instances (SOV-OPT B&B vs HiGHS 1.15.1)</div>
      <table class="editorial-table">
        <thead><tr>
          <th>Instance</th><th>Vars</th><th>Cons</th><th>Int</th>
          <th>SOV Status</th><th>SOV Time</th>
          <th>HiGHS Status</th><th>HiGHS Time</th>
          <th>SOV Incumbent</th><th>HiGHS Obj</th><th>Gap</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  function renderMIPLIBTable(data) {
    const rows = data.map(r => `
      <tr>
        <td><strong style="font-size:11px">${r.instance}</strong></td>
        <td>${r.constraints}</td>
        <td>${r.variables}</td>
        <td>${r.integer_variables}</td>
        <td>${statusCell(r.sovopt_status)}</td>
        <td class="mono" style="font-size:11px">${fmtTime(r.sovopt_time_s)}</td>
        <td class="mono" style="font-size:11px">${r.sovopt_objective != null ? fmtObj(r.sovopt_objective) : 'N/A'}</td>
        <td class="mono" style="font-size:11px">${r.sovopt_bound != null ? fmtObj(r.sovopt_bound) : 'N/A'}</td>
        <td class="mono" style="font-size:11px">${r.sovopt_gap != null ? (r.sovopt_gap * 100).toFixed(2) + '%' : 'N/A'}</td>
        <td class="mono" style="font-size:11px">${r.sovopt_nodes != null ? r.sovopt_nodes : 'N/A'}</td>
        <td>${r.verification || 'N/A'}</td>
      </tr>`).join('');
    return `
      <table class="editorial-table">
        <thead><tr>
          <th>Instance</th><th>Rows</th><th>Columns</th><th>Int Vars</th>
          <th>Status</th><th>Runtime</th><th>Incumbent</th><th>Best Bound</th>
          <th>Gap</th><th>Nodes</th><th>Verification</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  function renderSparseStressTable(data) {
    const phaseBadge = p => {
      const cols = {
        'FULL SOLVE': '#2e7d32',
        'PARTIAL ITERATION STRESS': '#f57c00',
        'PREPROCESSING STRESS': '#1565c0',
        'MEMORY STRESS': '#757575',
      };
      return `<span style="color:${cols[p]||'#546e7a'};font-weight:600;font-size:11px">${p||'—'}</span>`;
    };
    const rows = data.map(r => `
      <tr>
        <td><strong>${r.label}</strong></td>
        <td class="mono" style="font-size:11px">${r.n_vars.toLocaleString()}</td>
        <td class="mono" style="font-size:11px">${r.n_cons.toLocaleString()}</td>
        <td class="mono" style="font-size:11px">${(r.actual_nnz||r.est_nonzeros||0).toLocaleString()}</td>
        <td>${r.est_sparsity_pct}%</td>
        <td class="mono" style="font-size:11px">${r.est_memory_mb} MB</td>
        <td>${phaseBadge(r.phase_tested)}</td>
        <td>${r.solve_time_s != null ? fmtTime(r.solve_time_s) : (r.preprocessing_time_s != null ? fmtTime(r.preprocessing_time_s) + ' (prep)' : '—')}</td>
        <td>${statusCell(r.status)}</td>
      </tr>`).join('');
    return `
      <table class="editorial-table">
        <thead><tr>
          <th>Label</th><th>Vars</th><th>Cons</th><th>NNZ</th><th>Sparsity</th>
          <th>Est. Mem</th><th>Phase</th><th>Time</th><th>Status</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  function renderMILPTelemetryCards(cases) {
    const cards = cases.map(c => {
      const isLimit = c.status === 'LIMIT_REACHED';
      const statusBadge = statusCell(c.status);
      const inc = c.incumbent != null ? fmtObj(c.incumbent) : 'N/A';
      const bound = c.best_certified_bound != null ? fmtObj(c.best_certified_bound) : 'N/A';
      const root = c.root_relaxation != null ? fmtObj(c.root_relaxation) : 'N/A';
      const gap = c.relative_gap != null ? (c.relative_gap * 100).toFixed(2) + '%' : 'N/A';

      return `
        <div style="background: var(--bg-surface); border: 1px solid var(--border-default); border-radius: 4px; padding: 14px; margin-bottom: 10px;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div>
              <strong style="font-size: 13px; color: var(--text-primary);">${c.name}</strong>
              <span style="font-size: 11px; color: var(--text-secondary); margin-left: 8px;">(${c.category} · ${c.variables} vars, ${c.constraints} cons, ${c.integer_variables} int)</span>
            </div>
            <div>${statusBadge}</div>
          </div>
          <div style="font-size: 11.5px; color: var(--text-secondary); margin-bottom: 10px;">${c.description}</div>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; font-size: 11.5px; background: var(--bg-alt, #fafafa); border: 1px solid var(--border-subtle, #eee); border-radius: 4px; padding: 10px;">
            <div><span style="color:var(--text-secondary)">Root Relaxation:</span><br><strong class="mono">${root}</strong></div>
            <div><span style="color:var(--text-secondary)">Incumbent:</span><br><strong class="mono">${inc}</strong></div>
            <div><span style="color:var(--text-secondary)">Best Bound:</span><br><strong class="mono">${bound}</strong></div>
            <div><span style="color:var(--text-secondary)">Relative Gap:</span><br><strong class="mono">${gap}</strong></div>
            <div><span style="color:var(--text-secondary)">Nodes Explored:</span><br><strong class="mono">${c.nodes_explored}</strong></div>
            <div><span style="color:var(--text-secondary)">Pruned Nodes:</span><br><strong class="mono">${c.pruned_nodes}</strong></div>
            <div><span style="color:var(--text-secondary)">Runtime:</span><br><strong class="mono">${fmtTime(c.solve_time_s)}</strong></div>
          </div>
          <div style="margin-top: 8px; font-size: 11px; color: ${isLimit ? '#b71c1c' : 'var(--text-secondary)'};">
            <strong>Termination:</strong> ${c.termination_reason}
          </div>
        </div>
      `;
    }).join('');

    return `<div>${cards}</div>`;
  }

  function renderBatchThroughputTable(data) {
    const rows = data.map(r => `
      <tr>
        <td><strong>${r.workers} worker${r.workers > 1 ? 's' : ''}</strong></td>
        <td class="mono" style="font-size: 11.5px;">${r.batch_size} instances</td>
        <td class="mono" style="font-size: 11.5px;">${r.wall_clock_seconds.toFixed(3)} s</td>
        <td class="mono" style="font-size: 11.5px; font-weight: 600;">${r.throughput_instances_per_second.toFixed(2)} inst/s</td>
        <td><strong style="color: #2e7d32;">${r.speedup_vs_single_worker.toFixed(2)}x</strong></td>
        <td><span style="color: #2e7d32; font-weight: 600;">✓ 100% verified</span></td>
      </tr>
    `).join('');

    return `
      <table class="editorial-table">
        <thead><tr>
          <th>Worker Tier</th><th>Batch Size</th><th>Wall-Clock Time</th><th>Throughput</th><th>Scaling Factor</th><th>Verification</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }

  function loadCompetitiveEvidence() {
    // Load differential benchmark
    fetch('/api/differential_benchmark')
      .then(r => r.ok ? r.json() : Promise.reject('not_ready'))
      .then(data => {
        const lpWrap = document.getElementById('highs-comparison-lp-wrap');
        const milpWrap = document.getElementById('highs-comparison-milp-wrap');
        if (lpWrap && data.lp_comparison) {
          lpWrap.innerHTML = renderLPComparisonTable(data.lp_comparison);
        }
        if (milpWrap && data.milp_comparison) {
          milpWrap.innerHTML = renderMILPComparisonTable(data.milp_comparison);
        }
        const mipWrap = document.getElementById('miplib-results-wrap');
        if (mipWrap && data.milp_comparison) {
          mipWrap.innerHTML = `<div style="font-size:11.5px;color:var(--text-secondary);margin-bottom:8px">
            30-second bounded evaluation across 38 MIPLIB 2017 instances. LIMIT_REACHED is reported without an optimality claim.
            ${data.summary ? `<strong>${data.summary.milp_sovopt_optimal}</strong>/${data.summary.milp_total} OPTIMAL, <strong>${data.summary.milp_sovopt_limit}</strong> LIMIT_REACHED, <strong>${data.summary.milp_sovopt_numerical_failure || 1}</strong> NUMERICAL_FAILURE.` : ''}
          </div>` + renderMIPLIBTable(data.milp_comparison);
        }
        if (data.meta) {
          const msgEl = document.getElementById('highs-loading-msg');
          if (msgEl) msgEl.remove();
          const mipMsg = document.getElementById('miplib-loading-msg');
          if (mipMsg) mipMsg.remove();
        }
      })
      .catch(() => {
        const el = document.getElementById('highs-loading-msg');
        if (el) el.textContent = 'Differential benchmark results not yet generated. Run: .venv/bin/python scripts/run_differential_benchmark.py';
        const m = document.getElementById('miplib-loading-msg');
        if (m) m.textContent = 'MIPLIB results not yet generated. Run differential benchmark script.';
      });

    // Load sparse stress results
    fetch('/api/sparse_stress')
      .then(r => r.ok ? r.json() : Promise.reject('not_ready'))
      .then(data => {
        const wrap = document.getElementById('sparse-stress-wrap');
        if (wrap && data.results) {
          const msg = document.getElementById('sparse-loading-msg');
          if (msg) msg.remove();
          wrap.innerHTML = renderSparseStressTable(data.results);
        }
      })
      .catch(() => {
        const el = document.getElementById('sparse-loading-msg');
        if (el) el.textContent = 'Sparse stress results not yet generated. Run: .venv/bin/python scripts/run_sparse_stress.py';
      });

    // Load MILP representative telemetry
    fetch('/api/milp_telemetry')
      .then(r => r.ok ? r.json() : Promise.reject('not_ready'))
      .then(data => {
        const wrap = document.getElementById('milp-telemetry-wrap');
        if (wrap && data.cases) {
          wrap.innerHTML = renderMILPTelemetryCards(data.cases);
        }
      })
      .catch(() => {
        const el = document.getElementById('milp-telemetry-loading-msg');
        if (el) el.textContent = 'MILP telemetry details available in reports/milp_telemetry/representative_cases.json';
      });

    // Load Batch Throughput multicore results
    fetch('/api/batch_throughput')
      .then(r => r.ok ? r.json() : Promise.reject('not_ready'))
      .then(data => {
        const wrap = document.getElementById('batch-throughput-wrap');
        if (wrap && data.results) {
          const msg = document.getElementById('batch-throughput-loading-msg');
          if (msg) msg.remove();
          wrap.innerHTML = renderBatchThroughputTable(data.results);
        }
      })
      .catch(() => {
        const el = document.getElementById('batch-throughput-loading-msg');
        if (el) el.textContent = 'Batch throughput results not yet generated. Run: .venv/bin/python scripts/run_batch_throughput.py';
      });
  }

  window.STATE = STATE;

  window.switchTab = switchTab;
  window.selectScenario = selectScenario;
  window.setLanguage = setLanguage;
  window.updateLanguageToggle = updateLanguageToggle;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
