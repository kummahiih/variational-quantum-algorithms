# Working model: QAOA tuned by the recursive dyadic sieve

> **Status (2026-11-20):** Explanation of the repository's existing one-layer QAOA prototype, not a new implementation or performance claim. The example numbers below are the documented ideal-statevector results; this document does not report an independent test run.
>
> **Read alongside:** [README](../README.md), [research journal](journal.md), [handover](handover.md), [related work](neighbors.md), and [agent conventions](../AGENTS.md).

## 1. The idea in plain language

Imagine trying to color the vertices of a graph black or white so that as many edges as possible connect vertices of different colors. This is **MaxCut**. With four vertices there are only $2^4 = 16$ colorings, but with $n$ vertices there are $2^n$.

**QAOA** (Quantum Approximate Optimization Algorithm) is a parameterized quantum circuit that prepares a *probability distribution over candidate colorings*. It has two tunable angles in the one-layer case:

- **$\gamma$ ($\gamma$):** controls a cost-dependent phase applied to each candidate coloring.
- **$\beta$ ($\beta$):** controls a mixer that combines those phases through quantum interference.

Useful angles can make good solutions more likely when the circuit is measured. But the angles are not known in advance: a **classical outer-loop optimizer** must choose them.

**This project's twist:** use the **recursive dyadic sieve** to decide *which angle values to test first*. Rather than scanning adjacent values from left to right, it first tests widely separated points, then fills gaps at progressively finer scales. It is a deterministic coarse-to-fine schedule, closely related to finite base-2 van der Corput/bit-reversal order.

```text
MaxCut graph
     |
     v
QAOA circuit with angles gamma, beta
     |
     v
Probability distribution over binary solutions
     |
     v
Expected solution cost E(gamma, beta)
     |
     v
Classical optimizer: choose better angles
     ^
     |
Recursive dyadic sieve: choose candidate angle order
```

**Two search spaces must remain distinct:**

1. **Solution space:** $x \in \{0,1\}^n$, the binary colorings eventually sampled from the circuit.
2. **Parameter space:** $(\gamma,\beta)$, the angles the sieve tests to improve the circuit.

The present sieve searches **parameter space**, *not* the MaxCut bitstrings directly. It is neither Grover search nor a quantum speedup result.

## 2. The concrete four-vertex example

The included [example](../examples/sieve_qaoa_maxcut.py) uses a cycle with four vertices and four edges:

```text
0 ------ 1
|        |
|        |
3 ------ 2
```

Each bit $x_j$ assigns a color to vertex $j$. An edge $(u,v)$ is cut if $x_u \ne x_v$.

The objective is the **negative cut size**, so minimizing it maximizes the cut:

```math
f(x) = -\sum_{(u,v)\in E} (x_u \oplus x_v).
```

For this graph:

| Assignments | Cut edges | Cost $f(x)$ |
| --- | ---: | ---: |
| `0000` and `1111` | 0 | 0 |
| Twelve other nonalternating colorings | 2 | -2 |
| `0101` and `1010` | 4 | -4 |

The best **individual** coloring has cost $-4$. The current one-layer QAOA cannot produce only those colorings on this example; its **best expected energy** is $-3$ (explained in Section 7). A single measurement can still return a cost-$-4$ coloring.

The function [`maxcut_costs`](../src/sieve_qaoa.py) constructs all $2^n$ costs, using bit shifts to evaluate edge disagreements. Duplicate edges are counted twice; self-loops and invalid indices are rejected.

## 3. Quantum states: probabilities come from amplitudes

An $n$-qubit state is

```math
|\psi\rangle = \sum_{x=0}^{2^n-1} a_x |x\rangle,
\qquad
\sum_x |a_x|^2 = 1.
```

The coefficient $a_x$ is a **complex amplitude**, and a computational-basis measurement returns bitstring $x$ with probability $|a_x|^2$.

QAOA begins in the uniform superposition

```math
|\psi_0\rangle
= |+\rangle^{\otimes n}
= \frac{1}{\sqrt{2^n}}\sum_x |x\rangle,
\qquad
|+\rangle=\frac{|0\rangle+|1\rangle}{\sqrt 2}.
```

