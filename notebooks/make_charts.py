import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from src.pipeline import run_exchange, get_expected_qber, using_stubs

RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
LEVELS = np.round(np.arange(0.0, 1.01, 0.1), 2)
TRIALS = 10  # lower this if real Qiskit runs are slow


def sweep(levels=LEVELS, trials=TRIALS, seed=42):
    """Run run_exchange over noise levels, with and without Eve."""
    rng = np.random.default_rng(seed)
    rows = []
    for eve in (False, True):
        for lv in levels:
            for _ in range(trials):
                r = run_exchange(float(lv), eve, rng=rng)
                rows.append({"noise": float(lv), "eve": eve, "qber": r["qber"],
                             "verdict": r["verdict"],
                             "key_len": r["final_key_len"]})
    return pd.DataFrame(rows)


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(RESULTS / name, dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_qber_vs_noise(df):
    d = df[~df.eve].groupby("noise").qber.agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(d.noise, d["mean"], yerr=d["std"], marker="o", capsize=3,
                label="Observed QBER (no Eve)")
    ax.plot(d.noise, [get_expected_qber(x) for x in d.noise], "--",
            label="Expected QBER (noise profile)")
    ax.axhline(0.11, color="red", ls=":", label="11% BB84 limit")
    ax.set_xlabel("Noise level")
    ax.set_ylabel("QBER")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_title("QBER vs noise")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)
    ax.grid(alpha=0.3)
    _save(fig, "qber_vs_noise.png")


def chart_eve_vs_clean(df):
    g = df.groupby(["noise", "eve"]).qber.mean().unstack()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(g.index, g[False], marker="o", label="No Eve")
    ax.plot(g.index, g[True], marker="s", color="crimson",
            label="Intercept-resend Eve")
    ax.axhline(0.11, color="red", ls=":", label="11% BB84 limit")
    ax.axhline(0.25, color="gray", ls="--", lw=1, label="25% ideal Eve")
    ax.set_xlabel("Noise level")
    ax.set_ylabel("QBER")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_title("QBER with and without Eve")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)
    ax.grid(alpha=0.3)
    _save(fig, "qber_with_without_eve.png")


def chart_key_length(df):
    g = df.groupby(["noise", "eve"]).key_len.mean().unstack()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(g.index, g[False], marker="o", label="No Eve (key kept)")
    ax.plot(g.index, g[True], marker="s", color="crimson",
            label="Eve (key discarded)")
    ax.set_xlabel("Noise level")
    ax.set_ylabel("Final key length (bits)")
    ax.set_title("Key length vs noise")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)
    ax.grid(alpha=0.3)
    _save(fig, "key_length_vs_noise.png")


if __name__ == "__main__":
    df = sweep()
    df.to_csv(RESULTS / "sweep.csv", index=False)
    chart_qber_vs_noise(df)
    chart_eve_vs_clean(df)
    chart_key_length(df)
    print("rows:", len(df), "| stubbed:", using_stubs())
    print("saved:", sorted(p.name for p in RESULTS.glob("*.png")))


