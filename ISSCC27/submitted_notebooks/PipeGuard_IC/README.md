# PipeGuard-IC

**An Open-Source Self-Calibrating Programmable Analog Front End for Edge Pipeline-Leak Monitoring**

PipeGuard-IC is an ISSCC 2027 IEEE SSCS Code-a-Chip submission in development. The project explores a reproducible, notebook-driven analog front-end workflow for conditioning weak vibration or acoustic signals before ADC sampling and edge inference.

## Project objective

The intended signal chain combines:

1. a sensor-equivalent input model,
2. a low-noise input stage,
3. programmable gain,
4. tunable band-pass filtering,
5. an ADC-ready output,
6. Python-driven simulation, optimization, and verification.

## Current status

Phase 1 scaffold. No fabricated-silicon performance is claimed. Circuit-level results will be added only after reproducible ngspice validation.

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
