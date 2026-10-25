"""Batch ECG -> RR intervals -> HRV pipeline (SAMPLE PROJECT, public data only).

Data: PhysioNet Fantasia database (Iyengar et al., 1996), 20 young + 20 elderly
healthy subjects, ECG at 250 Hz. Streams the needed segment straight from PhysioNet.

Steps per record:
  1. Load a 10-min ECG segment (minutes 5-15, skipping the settling period)
  2. Clean (NeuroKit2 default filter) and detect R-peaks with artifact correction
  3. Score signal quality; flag the record if mean quality < QUALITY_MIN
  4. Export RR intervals and compute time- and frequency-domain HRV
Then compare groups with Mann-Whitney U tests and save tables + figures.

Run:  python pipeline.py            (outputs land in ./output)
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator
import neurokit2 as nk
import numpy as np
import pandas as pd
import wfdb
from scipy import stats

FS = 250
START_MIN, DURATION_MIN = 5, 10
QUALITY_MIN = 0.5
OUT = Path(__file__).parent / "output"
FIG = OUT / "figures"
RR_DIR = OUT / "rr_intervals"
CACHE = Path(__file__).parent / "data_cache"
ECTOPIC_JUMP = 0.20  # successive RR change > 20% counts as an ectopic-like beat
ECTOPIC_MAX_PCT = 5.0  # sensitivity analysis drops records above this

RECORDS = [f"f{s}{g}{i:02d}" for g in ("y", "o") for s in (1, 2) for i in range(1, 11)]

# Figure style: neutral ink, recessive grid, two validated categorical slots
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
GROUP_COLOR = {"Young": "#2a78d6", "Elderly": "#eb6834"}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "figure.dpi": 150, "savefig.bbox": "tight", "figure.facecolor": "white",
})


def load_segment(record):
    cached = CACHE / f"{record}.npz"
    if cached.exists():
        d = np.load(cached)
        return d["ecg"], int(d["age"]), str(d["sex"])
    start = START_MIN * 60 * FS
    rec = wfdb.rdrecord(record, pn_dir="fantasia", sampfrom=start,
                        sampto=start + DURATION_MIN * 60 * FS)
    ecg = rec.p_signal[:, rec.sig_name.index("ECG")]
    age = int(rec.comments[0].split()[1])
    sex = rec.comments[0].split()[-1]
    CACHE.mkdir(exist_ok=True)
    np.savez_compressed(cached, ecg=ecg, age=age, sex=sex)
    return ecg, age, sex


def process(record):
    ecg, age, sex = load_segment(record)
    if np.isnan(ecg).any():
        ecg = pd.Series(ecg).interpolate(limit_direction="both").to_numpy()
    clean = nk.ecg_clean(ecg, sampling_rate=FS)
    _, info = nk.ecg_peaks(clean, sampling_rate=FS, correct_artifacts=True)
    peaks = info["ECG_R_Peaks"]
    quality = float(np.nanmean(nk.ecg_quality(clean, rpeaks=peaks, sampling_rate=FS)))

    rr_ms = np.diff(peaks) / FS * 1000
    ectopic_pct = 100 * np.mean(np.abs(np.diff(rr_ms)) / rr_ms[:-1] > ECTOPIC_JUMP)
    pd.DataFrame({"r_peak_sample": peaks[1:], "rr_ms": rr_ms}).to_csv(
        RR_DIR / f"{record}_rr.csv", index=False)

    hrv = pd.concat([nk.hrv_time(peaks, sampling_rate=FS),
                     nk.hrv_frequency(peaks, sampling_rate=FS, normalize=False)], axis=1)
    row = {
        "record": record, "group": "Young" if "y" in record else "Elderly",
        "age": age, "sex": sex, "n_beats": len(peaks), "quality": round(quality, 3),
        "flag_low_quality": quality < QUALITY_MIN,
        "ectopic_like_pct": round(ectopic_pct, 2), "mean_hr_bpm": 60000 / rr_ms.mean(),
    }
    for col in ("HRV_MeanNN", "HRV_SDNN", "HRV_RMSSD", "HRV_pNN50", "HRV_LF", "HRV_HF", "HRV_LFHF"):
        row[col.replace("HRV_", "")] = float(hrv[col].iloc[0])
    return row, clean, peaks


def compare_groups(df):
    rows = []
    young, old = df[df.group == "Young"], df[df.group == "Elderly"]
    for m in ("mean_hr_bpm", "SDNN", "RMSSD", "pNN50", "LF", "HF", "LFHF"):
        u, p = stats.mannwhitneyu(young[m], old[m], alternative="two-sided")
        rows.append({
            "metric": m, "young_median": young[m].median(), "elderly_median": old[m].median(),
            "U": u, "p_value": p,
            "rank_biserial_r": 1 - 2 * u / (len(young) * len(old)),
        })
    out = pd.DataFrame(rows)
    # Holm correction across the 7 tests
    order = out.p_value.argsort().to_numpy()
    adj = np.empty(len(out))
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, out.p_value.iloc[i] * (len(out) - rank)))
        adj[i] = running
    out["p_holm"] = adj
    return out


def fig_example(clean, peaks, record):
    secs = 6
    t = np.arange(secs * FS) / FS
    p = peaks[peaks < secs * FS]
    fig, ax = plt.subplots(figsize=(8, 2.6))
    ax.plot(t, clean[: secs * FS], color=INK_2, lw=1)
    ax.scatter(p / FS, clean[p], s=36, color=GROUP_COLOR["Young"], zorder=3,
               edgecolor="white", linewidth=1.5)
    ax.set(xlabel="Time (s)", ylabel="ECG (mV)",
           title=f"Cleaned ECG, blue dots = detected R-peaks (record {record})")
    fig.savefig(FIG / "01_ecg_rpeaks.png")
    plt.close(fig)


def fig_tachograms(examples):
    fig, ax = plt.subplots(figsize=(8, 3))
    for group, (record, peaks) in examples.items():
        rr = np.diff(peaks) / FS * 1000
        ax.plot(peaks[1:] / FS / 60, rr, color=GROUP_COLOR[group], lw=1.2,
                label=f"{group} ({record})")
    ax.set(xlabel="Time in segment (min)", ylabel="RR interval (ms)",
           title="Example RR tachograms: one young vs one elderly subject")
    ax.legend(frameon=False, loc="upper right", ncol=2)
    fig.savefig(FIG / "02_tachograms.png")
    plt.close(fig)


def fig_groups(df, comp):
    metrics = [("RMSSD", "RMSSD (ms)"), ("SDNN", "SDNN (ms)"), ("HF", "HF power (ms²)")]
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.4))
    rng = np.random.default_rng(0)
    for ax, (m, label) in zip(axes, metrics):
        for x, group in enumerate(("Young", "Elderly")):
            vals = df.loc[df.group == group, m].to_numpy()
            ax.scatter(x + rng.uniform(-0.12, 0.12, len(vals)), vals, s=30,
                       color=GROUP_COLOR[group], edgecolor="white", linewidth=1.2, zorder=3)
            ax.hlines(np.median(vals), x - 0.25, x + 0.25, color=INK, lw=2, zorder=4)
        p = comp.loc[comp.metric == m, "p_holm"].iloc[0]
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(plt.NullFormatter())
        ax.set_xticks([0, 1], ["Young", "Elderly"])
        ax.set_xlim(-0.5, 1.5)
        ax.set_title(f"{label}\nHolm-adjusted p = {p:.1g}", fontsize=10)
    fig.suptitle("HRV by age group (each dot = 1 subject, bar = median, log scale)",
                 color=INK, fontsize=11, fontweight="bold", y=1.1)
    fig.savefig(FIG / "03_group_comparison.png")
    plt.close(fig)


def main():
    for d in (OUT, FIG, RR_DIR):
        d.mkdir(parents=True, exist_ok=True)
    rows, examples = [], {}
    for rec in RECORDS:
        row, clean, peaks = process(rec)
        rows.append(row)
        print(f"{rec}: {row['n_beats']} beats, quality {row['quality']}, RMSSD {row['RMSSD']:.1f} ms")
        if rec == "f1y01":
            fig_example(clean, peaks, rec)
        if rec in ("f1y01", "f1o01"):
            examples["Young" if "y" in rec else "Elderly"] = (rec, peaks)

    df = pd.DataFrame(rows)
    df.round(3).to_csv(OUT / "hrv_per_subject.csv", index=False)
    analysed = df[~df.flag_low_quality]
    comp = compare_groups(analysed)
    comp.to_csv(OUT / "group_comparison.csv", index=False, float_format="%.4g")

    sensitivity = compare_groups(analysed[analysed.ectopic_like_pct <= ECTOPIC_MAX_PCT])
    sensitivity.to_csv(OUT / "group_comparison_sensitivity.csv", index=False, float_format="%.4g")

    fig_tachograms(examples)
    fig_groups(analysed, comp)
    print(f"\nFlagged low-quality: {df.flag_low_quality.sum()} / {len(df)}")
    print(comp.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    dropped = analysed[analysed.ectopic_like_pct > ECTOPIC_MAX_PCT].record.tolist()
    print(f"\nSensitivity analysis without {dropped}:")
    print(sensitivity.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
