"""Controlled target geometries in the hybrid optimizer's integer key encoding."""

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import groupby
from random import Random

from hybrid_qaoa import _morton_point
from pattern_search import ENERGY_TOLERANCE

GEOMETRIES = ("solid", "four_runs", "isolated", "uniform", "angle_patch")


class KeyGrid:
    """Translate a square, periodic grid into the joint sieve's Morton keys."""

    def __init__(self, angle_bits: int):
        if angle_bits < 1:
            raise ValueError("angle_bits must be positive")
        self.bits = angle_bits
        self.side = 1 << angle_bits
        self.size = self.side * self.side
        self.points = tuple(_morton_point(k, angle_bits) for k in range(self.size))
        self.key = [[0] * self.side for _ in range(self.side)]
        for k, (g, b) in enumerate(self.points):
            self.key[g][b] = k
        self.neighbors = []
        for g, b in self.points:
            self.neighbors.append((
                self.key[(g+1) % self.side][b], self.key[(g-1) % self.side][b],
                self.key[g][(b+1) % self.side], self.key[g][(b-1) % self.side]))


def equal_runs(size: int, valid_count: int, run_count: int, rng: Random) -> frozenset[int]:
    """Uniform legal placement of sorted equal runs with a gap of at least one."""
    if not 1 <= run_count <= valid_count <= size or valid_count % run_count:
        raise ValueError("run count must divide the valid count")
    if size - valid_count + 1 < run_count:
        raise ValueError("too few invalid keys to separate the runs")
    length = valid_count // run_count
    anchors = sorted(rng.sample(range(size-valid_count+1), run_count))
    return place_runs(size, [length]*run_count, anchors)


def place_runs(size: int, lengths: Sequence[int], anchors: Sequence[int]) -> frozenset[int]:
    """Place ordered positive lengths at shared sorted gap coordinates."""
    count = sum(lengths)
    if not lengths or any(x < 1 for x in lengths) or len(anchors) != len(lengths):
        raise ValueError("expected one anchor per positive length")
    if anchors[0] < 0 or anchors[-1] > size-count or any(a >= b for a,b in zip(anchors,anchors[1:])):
        raise ValueError("anchors must be distinct, ascending and in range")
    valid = set()
    offset = 0
    for a, length in zip(anchors, lengths):
        start = a + offset
        valid.update(range(start, start+length))
        offset += length
    return frozenset(valid)


def variable_lengths(total: int, runs: int, model: str, rng: Random) -> tuple[int, ...]:
    """Draw one ordered composition conditional on total mass and run count."""
    if not 2 <= runs < total:
        raise ValueError("expected at least two runs and some excess mass")
    if model == "balanced":
        each, extra = divmod(total, runs)
        lengths = [each+1]*extra + [each]*(runs-extra)
        rng.shuffle(lengths)
        return tuple(lengths)
    if model == "dominant":
        lengths = [1]*runs
        lengths[rng.randrange(runs)] = total-runs+1
        return tuple(lengths)
    if model != "unequal":
        raise ValueError("unknown run-length model")
    while True:
        cuts = [0, *sorted(rng.sample(range(1,total), runs-1)), total]
        lengths = tuple(b-a for a,b in zip(cuts,cuts[1:]))
        if min(lengths) != max(lengths):
            return lengths