For four qubits, each of the 16 amplitudes starts at $1/4$ and each bitstring has probability $1/16$. On hardware, Hadamard gates can prepare this state; the simulator initializes the amplitudes directly.

### 3.1 Cost-phase operator: $\gamma$

Define a diagonal cost Hamiltonian:

```math
H_C |x\rangle = f(x)|x\rangle.
```

For MaxCut, one equivalent expression is

```math
H_C = -\frac12\sum_{(u,v)\in E}(I-Z_uZ_v),
```

where $Z_j$ denotes the Pauli-Z operator on qubit $j$. The cost unitary is

```math
U_C(\gamma)=e^{-i\gamma H_C}, \qquad
U_C(\gamma)|x\rangle=e^{-i\gamma f(x)}|x\rangle.
```

It gives each coloring a **cost-dependent phase**. A phase is a rotation of a complex amplitude, so *this step alone does not change measurement probabilities*. Its purpose is to prepare relative phases for interference in the next step.

At $\gamma=\pi/4$, the phase factors for costs $0,-2,-4$ are respectively `1,i,-1`.

### 3.2 Mixing operator: $\beta$

Let $H_M=\sum_{j=0}^{n-1}X_j$, with $X_j$ the Pauli-X (bit-flip) operator on qubit $j$. The mixer is

```math
U_M(\beta)=e^{-i\beta H_M}
=\prod_{j=0}^{n-1}e^{-i\beta X_j}.
```

For a pair of amplitudes $a,b$ differing at one qubit, applying that qubit's mixer gives

```math
\begin{aligned}
a'&=\cos(\beta)a-i\sin(\beta)b,\\
b'&=-i\sin(\beta)a+\cos(\beta)b.
\end{aligned}
```

This combines amplitudes with different cost-dependent phases. Their interference changes the **magnitudes** of amplitudes and thus the output probabilities.

In short: **gamma tags solutions with phases; beta converts their relative phases into a different probability distribution.** Neither parameter independently guarantees an advantage.

### 3.3 The complete one-layer circuit

The circuit is

```math
|\psi(\gamma,\beta)\rangle
= e^{-i\beta H_M}\,e^{-i\gamma H_C}
  |+\rangle^{\otimes n}.
```

The rightmost operation occurs first. This is **$p=1$ QAOA**: one cost layer and one mixing layer, hence two tunable angles.

For greater depth $p$, alternate $p$ cost/mixer pairs with distinct angles $\gamma_1,\ldots,\gamma_p$ and $\beta_1,\ldots,\beta_p$. That yields $2p$ parameters and a larger search problem. The current code implements only $p=1$.

## 4. What the optimizer measures

For fixed angles, the state produces

```math
P(x\mid\gamma,\beta)
=|\langle x|\psi(\gamma,\beta)\rangle|^2.
```

The **expected energy** is

```math
\boxed{E(\gamma,\beta)
=\langle\psi(\gamma,\beta)|H_C|\psi(\gamma,\beta)\rangle
=\sum_x f(x)P(x\mid\gamma,\beta).}
```

The classical optimizer minimizes $E$. This is an *average cost* over measurements, **not** the cost of the single most likely bitstring and **not** necessarily the probability of obtaining an optimal bitstring.

For example, if outcomes with costs $-4,-2,0$ have total probabilities $0.5,0.4,0.1$, the expected energy is $-2.8$ even though an optimal coloring is measured only half the time.

Two useful evaluation metrics are therefore:

- **Expected energy:** $E(\gamma,\beta)$, which the current optimizer minimizes.
- **Success probability:** $P(f(x)\le\tau) = \sum_{x:f(x)\le\tau}P(x)$, for a chosen solution-quality threshold $\tau$.

These metrics are related but not interchangeable.

## 5. What the Python simulator calculates

In [`src/sieve_qaoa.py`](../src/sieve_qaoa.py):

