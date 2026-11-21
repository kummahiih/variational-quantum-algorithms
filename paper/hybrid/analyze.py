"""Summarize paired policy runs and rebuild the figures for the follow-up paper."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
METRICS = ["loss", "hit20", "hitcap", "gain", "pilot_calls", "used_calls"]
STARTERS = ("original", "recursive", "halton", "sobol", "random",
            "original_coordinate", "recursive_coordinate")
INK, GRID = "#203447", "#dbe3e8"
TEAL, ORANGE, INDIGO, BLUE, GRAY = "#007568", "#af4f22", "#695895", "#28619a", "#546674"


def tables(raw, out):
    raw["loss"] = raw.first_hit.fillna(raw.budget + 1)
    raw["hit20"] = raw.first_hit.le(20)
    raw["hitcap"] = raw.first_hit.notna()
    gap = raw.initial_energy - raw.grid_min
    raw["gain"] = (raw.initial_energy - raw.final_energy) / gap
    if (gap <= 1e-10).any():
        raise ValueError("normalized gain is undefined for a grid-optimal start")
    # Average seeds within a start, then starts within a graph.
    by_start = raw.groupby(["split", "case", "stratum", "start", "starter", "policy"])[METRICS].mean()
    by_graph = by_start.groupby(["split", "case", "stratum", "starter", "policy"]).mean()
    summary = by_graph.groupby(["split", "starter", "policy"]).mean()
    summary["graphs"] = by_graph.groupby(["split", "starter", "policy"]).size()
    summary["runs"] = raw.groupby(["split", "starter", "policy"]).size()
    summary.to_csv(out / "summary.csv", float_format="%.9f")
    selected = []
    for starter in STARTERS:
        legacy = summary.loc["legacy", starter]
        candidates = [(float(row.loss), int(label[1:])) for label, row in legacy.iterrows()
                      if label.startswith("k") and 1 < int(label[1:]) < 65]
        loss, k = min(candidates)  # smaller k breaks ties
        holdout = summary.loc["holdout", starter, f"k{k}"]
        selected.append((starter, k, loss, holdout.loss, holdout.hitcap))
    pd.DataFrame(selected, columns=["starter","calibration_k","calibration_loss",
        "holdout_loss","holdout_hitcap"]).to_csv(out / "calibrated_splits.csv", index=False)
    return by_graph, summary


def manuscript_tables(summary, out):
    labels = {"pattern":"Immediate pattern search","halton":"Halton","random":"Random",
              "sobol":"Sobol","original":"Original, joint","recursive":"Recursive, joint",
              "original_coordinate":"Original, coordinate","recursive_coordinate":"Recursive, coordinate"}
    main_rows = []
    for starter in ("halton","random","sobol","original","recursive","original_coordinate",
                    "recursive_coordinate","pattern"):
        a = summary.loc["holdout", starter, "k1" if starter == "pattern" else "k13"]
        main_rows.append(f"{labels[starter]} & {100*a.hit20:.1f} & {100*a.hitcap:.1f} & "
                         f"{a.loss:.2f} & {100*a.gain:.1f} & {a.used_calls:.1f}" + r" \\")
    decisions = []
    for starter, pol, name in (("pattern","k1","Immediate pattern search"),
            ("halton","k8","Fixed 8"), ("halton","k13","Fixed 13"), ("halton","k33","Fixed 33"),
            ("halton","k65","Halton only"), ("halton","patience4","Four-call patience"),
            ("halton","checkpoint","Learned 8 or 13")):
        a = summary.loc["confirmation", starter, pol]
        decisions.append(f"{name} & {a.pilot_calls:.1f} & {round(72*a.hit20)} & {round(72*a.hitcap)} "
                         f"& {a.loss:.2f} & {a.used_calls:.1f}" + r" \\")
    body = ""
    for cmd, rows in (("StarterRows", main_rows), ("DecisionRows", decisions)):
        body += "\\newcommand{\\" + cmd + "}{%\n" + "\n".join(rows) + "\n}\n"
    (out / "paper_tables.tex").write_text(body, encoding="utf-8")


def paired_intervals(by_graph, out):
    pairs = [(("halton", "k13"), ("pattern", "k1")),
             (("halton", "k13"), ("halton", "k65")),
             (("halton", "k33"), ("halton", "k13")),
             (("halton", "k33"), ("halton", "k65")),
             (("recursive", "k13"), ("pattern", "k1"))]
    for m in STARTERS:
        pairs.extend([((m, "patience4"), (m, "k13")), ((m, "checkpoint"), (m, "k13"))])
    rows = []
    for split in ("holdout", "confirmation"):
        frame = by_graph.loc[split]
        for (a, pa), (b, pb) in pairs:
            left = frame.xs((a, pa), level=("starter", "policy"))
            right = frame.xs((b, pb), level=("starter", "policy"))
            delta = (left - right).sort_index(level=["stratum", "case"])
            if delta.isna().any().any() or len(delta) != 24:
                raise ValueError("incomplete graph pairing")
            rng = np.random.default_rng(20261121)
            boots = np.zeros((10000, len(METRICS)))
            for _, sub in delta.groupby("stratum"):
                x = sub.to_numpy()
                sample = rng.integers(len(x), size=(10000, len(x)))
                boots += x[sample].sum(axis=1) / len(delta)
            lo, hi = np.quantile(boots, [0.025, 0.975], axis=0)
            for j, metric in enumerate(METRICS):
                rows.append((split, a, pa, b, pb, metric, delta[metric].mean(), lo[j], hi[j]))
    pd.DataFrame(rows, columns=["split","starter_a","policy_a","starter_b","policy_b",
        "metric","a_minus_b","lower95","upper95"]).to_csv(out / "paired.csv", index=False,
                                                           float_format="%.9f")


def style(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.tick_params(length=0, pad=4, colors=INK)
    for side in ("top","right","left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#a4b1b8")


def save(fig, dest):
    fig.savefig(dest, bbox_inches="tight", pad_inches=0.05,
                metadata={"Creator":"Hybrid QAOA study","CreationDate":None,"ModDate":None})
    plt.close(fig)


def figures(raw, summary, directory, out):
    directory.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size":9, "font.family":"DejaVu Sans", "text.color":INK,
        "axes.labelcolor":INK, "axes.titlesize":10, "pdf.fonttype":42})
    historic = pd.read_csv(out / "historical_crossover.csv")
    fig, ax = plt.subplots(figsize=(6.65, 2.15), layout="constrained")
    style(ax)
    ax.axvspan(13, 14, color="#dae9e7", zorder=0)
    for col, title, color, line in (("original","Original coordinate sieve",ORANGE,"-"),
            ("recursive","Recursive coordinate sieve",INDIGO,"--"),("pattern","Pattern search",TEAL,"-")):
        ax.step(historic.evaluation, historic[col], where="post", color=color,
                linestyle=line, linewidth=1.8, label=title)
    ax.set(xlim=(1,20.25), ylim=(-0.2,15.8), xticks=[1,5,8,10,13,14,17,20],
           yticks=[0,5,10,15], xlabel="Charged energy calls", ylabel="Cases reaching target (of 15)")
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    save(fig, directory / "crossover.pdf")

    fig, ax = plt.subplots(figsize=(6.65, 2.6), layout="constrained")
    style(ax)
    ax.axvline(13, color="#81929c", linestyle=":", linewidth=1)
    base = summary.loc["holdout", "pattern", "k1"].loss
    styles = (("recursive","Recursive joint",ORANGE,"-"),("sobol","Sobol",INDIGO,":"),
              ("random","Random",GRAY,"-."),("recursive_coordinate","Recursive coordinate",BLUE,"--"),
              ("halton","Halton",TEAL,"-"))
    for starter, label, color, ls in styles:
        sub = summary.loc["holdout", starter]
        early = [base] + [sub.loc[f"k{k}","loss"] for k in range(2,27)]
        ax.plot(range(1,27), early, ls, c=color, linewidth=1.5, label=label)
        late = (33, 49, 65)
        ax.scatter(late, [sub.loc[f"k{k}","loss"] for k in late], s=17, color=color)
    ax.set(xlim=(0,67), xticks=[1,8,13,20,26,33,49,65], xlabel="Pilot calls, including initialization",
           ylabel="Mean capped time to target")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.50,1.22), ncol=3, fontsize=8)
    save(fig, directory / "switch_sweep.pdf")

    fig, ax = plt.subplots(figsize=(6.65, 2.6), layout="constrained")
    style(ax)
    runs = raw[(raw.split=="confirmation") & (raw.starter=="halton")]
    for policy, label, color, ls in (("k33","33-call pilot",TEAL,"-"),("k13","13-call pilot",BLUE,"-"),
            ("checkpoint","Learned 8/13",INDIGO,"--"),("patience4","Four-call patience",ORANGE,"-.")):
        vals = runs.loc[runs.policy==policy,"first_hit"]
        x = np.arange(1,66)
        ax.step(x, [100*vals.le(t).mean() for t in x], where="post",
                c=color, ls=ls, linewidth=1.7, label=label)
    ax.set(xlim=(1,65), ylim=(-1,103), xticks=[1,8,13,20,28,40,50,65],
           yticks=[0,25,50,75,100], xlabel="Charged energy calls", ylabel="Cases reaching target (%)")
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    save(fig, directory / "confirmation.pdf")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=HERE/"results")
    parser.add_argument("--figures", type=Path, default=HERE/"figures")
    args = parser.parse_args()
    raw = pd.read_csv(args.results/"runs.csv.gz")
    by_graph, summary = tables(raw, args.results)
    manuscript_tables(summary, args.results)
    paired_intervals(by_graph, args.results)
    figures(raw, summary, args.figures, args.results)


if __name__ == "__main__":
    main()
