"""Regression tests for cluster geometry, eligibility, and paid query ordering."""

from itertools import combinations
from math import comb
from pathlib import Path
from random import Random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))

from cluster_landscapes import (GEOMETRIES, KeyGrid, angle_component_sizes, coverage_budget,
                                distance_scores, equal_runs, isolated_miss_count, key_run_lengths, place_runs, relabel_energies,
                                target_set, variable_lengths)
from cluster_expectation import first_hit_times
from hybrid_qaoa import search_grid


class ClusterLandscapeTests(unittest.TestCase):
    def test_shape_construction_and_distinct_geometries(self):
        grid = KeyGrid(4)
        self.assertEqual(set(grid.points), {(i,j) for i in range(16) for j in range(16)})
        for k,(g,b) in enumerate(grid.points):
            self.assertEqual(grid.key[g][b], k)
        for seed in range(16):
            for geometry in GEOMETRIES:
                mask = target_set(grid,16,geometry,Random(seed))
                self.assertEqual(len(mask),16)
                self.assertTrue(all(0 <= k < 256 for k in mask))
                self.assertEqual(mask,target_set(grid,16,geometry,Random(seed)))
                if geometry in ("solid","four_runs","isolated"):
                    r = {"solid":1,"four_runs":4,"isolated":16}[geometry]
                    self.assertEqual(key_run_lengths(mask),(16//r,)*r)
                if geometry=="angle_patch":
                    self.assertEqual(angle_component_sizes(grid,mask),(16,))

    def test_sorted_anchor_bijection_exhausts_legal_masks(self):
        # All pairs of length-2 intervals on eight keys with at least one gap.
        class FixedSample:
            def __init__(self, anchors): self.anchors = anchors
            def sample(self, population, k): return self.anchors
        layouts = {equal_runs(8,4,2,FixedSample(a)) for a in combinations(range(5),2)}
        brute = {frozenset(a) for a in combinations(range(8),4) if key_run_lengths(a)==(2,2)}
        self.assertEqual(layouts,brute)
        self.assertEqual(len(layouts),comb(5,2))
        with self.assertRaises(ValueError):
            equal_runs(8,6,6,Random(0))

    def test_distance_encodes_exact_same_targets_and_wraps(self):
        grid = KeyGrid(3)
        mask = frozenset([grid.key[0][0],grid.key[5][6]])
        distances = distance_scores(grid,mask)
        self.assertEqual({k for k,v in enumerate(distances) if v==0},mask)
        self.assertEqual(distances[grid.key[7][0]],1)
        for k,(g,b) in enumerate(grid.points):
            def torus_delta(a,c):
                return min(abs(a-c), grid.side-abs(a-c))
            expected = min(torus_delta(g,grid.points[s][0])+torus_delta(b,grid.points[s][1])
                           for s in mask)
            self.assertEqual(distances[k],expected)

    def test_qaoa_relabeling_preserves_values_start_and_target_count(self):
        vals = (8,2,0,5,-1,4,9,0,2,3,6,7)
        for seed in range(15):
            planted, shuffled = relabel_energies(vals,0,Random(seed))
            for layout in (planted,shuffled):
                self.assertEqual(sorted(layout.values),sorted(vals))
                self.assertEqual(layout.values[0],vals[0])
                self.assertEqual(layout.valid,{k for k,x in enumerate(layout.values) if x<=0})
                self.assertEqual(len(layout.valid),3)
            self.assertEqual(key_run_lengths(planted.valid),(3,))
        with self.assertRaises(ValueError):
            relabel_energies((0,1,2),0,Random(7))

    def test_both_paid_sieves_cover_every_block_and_match_rank_convention(self):
        grid=KeyGrid(2)
        for m in (1,2,3,4,5,8,16):
            deadline=coverage_budget(grid.size,m)
            for start in range(grid.size-m+1):
                mask=set(range(start,start+m))
                for method in ("original","recursive"):
                    result=search_grid(lambda g,b: int(grid.key[g][b] not in mask),angle_bits=2,
                                       initial=(0,0),starter=method,pilot_fraction=1,
                                       max_evaluations=deadline)
                    self.assertIsNotNone(result.first_hit(0))
                    if method=="original" and m>=2:
                        canonical=first_hit_times(4,m)[start]
                        self.assertEqual(result.first_hit(0),1 if start==0 else canonical+1)

    def test_variable_lengths_and_shared_gaps(self):
        for total in (8,19,32):
            for runs in (2,3,4,5):
                anchors = list(range(2,2*runs+1,2))
                for model in ("balanced","unequal","dominant"):
                    for seed in range(8):
                        lengths = variable_lengths(total,runs,model,Random(seed))
                        self.assertEqual(sum(lengths),total)
                        self.assertEqual(len(lengths),runs)
                        self.assertGreaterEqual(min(lengths),1)
                        if model == "unequal":
                            self.assertGreater(max(lengths),min(lengths))
                        if model == "dominant":
                            self.assertEqual(max(lengths),total-runs+1)
                        valid = place_runs(64,lengths,anchors)
                        self.assertEqual(key_run_lengths(valid),lengths)
        with self.assertRaises(ValueError):
            place_runs(16,(3,4),(4,4))
        with self.assertRaises(ValueError):
            variable_lengths(3,3,"unequal",Random(0))

    def test_total_mass_deadline_can_fail_for_unequal_runs(self):
        grid = KeyGrid(2)
        target = {1,2,3,5}
        for starter in ("recursive","original"):
            trace = search_grid(lambda g,b: int(grid.key[g][b] not in target),
                                angle_bits=2,initial=(0,0),max_evaluations=16,
                                pilot_fraction=1,starter=starter)
            hit = trace.first_hit(0)
            self.assertEqual(hit,5)
            self.assertGreater(hit,coverage_budget(16,len(target)))
            self.assertLessEqual(hit,coverage_budget(16,3))
            self.assertLessEqual(hit,coverage_budget(16,2))

    def test_isolated_miss_count_matches_brute_force(self):
        for n in range(2,9):
            for m in range(1, (n+1)//2 + 1):
                masks = [set(v) for v in combinations(range(n),m)
                         if all(b-a>1 for a,b in zip(v,v[1:]))]
                for forbidden in (set(), {0}, {0,n-1}, set(range(0,n,2)), set(range(n))):
                    expected = sum(not s.intersection(forbidden) for s in masks)
                    self.assertEqual(isolated_miss_count(n,m,forbidden), expected)

    def test_uniform_mask_hit_probability_depends_only_on_distinct_queries(self):
        n,m,t=8,2,3
        for queries in ((1,3,6),(0,2,4),(7,0,2)):
            misses=sum(not set(queries).intersection(s) for s in combinations(range(n),m))
            self.assertEqual(misses,comb(n-t,m))