| Function/class | Purpose |
| --- | --- |
| `maxcut_costs(n_qubits, edges)` | Build all binary-solution costs for MaxCut. |
| `qaoa_probabilities(costs, gamma, beta)` | Compute every output probability for one $p=1$ circuit. |
| `qaoa_energy(costs, gamma, beta)` | Compute exact expected cost from those probabilities. |
| `optimize_with_recursive_sieve(...)` | Choose angles through repeated sieve-ordered coordinate scans. |
| `SieveQAOAResult` | Store chosen angles, energy, evaluation count, output probabilities, and most likely bitstring. |

The simulator starts with the cost-dependent phases:

```python
norm = 1 / sqrt(size)
state = [exp(-1j * gamma * cost) * norm for cost in values]
```

Then it loops through qubits and pairs of basis states, applying the exact two-amplitude mixer above. It returns `abs(amplitude)**2` for every output state, and the energy function computes the weighted average of costs.

This is a **classical, dense, ideal-statevector simulation**. It does not execute hardware gates or estimate energies from finite shots. Each energy evaluation works with $2^n$ amplitudes and all $2^n$ costs. The simulation uses $O(2^n)$ statevector storage and approximately $O(n2^n)$ arithmetic per energy evaluation.

## 6. How the recursive dyadic sieve selects angles

The [recursive sieve](../src/recursive_dyadic_sieve.py) outputs all $b$-bit integers exactly once, with zero last. At each dyadic refinement level, it uses **bit-reversed order within that level**.

For $b=4$, the order is:

```text
8, 4, 12, 2, 10, 6, 14, 1,
9, 5, 13, 3, 11, 7, 15, 0
```

The optimizer maps each integer to an angle:

```math
\theta_k = \frac{2\pi k}{2^b}.
```

With the default `angle_bits=4`, there are 16 grid angles separated by $\pi/8$. The first eight candidates are:

| Visit | Key $k$ | Angle $\theta_k$ |
| ---: | ---: | --- |
| 1 | 8 | $\pi$ |
| 2 | 4 | $\pi/2$ |
| 3 | 12 | $3\pi/2$ |
| 4 | 2 | $\pi/4$ |
| 5 | 10 | $5\pi/4$ |
| 6 | 6 | $3\pi/4$ |
| 7 | 14 | $7\pi/4$ |
| 8 | 1 | $\pi/8$ |

The effect is **broad coverage before local refinement**. The precise ordering, not merely the set of grid points, is what the experiment investigates.

The original [ascending-within-level sieve](../src/dyadic_sieve.py) has a different four-bit order:

```text
8, 4, 12, 2, 6, 10, 14,
1, 3, 5, 7, 9, 11, 13, 15, 0
```

Both cover the same full grid; the within-level ordering differs.

### 6.1 Coordinate-wise optimization

The optimizer does **not** scan all $16^2=256$ parameter pairs. It performs coordinate scans:

1. Start at $(\gamma,\beta)=(\pi/4,\pi/8)$; evaluate the baseline energy.
2. Hold $\beta$ fixed, try all grid values of $\gamma$ in recursive sieve order; retain the best.
3. Hold that $\gamma$ fixed, scan all grid values of $\beta$; retain the best.
4. Repeat for `sweeps` rounds (default: two).

The actual scan code keeps the best candidate while evaluating each proposal against the **same fixed other angle**. It updates the chosen coordinate at the end of the scan or at an early stop. It keeps a candidate only when the improvement exceeds a small numerical tolerance.

At the defaults `angle_bits=4` and $sweeps=2$:

```math
\text{counted energy evaluations}
=1+(2\text{ coordinates})(2\text{ sweeps})(16\text{ grid values})
=\boxed{65}.
```

The separate baseline call in the example script and the final calculation of output probabilities are not counted in the optimizer's returned `evaluations` field. Each counted evaluation is an *exact statevector energy evaluation*, not one hardware measurement.

### 6.2 Stopping and budget controls

The optimizer accepts:

- `angle_bits` — grid resolution (default $4$).
- `sweeps` — number of gamma/beta scan rounds (default $2$).
- `initial_angles` — default $(\pi/4,\pi/8)$, deliberately nonzero.
- `target_energy` — stop when the best expected energy is low enough.
- `max_evaluations` — cap the number of counted exact energy evaluations, including the first one.

Starting with both angles zero can make a one-coordinate scan flat in this ansatz; the chosen nonzero start avoids that trivial stall in the example.

**Why ordering matters:** A complete scan over the same angle grid reaches the same best energy for that *fixed coordinate and other-angle value*, regardless of candidate order. With **early stopping or a limited evaluation budget**, candidate order can determine how quickly a satisfactory angle is encountered. Multi-sweep trajectories can also differ at ties.

For the four-cycle, with beta fixed at $\pi/8$, the recursive sieve reaches gamma $3\pi/4$ on the sixth gamma trial. Including the baseline, `target_energy=-2.9` can be reached after **seven counted evaluations**. That is an illustration of early stopping in this single problem, not evidence that the sieve is universally faster.

## 7. The four-cycle result explained analytically

For precisely this four-cycle, this negative-cut Hamiltonian, and this $p=1$ mixer convention, the QAOA energy simplifies to

```math
\boxed{E(\gamma,\beta)
=-2+\sin(4\beta)\sin(2\gamma).}
```

This formula can be used as an independent mathematical check of the reported energy values.

**Initial angles:**

```math
\begin{aligned}
\gamma_0&=\pi/4,\qquad \beta_0=\pi/8,\\
E(\gamma_0,\beta_0)
&=-2+\sin(\pi/2)\sin(\pi/2)=-1.
\end{aligned}
```

**Optimized angles:**

```math
\begin{aligned}
\gamma_*&=3\pi/4\approx2.35619,\\
\beta_*&=\pi/8\approx0.39270,\\
E(\gamma_*,\beta_*)
&=-2+\sin(\pi/2)\sin(3\pi/2)\\
&=\boxed{-3}.
\end{aligned}
```

Since the product of sines is between $-1$ and $1$, **$-3$ is a global minimum of the $p=1$ expected-energy landscape for this graph and convention**. It is **not** the best possible individual MaxCut cost, which remains $-4$.

At the optimized parameters, the simulated output probabilities grouped by cut size are:

| Cut size | Cost | Total probability |
| ---: | ---: | ---: |
| 0 | 0 | $1/32 = 3.125\%$ |
| 2 | -2 | $14/32 = 43.75\%$ |
| 4 | -4 | $17/32 = 53.125\%$ |

The two optimal bitstrings `0101` and `1010` each have probability $17/64 = 26.5625\%$, or $53.125\%$ together. Checking the expectation:

```math
E=0(1/32)-2(14/32)-4(17/32)=-3.
```

The average cut size is $3$, versus a maximum cut of $4$: an **expected cut approximation ratio of 75%** for this example. The **53.125% optimal-cut probability** is a different statistic. For comparison, a genuinely uniform random bitstring yields one of the two optimal colorings with probability $2/16=12.5\%$ and expected energy $-2$. The chosen initial QAOA angles have expected energy $-1$, so they are not a uniform-random baseline.

## 8. Connection to the previously proved sieve theorem

The repository's mathematical analysis concerns a **different search problem**: enumerating $N=2^n$ integer-ordered keys and stopping upon the first hit in a **single contiguous successful interval** of length $m=2^r$. For $2\le m\le N$, assuming the interval start is uniformly distributed over all valid positions, the original sieve has expected first-hit trial

```math
\boxed{
\mathbb{E}[T]
=\frac{N(N-m+2)}{2m(N-m+1)}.
}
```

The associated **integer first-hit sum identity** for the original sieve is machine-checked in Lean in [`lean/FirstHitSum.lean`](../lean/FirstHitSum.lean). The uniform expectation follows mathematically by dividing by the number of starts. The recursive variant has been checked numerically for this special cluster model but has not received the same Lean proof. The owner previously reported a successful Lean build (19 jobs).

That theorem does **not** imply an advantage for arbitrary QAOA energy landscapes. For parameter optimization, a successful set at threshold $\tau$ is

