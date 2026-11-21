"""Compare first feasible evaluations with controlled geometry in the sieve's key space."""

import argparse
import csv
import gzip
import hashlib
import io
from collections import Counter
from contextlib import contextmanager
from fractions import Fraction
from math import comb, cos, pi
from pathlib import Path
from random import Random

from benchmark_hybrid_qaoa import ROOT, STARTS_16, exact_landscape, study_graphs
from cluster_expectation import power_of_two_cluster_expectation, random_without_replacement_expectation
from cluster_landscapes import (GEOMETRIES, KeyGrid, angle_component_sizes, coverage_budget,
                                distance_scores, isolated_miss_count, key_run_lengths, place_runs,
                                relabel_energies, target_set, variable_lengths)
from dyadic_sieve import keys as original_keys
from hybrid_qaoa import search_grid
from pattern_search import ENERGY_TOLERANCE
from recursive_dyadic_sieve import keys as recursive_keys
from sieve_qaoa import maxcut_costs, qaoa_energy

BUDGET = 65
# Each policy gives its starter, paid pilot cap and optional patience.
# A None cap uses the dyadic coverage deadline implied by the nominal count.
POLICY_SETTINGS = {
    "original": ("original", BUDGET, None),
    "recursive": ("recursive", BUDGET, None),
    "halton": ("halton", BUDGET, None),
    "sobol": ("sobol", BUDGET, None),
    "random": ("random", BUDGET, None),
    "pattern": ("recursive", 1, None),
    "original13": ("original", 13, None),
    "recursive13": ("recursive", 13, None),
    "halton13": ("halton", 13, None),
    "recursive33": ("recursive", 33, None),
    "halton33": ("halton", 33, None),
    "original_bound": ("original", None, None),
    "recursive_bound": ("recursive", None, None),
    "recursive_patience": ("recursive", 26, 4),
}
POLICIES = tuple(POLICY_SETTINGS)
DATA = ROOT / "paper/clusters/results"
OUTCOME_FIELDS = list(POLICIES) + [p+"_used" for p in POLICIES]
SHAPE_FIELDS = ["valid_count", "key_runs", "longest_key_run", "angle_components", "largest_component"]


def seed_for(*parts):
    value = "|".join(map(str, ("cluster-study-v1", *parts))).encode("utf-8")
    return int.from_bytes(hashlib.sha256(value).digest()[:8], "big")


