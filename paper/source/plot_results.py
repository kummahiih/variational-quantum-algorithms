"""Create the publication's figures from the deterministic benchmark CSV.

Requires matplotlib for plotting only; QAOA runs require no dependencies.
"""
from pathlib import Path
from collections import defaultdict
import csv
import statistics
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ROWS = list(csv.DictReader((ROOT / 'results/qaoa_benchmark_raw.csv').open()))
ORDER = ['recursive','original','ascending','shuffled','random_joint','pattern']
LABELS = ['Recursive sieve','Original sieve','Ascending grid','Shuffled grid','Random angle pairs','Pattern search']

# Figure 1: compare coarse-to-fine visit order for b=4
orig = [8,4,12,2,6,10,14,1,3,5,7,9,11,13,15,0]
rec  = [8,4,12,2,10,6,14,1,9,5,13,3,11,7,15,0]
fig, ax = plt.subplots(figsize=(6.9,2.5))
ax.plot(range(1,17), orig, '-o', ms=3, lw=1.5, label='Original sieve')
ax.plot(range(1,17), rec, '-s', ms=3, lw=1.3, label='Recursive sieve')
ax.set(xlabel='Evaluation rank',ylabel='Integer angle-grid key',xlim=(1,16),ylim=(-0.5,15.5))
ax.set_xticks([1,4,8,12,16]);ax.set_yticks([0,4,8,12,15])
ax.legend(frameon=False, fontsize=8, ncol=2)
ax.grid(alpha=.15)
fig.tight_layout()
fig.savefig(ROOT / 'figures/sieve_orders.pdf')
fig.savefig(ROOT / 'figures/sieve_orders.png', dpi=180)
plt.close(fig)

# Figure 2: hit rate by evaluation budget, using each randomized seed as a trial;
# conditions are not independent random problem draws, so descriptive only.
# The original and recursive sieves have IDENTICAL aggregated hit rates at
# these four checkpoints. Draw a thick blue outer trace with a narrower dashed
# orange inner trace so neither series is hidden by overplotting.
fig, ax = plt.subplots(figsize=(7.4, 3.35))
xs = [10, 20, 40, 65]
def hit_curve(method):
    rs = [r for r in ROWS if r['method'] == method]
    return [100 * sum(bool(r['first_hit']) and int(r['first_hit']) <= b
                      for r in rs) / len(rs) for b in xs]

handles = {}
# Draw the alternative comparators first; they can also coincide at later
# checkpoints, but we give priority to keeping both sieve series visible.
for method, label, color in zip(ORDER[2:], LABELS[2:],
                                ['tab:green', 'tab:red', 'tab:purple', 'tab:brown']):
    (line,) = ax.plot(xs, hit_curve(method), marker='o', markersize=4,
                      linewidth=1.6, color=color, label=label, zorder=2)
    handles[method] = line

# Render same-position curves as a two-color outlined line rather than
# shifting x/y data or pretending the two methods have different outcomes.
(blue,) = ax.plot(xs, hit_curve('recursive'), color='tab:blue',
                  marker='o', markersize=8, linewidth=4.3, zorder=5,
                  label='Recursive sieve')
(orange,) = ax.plot(xs, hit_curve('original'), color='tab:orange',
                    linestyle='--', marker='s', markerfacecolor='white',
                    markeredgewidth=1.1, markersize=4.3, linewidth=1.6,
                    zorder=6, label='Original sieve')
handles['recursive'], handles['original'] = blue, orange

ax.set(xlabel='Maximum exact energy evaluations (including initialization)',
       ylabel='Reached the 80% target (%)', xlim=(9, 66), ylim=(0, 105))
ax.set_xticks(xs)
ax.grid(alpha=.15)
ax.legend([handles[m] for m in ORDER], LABELS, frameon=False,
          fontsize=7.4, ncol=2, loc='lower right')
ax.annotate('Blue and orange curves coincide', xy=(10.8, 16.5),
            fontsize=7.6, color='0.28')
fig.tight_layout()
fig.savefig(ROOT / 'figures/target_hits.pdf')
fig.savefig(ROOT / 'figures/target_hits.png', dpi=180)
plt.close(fig)

# Aggregated raw quantities, with no inference/p-values.
summary=[]
for method in ORDER:
 rs=[r for r in ROWS if r['method']==method]
 def h(b):return sum(bool(r['first_hit']) and int(r['first_hit'])<=b for r in rs)/len(rs)
 def gain(b):return statistics.mean((float(r['initial_energy'])-float(r[f'energy_at_{b}']))/(float(r['initial_energy'])-float(r['grid_reference_energy'])) for r in rs)
 summary.append((method,len(rs),h(10),h(20),h(65),gain(10),gain(65),statistics.mean(float(r['optimal_probability_at_65']) for r in rs)))
with (ROOT/'results/qaoa_benchmark_summary.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['method','runs','hit_rate_at_10','hit_rate_at_20','hit_rate_at_65','gain_at_10','gain_at_65','mean_optimal_probability_at_65']); w.writerows(summary)
print('Wrote figures + aggregated summary with', len(ROWS), 'raw runs')
for r in summary: print(r)
