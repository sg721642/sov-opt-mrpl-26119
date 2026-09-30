# GPU validation and deployment

## Mac development

Run CPU LP/MILP/QP and CPU PDHG on the Mac. The included device backend is CUDA, which requires a compatible NVIDIA GPU/runtime. It is not a Metal/MPS implementation and will not accelerate on an Apple Silicon GPU. Do not install CUDA wheels on the Mac hoping they will use Apple graphics.

## NVIDIA Linux experiment

Use an institution workstation or a GPU host you already have permission to use. This package does not rent hardware or create accounts. Before installing packages, confirm the machine has a supported NVIDIA driver and CUDA setup following NVIDIA's official Linux installation guide.

```bash
nvidia-smi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Install the CuPy build matching the available CUDA family, as documented at https://docs.cupy.dev/en/stable/install.html. For an appropriately configured CUDA 12.x environment, the wheel family is:

```bash
python -m pip install cupy-cuda12x
python -c "import cupy; print(cupy.__version__); print(cupy.cuda.runtime.getDeviceCount())"
```

Do not install several CuPy wheel variants together. The optional GPU dependency is not pinned in the CPU requirements because the correct binary package depends on the machine. Record the resolved version and CUDA/driver versions in your experiment. This package's CUDA path was not executed on delivery hardware and may require compatibility fixes.

```bash
python -m sovopt examples/avgas.json --backend pdhg-cuda --output reports/cuda_lp.json
python scripts/compare_gpu.py examples/avgas.json
python -m pip freeze > reports/gpu_environment.txt
nvidia-smi > reports/nvidia_smi.txt
```

`compare_gpu.py` executes both CPU and CUDA PDHG: one cold result and five repeat results per backend. It only computes a speedup if every run passes its numerical gate. The measured total includes setup, transfers, synchronization and CPU verification; it is not a kernel-only time. A small example will likely be overhead-dominated. The script is a hardware gate, not evidence of large-scale speedup.

The current dense input/caps prevent a serious million-variable GPU benchmark. Implement sparse input and scaling gates in the development plan first. No GPU result or acceleration number is pre-populated in this delivery.

## Local network demonstration

Default host is `127.0.0.1`, so only the same computer can connect. For a trusted local network:

```bash
python server.py --host 0.0.0.0 --port 8000
```

Open the host computer's local-network IP address with port 8000 from another machine on that network. Your firewall/network must permit this. This does not create a public internet URL.

## Container deployment

Docker is optional. If installed:

```bash
docker build -t sovopt-demo .
docker run --rm -p 8000:8000 sovopt-demo
```

Open `http://127.0.0.1:8000`. The container includes a CPU runtime, not a CUDA stack. Port configuration is read from the `PORT` environment variable. No source or image has been published on your behalf.

To obtain a public link later, deploy this Dockerfile to a container host supporting a persistent HTTP process, port environment variable and sufficient worker memory. Use `/health` as the health-check path. Provider plans and interfaces change, so follow that provider's current container-deployment documentation rather than assuming a particular free tier exists.

Before sharing a public endpoint, add TLS and authentication/rate limits at the proxy, enforce process/container memory and CPU limits, and keep the demo's request-size, model-size and timeout restrictions. The Python standard-library server is a local prototype service, not a production web stack. It has two worker slots, 200 KB requests, a 30-variable/80-row web cap, a 35-second subprocess deadline, same-origin checks and no file-upload/path-execution API. These restrictions reduce accidental resource use but do not replace production isolation. There is no server-side user-account system, database or persistent experiment store.

## What to share with a judge

Share a running URL only after testing it from a second device. Also preserve the offline source ZIP and an audit JSON in case hosting fails. Never claim the local address `127.0.0.1` is a public link. Do not put confidential refinery inputs on a public demo server.