@contextmanager
def data_writer(path, fields):
    if path.suffix == ".gz":
        with path.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb",
                mtime=0) as gz, io.TextIOWrapper(gz, encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(fields)
            yield writer
    else:
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(fields)
            yield writer


def shape(grid, valid):
    runs = key_run_lengths(valid)
    components = angle_component_sizes(grid, valid)
    return (len(valid), len(runs), max(runs), len(components), max(components))


def outcomes(grid, values, threshold, valid_count, seed, extra_caps=()):
    bound = min(BUDGET, coverage_budget(grid.size, valid_count))
    hits, spent = [], []
    settings = [*POLICY_SETTINGS.values(), *(("recursive",min(BUDGET,c),None) for c in extra_caps)]
    for method, allowance, patience in settings:
        k = bound if allowance is None else allowance
        trace = search_grid(lambda g,b: values[grid.key[g][b]], angle_bits=grid.bits,
                            initial=(0,0), max_evaluations=BUDGET, starter=method,
                            pilot_fraction=k/BUDGET, patience=patience, seed=seed)
        # A hit is an evaluated feasible point, regardless of later polishing.
        hit = next((i for i, t in enumerate(trace.trials, 1)
                    if t.energy <= threshold + ENERGY_TOLERANCE), None)
        hits.append(hit)
        spent.append(len(trace.trials))
    return hits + spent


def exact_study(out):
    fields = ["size","valid_count","q","order","placements","mean","max_hit",
              "formula","uniform_permutation_mean","random_zero_first_mean","null_hit_by_q"]
    with data_writer(out/"exact.csv", fields) as ws, data_writer(out/"exact_histograms.csv",
            ["size","valid_count","order","first_hit","placements"]) as wh:
        for bits in (6, 8, 10, 12):
            n = 1 << bits
            for q in (8, 16, 32):
                m = n//q
                count = n-m+1
                canonical = power_of_two_cluster_expectation(bits, m)
                common = canonical + 1 - Fraction(q, count)
                chance = 1 - Fraction(comb(n-q,m), comb(n,m))
                for name, key_fn in (("original", original_keys), ("recursive", recursive_keys)):
                    positive = list(key_fn(bits))[:-1]
                    for order, keys, ref in (("canonical",positive+[0],canonical),
                                             ("zero_first",[0]+positive,common)):
                        ranks = [0]*n
                        for t, key in enumerate(keys, 1):
                            ranks[key] = t
                        hist = Counter(min(ranks[a:a+m]) for a in range(count))
                        actual = Fraction(sum(t*v for t,v in hist.items()), count)
                        if actual != ref or max(hist) != q:
                            raise AssertionError("solid-cluster formula or deadline failed")
                        ws.writerow((n,m,q,name+"_"+order,count,float(actual),max(hist),str(ref),
                            float(random_without_replacement_expectation(bits,m)),
                            float(1+(1-Fraction(1,count))*Fraction(n,m+1)),float(chance)))
                        for t, placements in sorted(hist.items()):
                            wh.writerow((n,m,name+"_"+order,t,placements))


def isolated_study(out):
    """Exact ordering comparison under a uniform no-neighbors constraint."""
    grid = KeyGrid(4)
    n = grid.size
    orders = {"ascending_key": tuple(range(n))}
    for method in ("original", "recursive", "halton", "sobol"):
        trace = search_grid(lambda *_: 0, angle_bits=4, initial=(0,0), starter=method,
                            pilot_fraction=1, max_evaluations=n)
        orders[method] = tuple(grid.key[g][b] for g,b in (t.point for t in trace.trials))
    fields = ["size","valid_count","q","order","denominator","mean_fraction","mean",
              "hit_q_fraction","hit_q","uniform_mean","uniform_hit_q"]
    with data_writer(out/"isolated_exact.csv", fields) as writer:
        for m in (8,16,32):
            q = n//m
            total = comb(n-m+1,m)
            for method, order in orders.items():
                if len(set(order)) != n:
                    raise AssertionError("expected a complete nonrepeating schedule")
                blocked = set()
                survival = []
                for key in order:
                    survival.append(isolated_miss_count(n,m,blocked))
                    blocked.add(key)
                mean = Fraction(sum(survival),total)
                hit = 1-Fraction(survival[q],total)
                writer.writerow((n,m,q,method,total,str(mean),float(mean),str(hit),float(hit),
                                 (n+1)/(m+1),1-comb(n-q,m)/comb(n,m)))


def synthetic_study(out, reps):
    fields = ["bits","q","rep","geometry","feedback",*SHAPE_FIELDS,*OUTCOME_FIELDS]
    with data_writer(out/"synthetic.csv.gz", fields) as writer:
        for bits in (4,5):
            grid = KeyGrid(bits)
            for q in (8,16,32):
                m = grid.size//q
                for rep in range(reps):
                    solver_seed = seed_for("synthetic-solver",bits,q,rep)
                    for geometry in GEOMETRIES:
                        rng = Random(seed_for("mask",bits,q,rep,geometry))
                        valid = target_set(grid,m,geometry,rng)
                        info = shape(grid,valid)
                        if len(valid) != m:
                            raise AssertionError("target count changed")
                        for feedback, scores in (("membership",[int(k not in valid) for k in range(grid.size)]),
                                                 ("distance",distance_scores(grid,valid))):
                            results = outcomes(grid,scores,0,m,solver_seed)
                            if geometry == "solid" and any(results[POLICIES.index(p)] is None or
                                results[POLICIES.index(p)] > q for p in
                                ("original","recursive","original_bound","recursive_bound")):
                                raise AssertionError("paid coverage guarantee failed")
                            writer.writerow((bits,q,rep,geometry,feedback,*info,*results))


VARIABLE_MODELS = ("single", "balanced", "unequal", "dominant", "isolated", "uniform")
VARIABLE_POLICIES = (*POLICIES, "recursive_count_bound", "recursive_longest_bound")


def paid_ranks(n):
    orders = []
    for key_fn in (original_keys, recursive_keys):
        ranks = [0]*n
        for t,k in enumerate([0]+list(key_fn(n.bit_length()-1))[:-1],1):
            ranks[k] = t
        orders.append(ranks)
    return orders


def variable_width_exact(out):
    fields = ["size","width","placements","order","mean_fraction","mean","max_hit","deadline"]
    with data_writer(out/"variable_single_exact.csv",fields) as writer:
        for n in (256,1024):
            for name,ranks in zip(("original","recursive"),paid_ranks(n)):
                for m in range(n//32,n//8+1):
                    times = [min(ranks[a:a+m]) for a in range(n-m+1)]
                    mean = Fraction(sum(times),len(times))
                    deadline = coverage_budget(n,m)
                    if max(times)>deadline:
                        raise AssertionError("non-dyadic block deadline failed")
                    writer.writerow((n,m,len(times),name,str(mean),float(mean),max(times),deadline))


def varying_study(out, reps):
    fields = ["bits","total","planned_runs","rep","model","feedback","lengths",*SHAPE_FIELDS,
              "total_deadline","count_deadline","longest_deadline","original_full","recursive_full",
              *VARIABLE_POLICIES,*(p+"_used" for p in VARIABLE_POLICIES)]
    with data_writer(out/"variable_runs.csv.gz",fields) as writer:
        for bits in (4,5):
            grid = KeyGrid(bits)
            n = grid.size
            rank_o, rank_r = paid_ranks(n)
            for total in range(n//32,n//8+1):
                for runs in (2,3,4,5):
                    for rep in range(reps):
                        coord = (bits,total,runs,rep)
                        anchor_rng = Random(seed_for("variable-anchors",*coord))
                        anchors = sorted(anchor_rng.sample(range(n-total+1),runs))
                        solver_seed = seed_for("variable-solver",*coord)
                        for model in VARIABLE_MODELS:
                            rng = Random(seed_for("variable-layout",*coord,model))
                            if model in ("balanced","unequal","dominant"):
                                lengths = variable_lengths(total,runs,model,rng)
                                valid = place_runs(n,lengths,anchors)
                            else:
                                geometry = "solid" if model=="single" else model
                                valid = target_set(grid,total,geometry,rng)
                            lengths = key_run_lengths(valid)
                            info = shape(grid,valid)
                            if len(valid)!=total:
                                raise AssertionError("variable layout changed its valid count")
                            r = len(lengths)
                            deadlines = (coverage_budget(n,total),coverage_budget(n,(total+r-1)//r),
                                         coverage_budget(n,max(lengths)))
                            full = min(rank_o[k] for k in valid), min(rank_r[k] for k in valid)
                            if max(full)>deadlines[2] or deadlines[2]>deadlines[1]:
                                raise AssertionError("longest-run or count-based deadline failed")
                            # The planted positive compositions are saved verbatim. Null masks
                            # are regenerated from their recorded coordinates and labelled seed.
                            spec = "|".join(map(str,lengths)) if model not in ("isolated","uniform") else ""
                            for feedback,values in (("membership",[int(k not in valid) for k in range(n)]),
                                                    ("distance",distance_scores(grid,valid))):
                                result = outcomes(grid,values,0,total,solver_seed,deadlines[1:])
                                writer.writerow((*coord,model,feedback,spec,*info,*deadlines,*full,*result))


def one_edge_study(out):
    """An actual two-qubit statevector yields exactly m acceptable cost-angle keys."""
    n = 256
    costs = maxcut_costs(2, [(0,1)])
    fields = ["size","valid_count","start","encoding","key_runs","longest_key_run",
              "original","recursive","threshold"]
    with data_writer(out/"one_edge.csv.gz",fields) as writer:
        ranks = []
        for key_fn in (original_keys, recursive_keys):
            r = [0]*n
            for t,k in enumerate([0]+list(key_fn(8))[:-1],1):
                r[k]=t
            ranks.append(r)
        for m in (8,16,32):
            center = (m-1)/2
            threshold = -(1+cos(pi*m/n))/2
            energies = [qaoa_energy(costs, -pi/2+2*pi*(j-center)/n, pi/8) for j in range(n)]
            analytic = [-(1+cos(2*pi*(j-center)/n))/2 for j in range(n)]
            if max(abs(u-v) for u,v in zip(energies,analytic)) > 1e-12:
                raise AssertionError("one-edge statevector mismatch")
            for a in range(n-m+1):
                rng = Random(seed_for("edge",m,a))
                perm = list(range(n))
                rng.shuffle(perm)
                maps = (("physical",range(n)),("odd_stride",[(1+n//2)*k % n for k in range(n)]),
                        ("shuffled",perm))
                for name, mapping in maps:
                    valid = [k for k,j in enumerate(mapping)
                             if energies[(j-a)%n] <= threshold + ENERGY_TOLERANCE]
                    runs = key_run_lengths(valid)
                    if len(valid)!=m or (name=="physical" and valid!=list(range(a,a+m))):
                        raise AssertionError("physical target threshold mismatch")
                    writer.writerow((n,m,a,name,len(runs),max(runs),
                                     *(min(r[k] for k in valid) for r in ranks),threshold))


def archived_study(out, remaps):
    # Pull the actual thresholds from the preceding study, then reconstruct and cross-check them.
    with gzip.open(ROOT/"paper/hybrid/results/runs.csv.gz","rt") as stream:
        archived = {(r["case"],r["start"]):float(r["target"]) for r in csv.DictReader(stream)
                    if r["split"]=="confirmation" and r["policy"]=="k1"}
    grid = KeyGrid(4)
    fields = ["case","stratum","start","draw","layout","initial","threshold",*SHAPE_FIELDS,*OUTCOME_FIELDS]
    with data_writer(out/"archived_qaoa.csv.gz",fields) as writer:
        for split,case,stratum,_,_ in study_graphs():
            if split != "confirmation":
                continue
            table = exact_landscape(case,4)
            for start,(g0,b0) in STARTS_16.items():
                values = tuple(table[(g0+g)%16][(b0+b)%16] for g,b in grid.points)
                target = archived[case.name,start]
                if abs(target - (values[0]-0.8*(values[0]-min(values)))) > 1e-12:
                    raise AssertionError("archived threshold mismatch")
                valid = frozenset(k for k,v in enumerate(values) if v<=target+ENERGY_TOLERANCE)
                native_shape = shape(grid,valid)
                for draw in range(remaps):
                    rng = Random(seed_for("energy-layout",case.name,start,draw))
                    solver_seed = seed_for("energy-solver",case.name,start,draw)
                    solid, shuffled = relabel_energies(values,target,rng)
                    layouts = (("native",values,native_shape),("solid",solid.values,shape(grid,solid.valid)),
                               ("shuffled",shuffled.values,shape(grid,shuffled.valid)))
                    for label, data, info in layouts:
                        writer.writerow((case.name,stratum,start,draw,label,values[0],target,*info,
                                         *outcomes(grid,data,target,len(valid),solver_seed)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=DATA)
    parser.add_argument("--variable-only",action="store_true",help="run just variable widths and compositions")
    parser.add_argument("--replicates",type=int,default=192,help="independent synthetic draws per stratum")
    parser.add_argument("--variable-replicates",type=int,default=6,help="draws per exact width and run count")
    parser.add_argument("--remaps",type=int,default=32,help="paired reindexings per archived graph/start")
    args=parser.parse_args()
    if min(args.replicates,args.remaps,args.variable_replicates)<1:
        parser.error("replicates and remaps must be positive")
    args.out.mkdir(parents=True,exist_ok=True)
    if args.variable_only:
        variable_width_exact(args.out)
        varying_study(args.out,args.variable_replicates)
        print(f"Variable-width results in {args.out}")
        return
    exact_study(args.out)
    isolated_study(args.out)
    one_edge_study(args.out)
    variable_width_exact(args.out)
    synthetic_study(args.out,args.replicates)
    archived_study(args.out,args.remaps)
    varying_study(args.out,args.variable_replicates)
    synthetic=2*3*args.replicates*len(GEOMETRIES)*2
    archive=24*3*args.remaps*3
    changing = (25+97)*4*args.variable_replicates*len(VARIABLE_MODELS)*2
    print(f"{changing} variable-width rows, {len(VARIABLE_POLICIES)} policies each")
    print(f"{synthetic} synthetic and {archive} archived layout rows, {len(POLICIES)} policies each")


if __name__ == "__main__":
    main()
