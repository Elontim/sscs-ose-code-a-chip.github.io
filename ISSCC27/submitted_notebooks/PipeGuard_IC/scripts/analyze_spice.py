#!/usr/bin/env python3
"""Validate, summarize, and plot PipeGuard-IC ngspice outputs."""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def load_numeric(name: str, required: bool = True) -> np.ndarray | None:
    path = RESULTS / name
    if not path.is_file() or path.stat().st_size == 0:
        if required:
            raise FileNotFoundError(f"Missing result: {path}. Run scripts/run_ngspice.py first.")
        return None
    rows: list[list[float]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            values = [float(field) for field in line.split()]
        except ValueError:
            continue
        if values:
            rows.append(values)
    if not rows:
        raise ValueError(f"No numeric rows found in {path}")
    width = min(map(len, rows))
    return np.asarray([row[:width] for row in rows], dtype=float)


def add_metric(rows: list[dict], metric: str, value: float, unit: str, source: str) -> None:
    rows.append({"metric": metric, "value": value, "unit": unit, "source": source})


def main() -> int:
    try:
        dc = load_numeric("dc_operating_point.dat")
        ac = load_numeric("ac_response.dat")
        if dc is None or ac is None or ac.shape[1] < 3:
            raise ValueError("DC/AC outputs are incomplete.")

        rows: list[dict] = []
        dc_output = float(dc[-1, -2] if dc.shape[1] >= 2 else dc[-1, -1])
        add_metric(rows, "DC output", dc_output, "V", "dc_operating_point.dat")

        frequency = ac[:, 0]
        magnitude_db, phase_deg = ac[:, -2], ac[:, -1]
        valid = np.isfinite(frequency) & np.isfinite(magnitude_db) & (frequency > 0)
        frequency, magnitude_db, phase_deg = frequency[valid], magnitude_db[valid], phase_deg[valid]
        if frequency.size < 2:
            raise ValueError("AC output contains too few valid points.")
        peak_index = int(np.argmax(magnitude_db))
        peak_db = float(magnitude_db[peak_index])
        band = frequency[magnitude_db >= peak_db - 3.0]
        add_metric(rows, "Peak small-signal gain", peak_db, "dB", "ac_response.dat")
        add_metric(rows, "Peak-gain frequency", float(frequency[peak_index]), "Hz", "ac_response.dat")
        add_metric(rows, "Approx. -3 dB lower frequency", float(band[0]), "Hz", "ac_response.dat")
        add_metric(rows, "Approx. -3 dB upper frequency", float(band[-1]), "Hz", "ac_response.dat")

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
        plt.close(fig)

        bias = load_numeric("bias_sweep.dat", required=False)
        if bias is not None and bias.shape[1] >= 3:
            vbias, vout, supply_current = bias[:, 0], bias[:, -2], np.abs(bias[:, -1])
            valid_bias = (vout > 0.2) & (vout < 1.6) & np.isfinite(supply_current)
            if np.any(valid_bias):
                candidates = np.flatnonzero(valid_bias)
                selected = int(candidates[np.argmin(supply_current[valid_bias])])
                add_metric(rows, "Lowest-current valid bias candidate", float(vbias[selected]), "V", "bias_sweep.dat")
                add_metric(rows, "Candidate supply current", float(supply_current[selected]), "A", "bias_sweep.dat")
            fig, ax1 = plt.subplots(figsize=(8, 4.5))
            ax1.plot(vbias, vout, color="#0B4F6C", label="Output voltage")
            ax1.set(xlabel="Tail-bias voltage (V)", ylabel="Output voltage (V)")
            ax2 = ax1.twinx()
            ax2.plot(vbias, supply_current * 1e6, color="#FF7F11", label="Supply current")
            ax2.set_ylabel("Supply current (µA)")
            ax1.grid(alpha=0.25)
            fig.tight_layout()
            fig.savefig(RESULTS / "bias_sweep.png", dpi=180)
            plt.close(fig)

        noise = load_numeric("noise_response.dat", required=False)
        if noise is not None and noise.shape[1] >= 3:
            nf, onoise, inoise = noise[:, 0], np.abs(noise[:, -2]), np.abs(noise[:, -1])
            mask = (nf >= 300) & (nf <= 8000) & np.isfinite(inoise)
            if np.count_nonzero(mask) >= 2:
                integrated = float(np.sqrt(np.trapz(inoise[mask] ** 2, nf[mask])))
                add_metric(rows, "Integrated input noise, 300 Hz–8 kHz", integrated, "V_rms", "noise_response.dat")
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.loglog(nf, inoise, label="Input-referred", color="#0B4F6C")
            ax.loglog(nf, onoise, label="Output", color="#01BAEF", alpha=0.8)
            ax.set(xlabel="Frequency (Hz)", ylabel="Noise density (V/√Hz)")
            ax.grid(True, which="both", alpha=0.25)
            ax.legend()
            fig.tight_layout()
            fig.savefig(RESULTS / "noise_response.png", dpi=180)
            plt.close(fig)

        transient = load_numeric("transient_response.dat", required=False)
        if transient is not None and transient.shape[1] >= 5:
            time = transient[:, 0]
            vin_diff = transient[:, -4] - transient[:, -3]
            vout = transient[:, -2]
            current = np.abs(transient[:, -1])
            settled = time >= time.min() + 0.5 * (time.max() - time.min())
            vin_pp = float(np.ptp(vin_diff[settled]))
            vout_pp = float(np.ptp(vout[settled]))
            if vin_pp > 0:
                add_metric(rows, "Transient voltage gain", 20 * np.log10(vout_pp / vin_pp), "dB", "transient_response.dat")
            add_metric(rows, "Average simulated power", 1.8 * float(np.mean(current[settled])), "W", "transient_response.dat")
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.plot(time * 1e3, vin_diff * 1e3, label="Differential input (mV)", color="#01BAEF")
            ax.plot(time * 1e3, vout, label="Output (V)", color="#0B4F6C")
            ax.set(xlabel="Time (ms)", ylabel="Amplitude")
            ax.grid(alpha=0.25)
            ax.legend()
            fig.tight_layout()
            fig.savefig(RESULTS / "transient_response.png", dpi=180)
            plt.close(fig)

        summary = pd.DataFrame(rows)
        summary.to_csv(RESULTS / "summary.csv", index=False)
        print(summary.to_string(index=False))
        print("Wrote results/summary.csv and available verification plots.")
        return 0
    except (FileNotFoundError, ValueError, IndexError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