```math
S_\tau=\{(\gamma,\beta): E(\gamma,\beta)\le\tau\}.
```

This is generally **two-dimensional, periodic, possibly disconnected**, and dependent on the circuit and problem. Even a one-coordinate slice may have multiple separated low-energy intervals. The contiguous-cluster theorem does not directly describe these sets.

The useful *hypothesis* is narrower: coarse-to-fine ordering might find an acceptable parameter sooner than another ordering **under a matched evaluation budget**.

## 9. What the working model establishes—and what it does not

**Established in code/documentation:**

- A real one-layer QAOA **ansatz** is simulated exactly on a classical computer.
- The recursive sieve deterministically orders the discretized $\gamma,\beta$ candidates.
- Coordinate scans, target-energy stopping, and evaluation-budget stopping are implemented.
- The documented four-vertex MaxCut run improves expected energy from $-1$ to $-3$ using $65$ counted optimizer evaluations.
- The optimized state assigns about $53.125%$ probability to the two optimal solutions.
- Seven dedicated QAOA tests were reported passing in the earlier session. Their sources are in [`tests/test_sieve_qaoa.py`](../tests/test_sieve_qaoa.py); they were **not rerun to create this document**.

**Not established:**

- No quantum hardware run, finite-shot study, or noise model.
- No observed reduction in real hardware cost.
- No comparison yet against the original sieve, ordinary grid, random ordering, Sobol/Halton, or conventional parameter optimizers at matched budgets.
- No theorem implying faster QAOA training or generic quantum advantage.
- No proof that the recursive sieve is preferable on arbitrary periodic, fragmented, noisy, or higher-dimensional parameter landscapes.
- No scalable large-$n$ simulation: storing the dense statevector and cost array grows exponentially.

A coordinate scan may miss the best **joint** angle pair, because moving one coordinate at a time need not find the minimum of a coupled multidimensional surface. The present four-cycle happens to reach a global minimum of its $p=1$ energy landscape.

This is also **not Grover search**: Grover amplifies binary solution states marked by a coherent oracle; the present optimizer searches classical encodings of *circuit angles* and computes expected energies through exact classical simulation.

## 10. How to run and verify

From the repository root with Python 3.11+ (no third-party Python runtime dependencies for this draft):

```bash
python examples/sieve_qaoa_maxcut.py
python -m unittest discover -s tests -v
```

The example prints initial/optimized expected energies, angles, optimizer evaluation count, most likely bitstring, and top outcomes. A separate Lean verification is optional for Python-only work:

```bash
lake -d lean build
```

Lean is presently paused: **do not add more proofs without an explicit request**. Keep `src/` flat and the Lean setup minimal, per [`AGENTS.md`](../AGENTS.md).

## 11. The next fair experiment (not performed here)

The natural next step, **only when requested**, is a controlled comparison of:

1. Recursive bit-reversal sieve (current method).
2. Original ascending-within-level dyadic sieve.
3. Ordinary grid or randomized grid order.
4. Where appropriate, Sobol/Halton sampling and conventional optimizers such as Rotosolve.

For each method, compare **time to reach an energy threshold**, **best energy under equal evaluation budgets**, and **probability of measuring a satisfactory binary solution**. Use multiple MaxCut graphs and thresholds; distinguish ideal exact-energy calls, classical function evaluations, circuit executions, and hardware shots. Do not equate them.

For a *fixed* angle grid with exhaustive evaluation, different visit orders do not create a better minimum over that same set. The practical hypothesis concerns **early discovery**, **budget-constrained performance**, and possibly **parameter initialization**, not magic improvements from reordering a completed grid scan.

---

## Short mental model

> **QAOA** maps angle settings to a probability distribution over solutions. **The cost operator** encodes objective-dependent phases; **the mixer** turns phase relations into interference and changed probabilities. **The classical outer loop** tunes angles to reduce expected cost. **The recursive dyadic sieve** decides which discretized angles to evaluate first. Its potential contribution is reaching useful settings sooner when evaluations are limited—not searching the bitstrings directly, and not an established quantum speedup.
