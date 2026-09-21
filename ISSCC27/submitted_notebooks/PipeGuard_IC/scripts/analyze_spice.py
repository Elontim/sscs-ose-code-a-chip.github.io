#!/usr/bin/env python3
"""Validate and summarize PipeGuard-IC ngspice outputs."""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def load_numeric(path: Path) -> np.ndarray:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Missing result: {path}. Run scripts/run_ngspice.py first.")
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        try:
            values = [float(field) for field in fields]
        except ValueError:
            continue
        if values:
            rows.append(values)
    if not rows:
        raise ValueError(f"No numeric rows found in {path}")
    width = min(map(len, rows))
    return np.asarray([row[:width] for row in rows], dtype=float)


def main() -> int:
    try:
        dc = load_numeric(RESULTS / "dc_operating_point.dat")
        ac = load_numeric(RESULTS / "ac_response.dat")
        if ac.shape[1] < 3:
            raise ValueError("AC output needs frequency, magnitude, and phase columns.")

        # wrdata may repeat the scale before each requested vector.
        frequency = ac[:, 0]
        magnitude_db = ac[:, -2]
        phase_deg = ac[:, -1]
        valid = np.isfinite(frequency) & np.isfinite(magnitude_db) & (frequency > 0)
        frequency, magnitude_db, phase_deg = frequency[valid], magnitude_db[valid], phase_deg[valid]
        if frequency.size < 2:
            raise ValueError("AC output contains too few valid points.")

        peak_index = int(np.argmax(magnitude_db))
        peak_db = float(magnitude_db[peak_index])
        cutoff_mask = magnitude_db >= peak_db - 3.0
        bandwidth_points = frequency[cutoff_mask]
        summary = pd.DataFrame({
            "metric": ["DC output (last numeric value)", "Peak gain", "Peak-gain frequency",
                       "Approx. -3 dB lower frequency", "Approx. -3 dB upper frequency"],
            "value": [float(dc[-1, -2] if dc.shape[1] >= 2 else dc[-1, -1]), peak_db,
                      float(frequency[peak_index]), float(bandwidth_points[0]),
                      float(bandwidth_points[-1])],
            "unit": ["V", "dB", "Hz", "Hz", "Hz"],
        })
        summary.to_csv(RESULTS / "summary.csv", index=False)

        fig, ax = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
        ax[0].semilogx(frequency, magnitude_db, color="#0B4F6C", lw=2)
        ax[0].axhline(peak_db - 3, color="#FF7F11", ls="--", lw=1)
        ax[0].set_ylabel("Gain (dB)")
        ax[1].semilogx(frequency, phase_deg, color="#01BAEF", lw=2)
        ax[1].set(xlabel="Frequency (Hz)", ylabel="Phase (deg)")
        for axis in ax:
            axis.grid(True, which="both", alpha=0.25)
        fig.suptitle("PipeGuard-IC SKY130 AC response")
        fig.tight_layout()
        fig.savefig(RESULTS / "ac_response.png", dpi=180)
        print(summary.to_string(index=False))
        print("Wrote results/summary.csv and results/ac_response.png")
        return 0
    except (FileNotFoundError, ValueError, IndexError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