def target_set(grid: KeyGrid, count: int, geometry: str, rng: Random) -> frozenset[int]:
    if not 1 <= count <= grid.size:
        raise ValueError("invalid target count")
    if geometry in ("solid", "four_runs", "isolated"):
        runs = {"solid": 1, "four_runs": 4, "isolated": count}[geometry]
        return equal_runs(grid.size, count, runs, rng)
    if geometry == "uniform":
        return frozenset(rng.sample(range(grid.size), count))
    if geometry != "angle_patch" or count & (count-1):
        raise ValueError("unknown geometry or non-dyadic angle patch size")
    # A translated toroidal rectangle with aspect ratio one or two.
    height = 1 << ((count.bit_length()-1)//2)
    width = count // height
    if rng.randrange(2):
        height, width = width, height
    g0, b0 = rng.randrange(grid.side), rng.randrange(grid.side)
    return frozenset(grid.key[(g0+i) % grid.side][(b0+j) % grid.side]
                     for i in range(height) for j in range(width))


def key_run_lengths(valid) -> tuple[int, ...]:
    """Maximal nonwrapping runs in integer key order."""
    groups = groupby(enumerate(sorted(valid)), key=lambda item: item[1]-item[0])
    return tuple(sum(1 for _ in members) for _, members in groups)


def angle_component_sizes(grid: KeyGrid, valid) -> tuple[int, ...]:
    remaining = set(valid)
    sizes = []
    while remaining:
        stack = [remaining.pop()]
        count = 0
        while stack:
            count += 1
            for neighbor in grid.neighbors[stack.pop()]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        sizes.append(count)
    return tuple(sorted(sizes, reverse=True))


def isolated_miss_count(size: int, count: int, queried: set[int]) -> int:
    """Count nonadjacent count-subsets of [0,size) avoiding all queried indices."""
    if size < 1 or not 0 <= count <= (size+1)//2:
        raise ValueError("invalid isolated-target dimensions")
    if any(k < 0 or k >= size for k in queried):
        raise ValueError("queried index outside the key space")
    # prev and prev2 count placements on the two shorter prefixes of the path.
    prev2 = prev = [1] + [0] * count
    for k in range(size):
        current = prev.copy()
        if k not in queried:
            for j in range(1, count+1):
                current[j] += prev2[j-1]
        prev2, prev = prev, current
    return prev[count]


def distance_scores(grid: KeyGrid, valid) -> list[int]:
    """Exact graph distance on the angle torus from each key to a valid cell."""
    if not valid:
        raise ValueError("a nonempty target is required")
    distances = [-1] * grid.size
    queue = deque(valid)
    for k in valid:
        distances[k] = 0
    while queue:
        k = queue.popleft()
        for neighbor in grid.neighbors[k]:
            if distances[neighbor] == -1:
                distances[neighbor] = distances[k]+1
                queue.append(neighbor)
    return distances


def coverage_budget(size: int, minimum_run: int) -> int:
    """Sufficient paid calls when at least one nonwrapping run has this length."""
    if size < 2 or size & (size-1) or not 1 <= minimum_run <= size:
        raise ValueError("expected a power-of-two space and a length in range")
    return size // (1 << (minimum_run.bit_length()-1))


@dataclass(frozen=True)
class Relabeling:
    values: tuple[float, ...]
    valid: frozenset[int]


def relabel_energies(values: Sequence[float], target: float, rng: Random
                     ) -> tuple[Relabeling, Relabeling]:
    """Paired solid/uniform layouts, with the same energy multiset and initial energy.

    Key zero is the common paid start and must be invalid. Both layouts use the
    identical shuffled lists of valid and invalid energies. Only their assigned
    locations change. The threshold is the archived graph/start threshold.
    """
    if not values or values[0] <= target + ENERGY_TOLERANCE:
        raise ValueError("the designated start must be invalid")
    good = [v for v in values[1:] if v <= target + ENERGY_TOLERANCE]
    bad = [v for v in values[1:] if v > target + ENERGY_TOLERANCE]
    if not good:
        raise ValueError("expected at least one valid key")
    rng.shuffle(good)
    rng.shuffle(bad)
    n, m = len(values), len(good)
    a = rng.randint(1, n-m)
    masks = (frozenset(range(a, a+m)), frozenset(rng.sample(range(1, n), m)))

    def assign(mask):
        hits, misses = iter(good), iter(bad)
        ordered = [values[0]]
        ordered.extend(next(hits) if k in mask else next(misses) for k in range(1, n))
        return Relabeling(tuple(ordered), mask)

    return assign(masks[0]), assign(masks[1])
