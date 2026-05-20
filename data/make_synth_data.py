"""Generate synthetic LC-MS assay run / QC data as CSV."""

import argparse
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

FIELDNAMES = [
    "assay_run_id",
    "run_date",
    "analyte",
    "matrix",
    "instrument_id",
    "sample_type",
    "level",
    "replicate",
    "nominal_conc_ng_ml",
    "back_calc_conc_ng_ml",
    "peak_area_ratio",
    "dilution_factor",
    "bias_pct",
    "within_acceptance",
]

ANALYTE = "CompoundX"
MATRIX = "Human plasma"
INSTRUMENTS = ["LCMS-01", "LCMS-02", "LCMS-03"]

CAL_LEVELS = [f"CAL{i}" for i in range(1, 9)]
CAL_NOMINALS = [0.5, 1.0, 2.5, 10.0, 25.0, 100.0, 250.0, 500.0]

QC_LEVELS = ["LLOQ", "LQC", "MQC", "HQC"]
QC_NOMINALS = {"LLOQ": 0.5, "LQC": 2.5, "MQC": 25.0, "HQC": 250.0}
QC_REPLICATES = 3

ACCEPTANCE = {"LLOQ": 20.0, "LQC": 15.0, "MQC": 15.0, "HQC": 15.0}


def _conc_to_area(nominal: float, drift: float, noise_scale: float, rng: random.Random) -> float:
    log_nom = math.log10(max(nominal, 1e-6))
    base = 0.15 + 0.18 * log_nom + drift
    noise = rng.gauss(0, noise_scale)
    return max(0.001, base + noise)


def _back_calc(nominal: float, bias_frac: float, rng: random.Random) -> float:
    noise = rng.lognormvariate(0, 0.03)
    return max(0.0, nominal * (1 + bias_frac) * noise)


def _bias_pct(nominal: float, back_calc: float) -> str:
    if nominal <= 0:
        return ""
    return f"{((back_calc - nominal) / nominal) * 100:.2f}"


def _within_acceptance(level: str, bias_pct_val: float | None) -> str:
    if bias_pct_val is None:
        return ""
    limit = ACCEPTANCE.get(level, 15.0)
    return "Y" if abs(bias_pct_val) <= limit else "N"


def _base_row(
    assay_run_id: str,
    run_date: str,
    instrument_id: str,
    sample_type: str,
    level: str,
    replicate: int,
) -> dict:
    return {
        "assay_run_id": assay_run_id,
        "run_date": run_date,
        "analyte": ANALYTE,
        "matrix": MATRIX,
        "instrument_id": instrument_id,
        "sample_type": sample_type,
        "level": level,
        "replicate": str(replicate),
        "nominal_conc_ng_ml": "",
        "back_calc_conc_ng_ml": "",
        "peak_area_ratio": "",
        "dilution_factor": "1",
        "bias_pct": "",
        "within_acceptance": "",
    }


def build_injection_rows(
    run_index: int,
    rng: random.Random,
    include_failures: bool,
    base_date: date,
) -> list[dict]:
    run_date = (base_date + timedelta(days=run_index)).isoformat()
    assay_run_id = f"RUN-{run_date.replace('-', '')}-{run_index + 1:03d}"
    instrument_id = INSTRUMENTS[run_index % len(INSTRUMENTS)]
    drift = rng.uniform(-0.04, 0.04)
    rows: list[dict] = []

    for cal_level, nominal in zip(CAL_LEVELS, CAL_NOMINALS):
        row = _base_row(assay_run_id, run_date, instrument_id, "CAL", cal_level, 1)
        back_calc = _back_calc(nominal, rng.uniform(-0.02, 0.02), rng)
        row["nominal_conc_ng_ml"] = f"{nominal:.4f}"
        row["back_calc_conc_ng_ml"] = f"{back_calc:.4f}"
        row["peak_area_ratio"] = f"{_conc_to_area(nominal, drift, 0.01, rng):.4f}"
        row["bias_pct"] = _bias_pct(nominal, back_calc)
        rows.append(row)

    failure_slots: set[tuple[str, int]] = set()
    if include_failures:
        fail_level = rng.choice(QC_LEVELS)
        fail_rep = rng.randint(1, QC_REPLICATES)
        failure_slots.add((fail_level, fail_rep))

    for qc_level, nominal in QC_NOMINALS.items():
        for rep in range(1, QC_REPLICATES + 1):
            row = _base_row(assay_run_id, run_date, instrument_id, "QC", qc_level, rep)
            if (qc_level, rep) in failure_slots:
                bias_frac = rng.choice([-1, 1]) * rng.uniform(0.22, 0.35)
            else:
                bias_frac = rng.uniform(-0.08, 0.08)
            back_calc = _back_calc(nominal, bias_frac, rng)
            bias_val = ((back_calc - nominal) / nominal) * 100
            dilution = "10" if qc_level == "HQC" and rep == 1 and rng.random() < 0.3 else "1"
            row["nominal_conc_ng_ml"] = f"{nominal:.4f}"
            row["back_calc_conc_ng_ml"] = f"{back_calc:.4f}"
            row["peak_area_ratio"] = f"{_conc_to_area(nominal, drift, 0.02, rng):.4f}"
            row["dilution_factor"] = dilution
            row["bias_pct"] = f"{bias_val:.2f}"
            row["within_acceptance"] = _within_acceptance(qc_level, bias_val)
            rows.append(row)

    for i in range(1, 3):
        row = _base_row(assay_run_id, run_date, instrument_id, "BLK", "BLK", i)
        back_calc = rng.uniform(0, 0.02)
        row["back_calc_conc_ng_ml"] = f"{back_calc:.4f}"
        row["peak_area_ratio"] = f"{rng.uniform(0.001, 0.01):.4f}"
        rows.append(row)

    row = _base_row(assay_run_id, run_date, instrument_id, "DBL", "DBL", 1)
    back_calc = rng.uniform(0, 0.01)
    row["back_calc_conc_ng_ml"] = f"{back_calc:.4f}"
    row["peak_area_ratio"] = f"{rng.uniform(0.001, 0.005):.4f}"
    rows.append(row)

    return rows


def generate_runs(
    num_runs: int,
    seed: int,
    include_failures: bool,
) -> list[dict]:
    rng = random.Random(seed)
    base_date = date(2026, 5, 20)
    rows: list[dict] = []
    for i in range(num_runs):
        rows.extend(build_injection_rows(i, rng, include_failures, base_date))
    return rows


def write_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic LC-MS assay run / QC CSV data."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/synth/qc_runs.csv"),
        help="Output CSV path (default: data/synth/qc_runs.csv)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of assay runs to simulate (default: 5)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--include-failures",
        action="store_true",
        help="Force some QC rows outside acceptance limits",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.runs < 1:
        raise SystemExit("--runs must be at least 1")
    rows = generate_runs(args.runs, args.seed, args.include_failures)
    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
