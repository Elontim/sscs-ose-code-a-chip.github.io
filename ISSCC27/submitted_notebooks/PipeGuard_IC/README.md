# PipeGuard-IC

**An Open-Source Self-Calibrating Programmable Analog Front End for Edge Pipeline-Leak Monitoring**

PipeGuard-IC is an ISSCC 2027 IEEE SSCS Code-a-Chip submission in development. It explores a reproducible, notebook-driven analog front end for conditioning weak vibration or acoustic signals before ADC sampling and edge inference.

## Why this project

Pipeline-monitoring nodes need to detect weak signatures while rejecting pump vibration, electrical interference, and sensor noise. Sending raw high-rate data also wastes energy. PipeGuard-IC moves useful signal conditioning into a low-power, tunable analog front end and connects it to an edge classifier.

## Proposed signal chain

1. piezoelectric sensor-equivalent model,
2. SKY130 low-noise differential input stage,
3. programmable gain,
4. tunable band-pass filtering,
5. ADC-ready output,
6. Python-driven simulation, optimization, and verification.

## Repository map

- `PipeGuard_IC.ipynb` — executable design narrative and analytical baseline
- `models/piezo_sensor_model.spice` — parameterized passive piezo model
- `circuits/sky130_lna.spice` — first-pass SKY130 amplifier core
- `circuits/testbench_dc.spice` — DC operating-point testbench
- `circuits/testbench_ac.spice` — differential AC testbench
- `circuits/testbench_bias_sweep.spice` — tail-bias feasibility sweep
- `circuits/testbench_noise.spice` — input/output noise-density analysis
- `circuits/testbench_transient.spice` — small-signal time-domain and power test
- `scripts/run_ngspice.py` — model discovery and reproducible batch runner
- `scripts/analyze_spice.py` — result validation, summary, and AC plot
- `results/` — generated data, logs, summaries, and plots

## Reproduce the current work

### Python analytical notebook

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook PipeGuard_IC.ipynb
```

### SKY130/ngspice circuit checks

Install ngspice and an open_pdks SKY130A installation, then run from this project directory:

```bash
python scripts/run_ngspice.py --analysis all
python scripts/analyze_spice.py
```

The runner checks `PDK_ROOT`, `SKY130_ROOT`, and common system paths. An explicit library can be supplied:

```bash
python scripts/run_ngspice.py --model-lib /absolute/path/to/sky130.lib.spice
```

A run is reported as passing only when ngspice exits successfully and produces a non-empty expected data file.

## Evidence status

| Evidence | Status |
|---|---|
| Reproducible synthetic sensor stimulus | Implemented |
| Analytical filter/SNR exploration | Implemented |
| Parameterized piezo sensor model | Implemented; parameters are assumptions pending measurement |
| SKY130 transistor netlist | Implemented; exploratory first iteration |
| DC, AC, bias, noise and transient testbenches | Implemented |
| Verified transistor-level results | Pending execution with ngspice + SKY130 PDK |
| Noise, transient, distortion, PVT and mismatch | Planned |
| Layout | Planned |

No fabricated-silicon performance is claimed. Analytical targets and circuit simulation results are labeled separately.

## Planned open-source stack

- Jupyter Notebook / Google Colab
- Python, NumPy, SciPy, pandas, Matplotlib
- ngspice and Xschem
- SKY130 open PDK
- optional gLayout/KLayout physical-design exploration

## Team

- **Ayoola Timilehin Israel** — Mechatronics Engineering; system definition, Python automation, embedded/edge integration, and documentation
- Additional collaborators: to be confirmed

## Licence

Apache License 2.0. See `LICENSE`.
