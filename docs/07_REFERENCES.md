# Inputs and implementation references

## User-provided inputs

- `description(2).docx`: MRPL PS 26119, indigenous GPU-accelerated optimization core, with LP/MILP/QP, numerical robustness and benchmarking requirements.
- `Final Deep-Research Solution for MRPL PS 26119_ A Verified Sovereign GPU-Accelerated LP_MILP_QP Solv(1)(2).pdf`: architectural and sixteen-week research blueprint.

The requirements were read from these files. Their proposed features are not evidence that those features have been implemented. Copies of the attachments are not duplicated in this source ZIP. The source mapping and hashes are in `reports/source_inputs.json`.

## Primary references

- PDHG/PDLP foundations: https://arxiv.org/abs/2106.04756
- Mehrotra, On the Implementation of a Primal-Dual Interior Point Method: https://doi.org/10.1137/0802028
- Koberstein, The Dual Simplex Method, Techniques for a Fast and Stable Implementation: https://digital.ub.uni-paderborn.de/hsmig/content/titleinfo/3885
- Neumaier and Shcherbina, Safe bounds in linear and mixed-integer linear programming: https://doi.org/10.1007/s10107-003-0433-3
- Python virtual environments: https://docs.python.org/3/tutorial/venv.html
- CuPy installation: https://docs.cupy.dev/en/stable/install.html
- NVIDIA Linux CUDA installation: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html
- Official MIPLIB downloads: https://miplib.zib.de/download.html
- Official Netlib LP data: https://www.netlib.org/lp/data/
- Official QPLIB: https://qplib.zib.de/

The references establish mathematical background and future work; the code is not a full reproduction of any cited industrial algorithm. The PDHG, installation and benchmark repository links were checked while preparing this package. No current commercial-solver feature or comparative superiority claim is needed for this release.

## Dependency boundary

Core: Python standard library and NumPy 2.3.5. NumPy supplies arrays, vector operations and platform arithmetic; the core does not call NumPy optimization functions or linear-system solvers. Optional CUDA: CuPy/runtime, with original CSR kernel source. External benchmark: SciPy 1.17.0/HiGHS in a separate process. Web: Python standard library plus HTML/CSS/JavaScript with no CDN assets, external fonts or analytics.

This is software-algorithm sovereignty at the prototype level, not independence from foreign hardware, compilers, operating systems or all numerical dependencies. Review licences and choose your own project distribution licence before publishing a repository; this ZIP does not bundle third-party dependency source or dataset archives.
