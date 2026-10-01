# Quarantined Datasets — SOV-OPT

This directory holds candidate optimization instances that are quarantined from the active, verified benchmark suite because their historical application provenance has not been established through primary literature.

## AVGAS (Aviation Gasoline Blending LP)

- **Files:** avgas.mps, avgas.json
- **File Source:** HiGHS public test suite repository (check/instances/avgas.mps)
- **MPS SHA-256:** 10d0e68381321ee9b6a22a53a33d07f7740070b0a077a78ef742a9e88eca8213
- **Claimed Historical Attribution:** Charnes, Cooper, and Mellon (1952), "Blending Aviation Gasolines — A Study in Programming Interdependent Activities", Econometrica 20(2): 135–159; and Symonds (1955), Linear Programming in the Petroleum Industry, F. J. Maingot.
- **Quarantine Reason:** While the repository source and hash are verified, the direct correspondence between the exact 8-variable, 10-constraint matrix in avgas.mps and the primary text in Charnes (1952) or Symonds (1955) has not been independently verified against primary literature in this project.
- **Status:** Quarantined from the active verified real-application benchmark suite. Not labeled as synthetic, but excluded from active performance claims, default demonstrations, and verification suites until primary evidence is confirmed.
