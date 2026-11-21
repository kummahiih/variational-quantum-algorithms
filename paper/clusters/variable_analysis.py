"""Analyze the paired variable-size block simulations under their declared size prior."""

from random import Random

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from benchmark_cluster_assumption import (BUDGET, VARIABLE_MODELS, VARIABLE_POLICIES, seed_for)
from cluster_landscapes import place_runs, variable_lengths

LABEL = {"single":"One variable-width block","balanced":"Nearly equal blocks",
         "unequal":"Random unequal blocks","dominant":"One dominant block",
         "isolated":"Guaranteed isolation","uniform":"Uniform subset"}


def variable_intervals(raw, out):
    ident = ["bits","total","planned_runs","rep"]
    wide = raw.set_index(ident+["model","feedback"]).sort_index()
    comparisons = (
        (("dominant","membership","recursive"),("balanced","membership","recursive")),
        (("unequal","membership","recursive"),("balanced","membership","recursive")),
        (("unequal","membership","recursive13"),("unequal","membership","recursive")),
        (("unequal","distance","pattern"),("unequal","membership","pattern")),
    )
    results=[]
    for a,b in comparisons:
        left=wide.xs(a[:2],level=("model","feedback"))[a[2]].fillna(BUDGET+1)
        right=wide.xs(b[:2],level=("model","feedback"))[b[2]].fillna(BUDGET+1)
        for bits,delta in (left-right).groupby(level="bits"):
            x=delta.droplevel("bits").unstack("rep").to_numpy()
            if np.isnan(x).any():
                raise ValueError("incomplete block-law pairing")
            strata,reps=x.shape
            rng=np.random.default_rng(20531121)
            boot=np.empty(10000)
            for i in range(0,10000,200):
                ids=rng.integers(reps,size=(200,strata,reps))
                boot[i:i+200]=x[np.arange(strata)[None,:,None],ids].mean(axis=(1,2))
            lo,hi=np.quantile(boot,[.025,.975])
            results.append((bits,"/".join(a),"/".join(b),x.mean(),lo,hi,strata,reps))
    pd.DataFrame(results,columns=["bits","a","b","capped_calls_a_minus_b","lo95","hi95",
                                 "fixed_width_count_strata","replicates_per_stratum"]
                 ).to_csv(out/"variable_paired.csv",index=False,float_format="%.9f")


def build(out, figs, save, axis_style):
    raw=pd.read_csv(out/"variable_runs.csv.gz")
    frames=[]
    for method in VARIABLE_POLICIES:
        part=raw[["bits","planned_runs","model","feedback"]].copy()
        part["method"]=method
        part["loss"]=raw[method].fillna(BUDGET+1)
        part["hit13"]=raw[method].le(13)
        part["hit65"]=raw[method].notna()
        part["used"]=raw[method+"_used"]
        frames.append(part)
    rows=pd.concat(frames,ignore_index=True)
    # Every width and count stratum has the same number of replicates within each grid.
    cols=["loss","hit13","hit65","used"]
    tab=rows.groupby(["bits","model","feedback","method"])[cols].mean()
    tab.to_csv(out/"variable_summary.csv",float_format="%.9f")
    rows.groupby(["bits","planned_runs","model","feedback","method"])[cols].mean().to_csv(
        out/"variable_by_count.csv",float_format="%.9f")
    geom=raw[raw.feedback=="membership"].copy()
    geom["hit_by_total_deadline"]=geom.recursive_full.le(geom.total_deadline)
    geom["count_bound_within_cap"]=geom.count_deadline.le(BUDGET)
    geom["longest_bound_within_cap"]=geom.longest_deadline.le(BUDGET)
    geometry=geom.groupby(["bits","model"])[["longest_key_run","recursive_full",
        "hit_by_total_deadline","count_bound_within_cap","longest_bound_within_cap"]].mean()
    geometry.to_csv(out/"variable_bounds.csv",float_format="%.9f")
    widths=pd.read_csv(out/"variable_single_exact.csv")
    priors=[]
    for (size,order),g in widths.groupby(["size","order"]):
        priors.append((size,order,int(g.width.min()),int(g.width.max()),int(g.placements.sum()),
                       g["mean"].mean(),np.average(g["mean"],weights=g.placements)))
    pd.DataFrame(priors,columns=["size","order","min_width","max_width","all_placements",
        "mean_uniform_width_then_start","mean_uniform_width_start_pair"]).to_csv(
        out/"variable_width_priors.csv",index=False,float_format="%.9f")
    variable_intervals(raw,out)

    with (out/"variable_tables.tex").open("w",encoding="utf-8") as stream:
        stream.write("\\newcommand{\\VariableRows}{%\n")
        for m in VARIABLE_MODELS:
            sub=tab.loc[4,m]
            values=[sub.loc[f,j].loss for f,j in [("membership","recursive"),("membership","halton"),
                    ("membership","random"),("membership","pattern"),("distance","pattern"),
                    ("membership","recursive13")]]
            stream.write(LABEL[m]+" & "+" & ".join(f"{v:.2f}" for v in values)+r" \\"+"\n")
        stream.write("}\n\\newcommand{\\BoundRows}{%\n")
        for m in VARIABLE_MODELS:
            g=geometry.loc[4,m]
            sub=tab.loc[4,m,"membership"]
            values=[g.hit_by_total_deadline,g.count_bound_within_cap,g.longest_bound_within_cap,
                    sub.loc["recursive"].hit65,sub.loc["recursive13"].hit65]
            stream.write(f"{LABEL[m]} & {g.longest_key_run:.1f} & "+
                         " & ".join(f"{100*v:.1f}" for v in values)+r" \\"+"\n")
        stream.write("}\n")

    figs.mkdir(parents=True,exist_ok=True)
    fig,(a,b)=plt.subplots(2,1,figsize=(6.45,3.65),
                           gridspec_kw={"height_ratios":[1.5,1]},layout="constrained")
    w=widths.query("size==256 and order=='recursive'")
    axis_style(a)
    a.plot(w.width,w["mean"],color="#08776b",lw=2,label="Exact mean, uniform start at each width")
    a.step(w.width,w.deadline,color="#ae5224",lw=1.7,where="post",label="Guaranteed deadline")
    a.set(xlim=(8,32),xticks=[8,12,15,16,20,24,28,32],yticks=[0,8,16,24,32],
          ylabel="Calls to first hit",xlabel="Length of a single solid block")
    a.legend(loc="upper right",fontsize=7.3,frameon=False)
    coordinates=(4,19,4,0)
    anchors=sorted(Random(seed_for("variable-anchors",*coordinates)).sample(range(256-19+1),4))
    labels=[]
    for y,m in enumerate(("balanced","unequal","dominant")):
        rng=Random(seed_for("variable-layout",*coordinates,m))
        lengths=variable_lengths(19,4,m,rng)
        val=sorted(place_runs(256,lengths,anchors))
        b.scatter(val,[y]*len(val),marker="|",s=76,color="#27649d",lw=1.45)
        labels.append(" + ".join(map(str,lengths)))
    b.set(ylim=(2.55,-.55),yticks=[0,1,2],yticklabels=labels,xlim=(0,255),
          xticks=[0,32,64,96,128,160,192,224,255],xlabel="Integer key for three allocations of 19 valid keys")
    b.tick_params(length=0)
    for k in range(0,256,16): b.axvline(k,color="#d9e1e5",lw=.7,zorder=0)
    for spine in b.spines.values(): spine.set_visible(False)
    save(fig,figs/"variable_sizes.pdf")
