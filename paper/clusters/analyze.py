"""Build conditional summaries, paired intervals, manuscript tables, and research figures."""

import argparse
from pathlib import Path
from math import comb
from random import Random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "examples"))
from benchmark_cluster_assumption import BUDGET, GEOMETRIES, POLICIES, seed_for
from cluster_landscapes import KeyGrid, target_set
from recursive_dyadic_sieve import keys as recursive_keys
import variable_analysis

METRICS = ["loss","hit13","hit_q","hit32","hit65","used"]
GEOM_LABELS = {"solid":"One solid run","four_runs":"Four equal runs","isolated":"Isolated",
               "uniform":"Uniform subset","angle_patch":"Angle rectangle"}
METHOD_LABELS = {"original":"Original sieve","recursive":"Recursive sieve","halton":"Halton",
                 "sobol":"Sobol","random":"Random order","pattern":"Pattern search",
                 "recursive13":"Recursive 13 + poll","recursive33":"Recursive 33 + poll",
                 "recursive_bound":"Recursive bound + poll","halton13":"Halton 13 + poll",
                 "recursive_patience":"Recursive patience"}
TEAL, BLUE, ORANGE, INDIGO, INK, GRID = "#08776b","#27649d","#ae5224","#776196","#243847","#d9e1e5"


def expand(raw, keys):
    frames = []
    for name in POLICIES:
        part = raw[keys].copy()
        hits = raw[name]
        part["method"] = name
        part["loss"] = hits.fillna(BUDGET+1)
        part["hit13"] = hits.le(13)
        part["hit_q"] = hits.le(raw.q)
        part["hit32"] = hits.le(32)
        part["hit65"] = hits.notna()
        part["used"] = raw[name+"_used"]
        frames.append(part)
    return pd.concat(frames,ignore_index=True)


def grouped(data, keys):
    return data.groupby(keys, observed=True)[METRICS].mean()


def bootstrap_delta(delta, strata, draws=10000):
    """Resample paired units within design strata, maintaining original stratum weights."""
    if delta[METRICS].isna().any().any():
        raise ValueError("unpaired observations")
    rng = np.random.default_rng(20531121)
    boot = np.zeros((draws,len(METRICS)))
    for _,part in delta.groupby(strata):
        x = part[METRICS].to_numpy(dtype=float)
        for start in range(0, draws, 500):
            m = min(500,draws-start)
            ids = rng.integers(0,len(x),size=(m,len(x)))
            boot[start:start+m] += x[ids].sum(axis=1) / len(delta)
    return np.quantile(boot,[0.025,0.975],axis=0)


def comparisons(syn, arch, out):
    rows=[]
    def add(design, a, b, values, keys, strata):
        labels=values.index.names
        subset_a=values.xs(a,level=keys)
        subset_b=values.xs(b,level=keys)
        delta=(subset_a-subset_b).reset_index()
        if delta.empty or len(subset_a)!=len(subset_b):
            raise ValueError(f"missing group for {labels}")
        lo,hi=bootstrap_delta(delta,strata)
        for i,metric in enumerate(METRICS):
            rows.append((design,"/".join(a),"/".join(b),metric,
                         delta[metric].mean(),lo[i],hi[i],len(delta)))

    # One paired synthetic unit is a replicate within a size/density setting.
    s=grouped(syn,["bits","q","rep","geometry","feedback","method"])
    for a,b in (
            (("solid","membership","recursive"),("uniform","membership","recursive")),
            (("solid","membership","recursive"),("solid","membership","random")),
            (("uniform","membership","recursive"),("uniform","membership","random")),
            (("solid","membership","recursive_bound"),("solid","membership","recursive13")),
            (("solid","distance","pattern"),("solid","membership","pattern")),
            (("solid","distance","pattern"),("solid","distance","recursive"))):
        add("synthetic_six_strata",a,b,s,["geometry","feedback","method"],["bits","q"])

    # Resample whole graphs after averaging three starts and 32 relabelings per graph.
    g=grouped(arch,["stratum","case","layout","method"])
    for a,b in (
            (("solid","recursive"),("native","recursive")),
            (("solid","recursive"),("shuffled","recursive")),
            (("shuffled","recursive"),("native","recursive")),
            (("native","recursive"),("native","halton")),
            (("solid","recursive"),("solid","halton")),
            (("shuffled","recursive"),("shuffled","halton")),
            (("solid","recursive_bound"),("solid","recursive13")),
            (("solid","recursive_bound"),("solid","recursive_patience"))):
        add("matched_qaoa",a,b,g,["layout","method"],["stratum"])
    pd.DataFrame(rows,columns=["design","a","b","metric","a_minus_b","lo95","hi95","units"]
                 ).to_csv(out/"paired.csv",index=False,float_format="%.9f")


