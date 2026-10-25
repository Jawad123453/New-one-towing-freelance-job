"""Validate automatic R-peak detection against expert beat annotations (SAMPLE PROJECT).

Data: PhysioNet MIT-BIH Arrhythmia Database (Moody & Mark, 2001), 48 half-hour
two-lead ambulatory ECGs at 360 Hz, every beat labelled by cardiologists.

For each record, detect R-peaks on lead 1 with three NeuroKit2 detectors and
match them to the reference beats within a 150 ms window (the ANSI/AAMI EC57
convention). Report sensitivity (Se) and positive predictive value (PPV) per
record and overall, and show which records break which detector.

Run:  python validate.py            (outputs land in ./output)
      MITDB_DIR=/path/to/mitdb python validate.py   (faster: read a local copy of the database)
"""
import os
from pathlib import Path

import matplotlib.pyplot as plt
import neurokit2 as nk
import numpy as np
import pandas as pd
import wfdb

FS = 360
TOLERANCE = int(0.150 * FS)
METHODS = ["neurokit", "pantompkins1985", "hamilton2002"]
OUT = Path(__file__).parent / "output"
CACHE = Path(__file__).parent / "data_cache"
# Beat symbols in MIT-BIH that mark real heartbeats (non-beat annotations are excluded)
BEAT_SYMBOLS = set("NLRBAaJSVrFejnE/fQ")

INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
METHOD_COLOR = {"neurokit": "#2a78d6", "pantompkins1985": "#eb6834", "hamilton2002": "#1baf7a"}
METHOD_LABEL = {"neurokit": "NeuroKit2", "pantompkins1985": "Pan-Tompkins", "hamilton2002": "Hamilton"}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "figure.dpi": 150, "savefig.bbox": "tight", "figure.facecolor": "white",
})


def load(record):
    cached = CACHE / f"{record}.npz"
    if cached.exists():
        d = np.load(cached)
        return d["ecg"], d["ref"]
    local = os.environ.get("MITDB_DIR")
    if local:
        rec = wfdb.rdrecord(os.path.join(local, record), channels=[0])
        ann = wfdb.rdann(os.path.join(local, record), "atr")
    else:
        rec = wfdb.rdrecord(record, pn_dir="mitdb", channels=[0])
        ann = wfdb.rdann(record, "atr", pn_dir="mitdb")
    ref = np.array([s for s, sym in zip(ann.sample, ann.symbol) if sym in BEAT_SYMBOLS])
    ecg = rec.p_signal[:, 0]
    CACHE.mkdir(exist_ok=True)
    np.savez_compressed(cached, ecg=ecg, ref=ref)
    return ecg, ref


def match(detected, reference):
    """Greedy one-to-one matching within the tolerance window."""
    detected = np.sort(detected)
    used = np.zeros(len(detected), bool)
    tp = 0
    for r in reference:
        lo, hi = np.searchsorted(detected, [r - TOLERANCE, r + TOLERANCE + 1])
        candidates = [i for i in range(lo, hi) if not used[i]]
        if candidates:
            best = min(candidates, key=lambda i: abs(detected[i] - r))
            used[best] = True
            tp += 1
    return tp, len(reference) - tp, len(detected) - tp


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = wfdb.get_record_list("mitdb")
    rows = []
    for record in records:
        ecg, ref = load(record)
        for method in METHODS:
            try:
                clean = nk.ecg_clean(ecg, sampling_rate=FS, method=method)  # each detector with its own preprocessing
                _, info = nk.ecg_peaks(clean, sampling_rate=FS, method=method)
                det = np.asarray(info["ECG_R_Peaks"])
            except Exception as exc:  # a detector failing on a record is itself a finding
                print(f"{record} {method}: failed ({exc})")
                det = np.array([], int)
            tp, fn, fp = match(det, ref)
            rows.append({"record": record, "method": method, "ref_beats": len(ref),
                         "TP": tp, "FN": fn, "FP": fp,
                         "Se": tp / (tp + fn), "PPV": tp / (tp + fp) if tp + fp else 0.0})
        print(record, " ".join(f"{r['method']}: Se {r['Se']:.3f} PPV {r['PPV']:.3f}"
                               for r in rows[-len(METHODS):]))

    df = pd.DataFrame(rows)
    df.round(4).to_csv(OUT / "per_record.csv", index=False)
    totals = df.groupby("method")[["TP", "FN", "FP"]].sum()
    totals["Se"] = totals.TP / (totals.TP + totals.FN)
    totals["PPV"] = totals.TP / (totals.TP + totals.FP)
    totals["F1"] = 2 * totals.Se * totals.PPV / (totals.Se + totals.PPV)
    totals = totals.loc[METHODS]
    totals.round(4).to_csv(OUT / "summary.csv")
    print("\n", totals.round(4).to_string())

    # Figure: only the records where some detector drops below F1 0.99; the rest are summarised
    df["F1"] = 2 * df.Se * df.PPV / (df.Se + df.PPV).replace(0, np.nan)
    min_f1 = df.groupby("record").F1.min()
    hard = min_f1[min_f1 < 0.99].sort_values().index.tolist()
    fig, ax = plt.subplots(figsize=(9, 3.8))
    x = np.arange(len(hard))
    for k, method in enumerate(METHODS):
        f1 = df[df.method == method].set_index("record").loc[hard, "F1"]
        ax.scatter(x + (k - 1) * 0.22, f1, s=40, color=METHOD_COLOR[method], edgecolor="white",
                   linewidth=1.2, zorder=3,
                   label=f"{METHOD_LABEL[method]} (overall F1 {totals.loc[method, 'F1']:.3f})")
    ax.set_xticks(x, hard)
    ax.set(xlabel="MIT-BIH record", ylabel="F1 score",
           title=f"Where detectors disagree: {len(hard)} of {len(min_f1)} records "
                 f"(all detectors score F1 ≥ 0.99 on the other {len(min_f1) - len(hard)})")
    ax.set_ylim(min(0.8, df.F1.min() - 0.03), 1.01)
    ax.legend(frameon=False, loc="lower right")
    fig.savefig(OUT / "f1_hard_records.png")
    plt.close(fig)

    worst = df.sort_values("F1").head(6)
    worst.round(4).to_csv(OUT / "hardest_records.csv", index=False)
    print("\nHardest record/detector pairs:\n", worst.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
