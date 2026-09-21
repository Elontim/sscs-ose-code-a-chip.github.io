#!/usr/bin/env python3
"""Run PipeGuard-IC SKY130 testbenches reproducibly.

The script locates the open_pdks SKY130 ngspice library, replaces the
explicit model placeholder in each testbench, and runs ngspice in batch mode.
It never reports a successful circuit result unless ngspice exits cleanly and
the expected data file exists.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CIRCUITS = PROJECT_ROOT / "circuits"
RESULTS = PROJECT_ROOT / "results"
MODEL_TOKEN = "__SKY130_MODEL_LIBRARY__"
TESTBENCHES = {
    "dc": (CIRCUITS / "testbench_dc.spice", RESULTS / "dc_operating_point.dat"),
    "ac": (CIRCUITS / "testbench_ac.spice", RESULTS / "ac_response.dat"),
}


def find_model_library(explicit: str | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    for variable in ("PDK_ROOT", "SKY130_ROOT"):
        root = os.environ.get(variable)
        if root:
            base = Path(root).expanduser()
            candidates.extend([
                base / "sky130A/libs.tech/ngspice/sky130.lib.spice",
                base / "libs.tech/ngspice/sky130.lib.spice",
            ])
    candidates.extend([
        Path("/usr/share/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice"),
        Path.home() / ".volare/sky130/versions",
    ])
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
        if candidate.is_dir():
            matches = sorted(candidate.glob("*/sky130A/libs.tech/ngspice/sky130.lib.spice"))
            if matches:
                return matches[-1].resolve()
    raise FileNotFoundError(
        "SKY130 ngspice model not found. Set PDK_ROOT or SKY130_ROOT, "
        "or pass --model-lib /absolute/path/to/sky130.lib.spice."
    )


def run_one(name: str, template: Path, expected: Path, model_lib: Path) -> None:
    text = template.read_text(encoding="utf-8")
    if MODEL_TOKEN not in text:
        raise RuntimeError(f"Model placeholder missing in {template}")
    generated = RESULTS / f"{template.stem}.generated.spice"
    generated.write_text(text.replace(MODEL_TOKEN, model_lib.as_posix()), encoding="utf-8")
    log = RESULTS / f"{name}_ngspice.log"
    command = ["ngspice", "-b", "-o", str(log), str(generated)]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"ngspice failed for {name}; inspect {log}")
    if not expected.is_file() or expected.stat().st_size == 0:
        raise RuntimeError(f"ngspice produced no expected data file: {expected}")
    print(f"[PASS] {name}: {expected.relative_to(PROJECT_ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", choices=["dc", "ac", "all"], default="all")
    parser.add_argument("--model-lib")
    args = parser.parse_args()

    if shutil.which("ngspice") is None:
        print("ERROR: ngspice is not installed or not on PATH.", file=sys.stderr)
        return 2

    RESULTS.mkdir(exist_ok=True)
    try:
        model_lib = find_model_library(args.model_lib)
        selected = TESTBENCHES if args.analysis == "all" else {args.analysis: TESTBENCHES[args.analysis]}
        print(f"Using SKY130 model library: {model_lib}")
        for name, (template, expected) in selected.items():
            run_one(name, template, expected, model_lib)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