def save(fig, path):
    fig.savefig(path,bbox_inches="tight",pad_inches=0.05,
                metadata={"Creator":"Target geometry study","CreationDate":None,"ModDate":None})
    plt.close(fig)


def axis_style(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="y",color=GRID,linewidth=0.7)
    ax.tick_params(length=0,pad=4,colors=INK)
    for side in ("top","right","left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#93a4ac")


def make_figures(synthetic, archive, exact_hist, mixture, out):
    out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.size":9,"font.family":"DejaVu Sans","text.color":INK,
                         "axes.labelcolor":INK,"pdf.fonttype":42})
    grid=KeyGrid(4)
    fig,ax=plt.subplots(figsize=(6.4,1.85),layout="constrained")
    for y,geo in enumerate(GEOMETRIES):
        valid=target_set(grid,16,geo,Random(seed_for("mask",4,16,0,geo)))
        ax.scatter(sorted(valid),[y]*len(valid),s=46,marker="|",color=TEAL,linewidth=1.5)
    for k in range(0,256,16):
        ax.axvline(k,color="#c7d3d7",lw=0.6,zorder=0)
    ax.set(xlim=(-2,257),ylim=(4.45,-0.45),yticks=range(5),
           yticklabels=[GEOM_LABELS[x] for x in GEOMETRIES],xticks=[0,32,64,96,128,160,192,224,255],
           xlabel="Integer search key")
    ax.tick_params(length=0)
    for spine in ax.spines.values(): spine.set_visible(False)
    save(fig,out/"geometry.pdf")

    fig,ax=plt.subplots(figsize=(6.4,2.32),layout="constrained")
    axis_style(ax)
    h=exact_hist.query("size==256 and valid_count==16 and order=='recursive_zero_first'")
    x=np.arange(1,42)
    solid=np.array([h.loc[h.first_hit.le(t),"placements"].sum()/241 for t in x])
    uniform=np.array([1-comb(256-t,16)/comb(256,16) for t in x])
    # The reference random policy also pays for key zero first on a uniformly placed block.
    random_solid=np.array([1-(240/241)*comb(256-t,16)/comb(255,16) for t in x])
    for y,label,color,style in ((solid,"Dyadic sieve, uniform block start",TEAL,"-"),
            (uniform,"Any fixed permutation, uniform subset",BLUE,"--"),
            (random_solid,"Random order after key 0, uniform block start",ORANGE,":")):
        ax.step(x,100*y,where="post",label=label,c=color,ls=style,lw=1.8)
    ax.axvline(16,color="#87949b",ls=":",lw=.8)
    ax.set(xlim=(1,41),ylim=(-1,103),xticks=[1,8,13,16,24,32,40],yticks=[0,25,50,75,100],
           xlabel="Paid evaluations",ylabel="Probability of a valid hit (%)")
    ax.legend(loc="lower right",fontsize=7.9,frameon=False)
    save(fig,out/"exact_curves.pdf")

    fig,ax=plt.subplots(figsize=(6.5,2.42),layout="constrained")
    methods=["recursive","halton","random","pattern","recursive13","recursive_bound"]
    geos=list(GEOMETRIES)
    sub=synthetic.xs(("membership",),level=("feedback",)).reset_index()
    pivot=sub.pivot_table(index="method",columns="geometry",values="hit_q").loc[methods,geos]
    matrix=100*pivot.to_numpy()
    from matplotlib.colors import LinearSegmentedColormap
    cmap=LinearSegmentedColormap.from_list("teal",["#f2f6f6","#9dcfc3","#006451"])
    ax.imshow(matrix,vmin=25,vmax=100,cmap=cmap,aspect="auto")
    ax.set_xticks(range(5),["One block","Four runs","Isolated","Uniform subset","Angle rectangle"])
    ax.set_yticks(range(len(methods)),[METHOD_LABELS[x] for x in methods])
    ax.tick_params(length=0,pad=5)
    for i in range(len(methods)):
        for j in range(len(geos)):
            ax.text(j,i,f"{matrix[i,j]:.1f}",ha="center",va="center",
                    color="white" if matrix[i,j]>78 else INK,fontsize=9)
    for spine in ax.spines.values(): spine.set_visible(False)
    save(fig,out/"conditional_hits.pdf")

    fig,ax=plt.subplots(figsize=(6.4,2.48),layout="constrained")
    axis_style(ax)
    methods=["recursive","halton","random","pattern","recursive13","recursive_bound"]
    yy=np.arange(len(methods))
    for layout,label,col,symbol,offset in (("native","Native QAOA",ORANGE,"o",-.19),
            ("shuffled","Shuffled",BLUE,"s",0),("solid","One valid block",TEAL,"D",.19)):
        ax.scatter([archive.loc[layout,m].loss for m in methods],yy+offset,c=col,
                   marker=symbol,s=32,label=label)
    ax.set(yticks=yy,yticklabels=[METHOD_LABELS[m] for m in methods],
           xlabel="Mean capped calls to first valid point",xlim=(7,40))
    ax.invert_yaxis()
    ax.legend(loc="upper center",bbox_to_anchor=(.52,1.2),ncol=3,frameon=False,fontsize=8)
    save(fig,out/"matched_qaoa.pdf")


    fig,(ax,rug)=plt.subplots(2,1,figsize=(6.4,2.6),sharex=True,
                              gridspec_kw={"height_ratios":[2.4,1]},layout="constrained")
    n,m,a=256,16,68
    keys=np.arange(n)
    center=a+(m-1)/2
    e=-(1+np.cos(2*np.pi*(keys-center)/n))/2
    cutoff=-(1+np.cos(np.pi*m/n))/2
    ax.plot(keys,e,color=BLUE,lw=1.6,label="One-edge QAOA energy")
    ax.axhline(cutoff,color=ORANGE,ls="--",lw=1.15,label="Validity threshold")
    ax.axvspan(a-.5,a+m-.5,color="#b5ded2",alpha=.65)
    ax.set(ylabel="Energy",yticks=[-1,-.5,0])
    axis_style(ax)
    ax.legend(loc="upper left",frameon=False,fontsize=7.8)
    plain=keys[e<=cutoff+1e-12]
    dispersed=keys[e[((n//2+1)*keys)%n]<=cutoff+1e-12]
    first=next(k for k in [0]+list(recursive_keys(8))[:-1] if k in plain)
    for y,v in enumerate((plain,dispersed)):
        rug.scatter(v,np.full(len(v),y),marker="|",s=72,color=TEAL,linewidth=1.1)
        rug.scatter([first],[y],s=22,color=ORANGE,zorder=4)
    rug.set(xlim=(-1,256),ylim=(1.65,-.6),yticks=[0,1],
            yticklabels=["Physical keys","Odd-stride keys"],xticks=[0,64,128,192,255],xlabel="Integer search key")
    rug.tick_params(length=0)
    for spine in rug.spines.values(): spine.set_visible(False)
    save(fig,out/"one_edge.pdf")

    fig, ax=plt.subplots(figsize=(6.45,2.15),layout="constrained")
    axis_style(ax)
    x=100*mixture.assumed_solid_probability
    ax.plot(x,mixture.recursive_loss,color=TEAL,lw=2,label="Pure recursive sieve")
    ax.plot(x,mixture.halton_loss,color=ORANGE,lw=2,ls="--",label="Pure Halton")
    delta=mixture.recursive_loss-mixture.halton_loss
    crossing=100*delta.iloc[0]/(delta.iloc[0]-delta.iloc[-1])
    ax.axvline(crossing,color=INK,lw=.9,ls=":")
    ax.annotate(f"{crossing:.1f}%",(crossing,21),xytext=(-5,0),textcoords="offset points",ha="right")
    ax.set(xlim=(0,100),xticks=[0,25,50,75,100],ylabel="Expected capped calls",
           xlabel="Assumed probability of a solid reindexing (%)")
    ax.legend(loc="upper right",frameon=False,fontsize=8)
    save(fig,out/"mixture.pdf")


def mixture_threshold(by_graph,out):
    wide=by_graph.loss.unstack(["layout","method"])
    native=wide["native","recursive"]-wide["native","halton"]
    solid=wide["solid","recursive"]-wide["solid","halton"]
    paired=pd.DataFrame({"native":native,"solid":solid})
    rng=np.random.default_rng(20531121)
    draws=np.zeros((10000,2))
    for _,part in paired.groupby(level="stratum"):
        x=part.to_numpy()
        ids=rng.integers(len(x),size=(10000,len(x)))
        draws+=x[ids].sum(axis=1)/len(paired)
    keep=(draws[:,0]>0)&(draws[:,1]<0)
    ratios=draws[keep,0]/(draws[keep,0]-draws[keep,1])
    point=native.mean()/(native.mean()-solid.mean())
    lo,hi=np.quantile(ratios,[.025,.975])
    pd.DataFrame([(point,lo,hi,keep.sum(),len(draws))],columns=[
        "crossing","lo95","hi95","interior_draws","draws"]
        ).to_csv(out/"mixture_threshold.csv",index=False,float_format="%.9f")


def law_comparison(exact, isolated, out):
    rows = []
    means = exact.query("size==256 and order=='recursive_zero_first'")
    for _, row in means.iterrows():
        n, m = int(row["size"]), int(row["valid_count"])
        restricted = isolated[isolated.valid_count.eq(m)].set_index("order")
        rows.extend([
            (n, m, "uniform_block_start", row["mean"], (n-m+2)/2),
            (n, m, "uniform_subset", (n+1)/(m+1), (n+1)/(m+1)),
            (n, m, "uniform_isolated", restricted.loc["recursive","mean"],
             restricted.loc["ascending_key","mean"]),
        ])
    table = pd.DataFrame(rows, columns=["size","valid_count","target_law","dyadic_mean","ascending_mean"])
    table.to_csv(out/"law_comparison.csv", index=False, float_format="%.9f")
    return table


def tex_tables(exact,syn,arch,edge,laws,out):
    blocks={}
    labels={"uniform_block_start":"Uniform start of one solid block",
            "uniform_subset":"Uniform 16-element subset",
            "uniform_isolated":"Uniform 16-element subset with no neighbors"}
    blocks["LawRows"]=[f"{labels[r.target_law]} & {r.dyadic_mean:.2f} & {r.ascending_mean:.2f}"
                       for r in laws[laws.valid_count.eq(16)].itertuples()]
    rows=[]
    for q in (8,16,32):
        a=exact.query("size==256 and q==@q and order=='original_canonical'").iloc[0]
        z=exact.query("size==256 and q==@q and order=='original_zero_first'").iloc[0]
        rows.append(f"{int(z.valid_count)} & {q} & {a['mean']:.2f} & {z['mean']:.2f} & "
                    f"{z.random_zero_first_mean:.2f} & {100*z.null_hit_by_q:.1f}")
    blocks["ExactRows"]=rows
    rows=[]
    for g in GEOMETRIES:
        sub=syn.xs((4,16,g),level=("bits","q","geometry"))
        rows.append(f"{GEOM_LABELS[g]} & "+" & ".join(f"{sub.loc[f,m].loss:.2f}"
                    for f,m in (("membership","recursive"),("membership","random"),
                        ("membership","pattern"),("distance","pattern"),
                        ("membership","recursive13"),("distance","recursive13"))))
    blocks["FeedbackRows"]=rows
    rows=[]
    for method in ("original","recursive","halton","sobol","random","pattern","recursive13",
                   "halton13","recursive_bound","recursive_patience"):
        v=[arch.loc[layout,method] for layout in ("native","shuffled","solid")]
        rows.append(METHOD_LABELS[method]+" & "+" & ".join(f"{r.loss:.2f} & {100*r.hit65:.1f}" for r in v))
    blocks["ArchiveRows"]=rows
    rows=[]
    for m in (8,16,32):
        v=[edge.loc[m,enc] for enc in ("physical","odd_stride","shuffled")]
        rows.append(f"{m} & "+" & ".join(f"{r.mean_hit:.2f} & {int(r.worst_hit)}" for r in v))
    blocks["EdgeRows"]=rows
    with (out/"paper_tables.tex").open("w",encoding="utf-8") as stream:
        for name,rows in blocks.items():
            stream.write("\\newcommand{\\"+name+"}{%\n")
            for row in rows: stream.write(row+r" \\"+"\n")
            stream.write("}\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results",type=Path,default=HERE/"results")
    parser.add_argument("--variable-only",action="store_true",help="summarize only variable-block experiments")
    parser.add_argument("--figures",type=Path,default=HERE/"figures")
    args=parser.parse_args()
    out=args.results
    if args.variable_only:
        plt.rcParams.update({"font.size":9,"font.family":"DejaVu Sans","text.color":INK,
                             "axes.labelcolor":INK,"pdf.fonttype":42})
        variable_analysis.build(out,args.figures,save,axis_style)
        return
    raw=pd.read_csv(out/"synthetic.csv.gz")
    syn=expand(raw,["bits","q","rep","geometry","feedback"])
    raw_a=pd.read_csv(out/"archived_qaoa.csv.gz")
    raw_a["q"]=raw_a.valid_count.map(lambda m:256//(1<<(int(m).bit_length()-1)))
    arc=expand(raw_a,["stratum","case","start","draw","layout"])
    syn_table=grouped(syn,["bits","q","geometry","feedback","method"])
    arc_graph=grouped(arc,["stratum","case","layout","method"])
    arc_table=grouped(arc_graph.reset_index(),["layout","method"])
    syn_table.to_csv(out/"synthetic_summary.csv",float_format="%.9f")
    arc_table.to_csv(out/"qaoa_summary.csv",float_format="%.9f")
    comparisons(syn,arc,out)
    edge=pd.read_csv(out/"one_edge.csv.gz").groupby(["valid_count","encoding"]).agg(
        placements=("start","size"),mean_hit=("recursive","mean"),worst_hit=("recursive","max"),
        min_longest_run=("longest_key_run","min"),max_longest_run=("longest_key_run","max"))
    edge.to_csv(out/"one_edge_summary.csv",float_format="%.9f")
    mixture=[]
    for i in range(101):
        p=i/100
        r=(1-p)*arc_table.loc["native","recursive"].loss + p*arc_table.loc["solid","recursive"].loss
        h=(1-p)*arc_table.loc["native","halton"].loss + p*arc_table.loc["solid","halton"].loss
        mixture.append((p,r,h))
    mixture=pd.DataFrame(mixture,columns=["assumed_solid_probability","recursive_loss","halton_loss"])
    mixture.to_csv(out/"mixture.csv",index=False,float_format="%.9f")
    mixture_threshold(arc_graph,out)
    exact=pd.read_csv(out/"exact.csv")
    laws=law_comparison(exact,pd.read_csv(out/"isolated_exact.csv"),out)
    tex_tables(exact,syn_table,arc_table,edge,laws,out)
    make_figures(syn_table,arc_table,pd.read_csv(out/"exact_histograms.csv"),mixture,args.figures)
    variable_analysis.build(out,args.figures,save,axis_style)


if __name__=="__main__":
    main()
