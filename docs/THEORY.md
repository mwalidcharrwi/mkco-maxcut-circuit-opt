# MKCO — theory

Notation. A circuit is a sequence of gates `g_1 … g_N`. `supp(g)` is the set of
wires (qubits and classical bits) that `g` touches. Two gates *conflict* when
their supports intersect. For a layering, *unit* gates take one layer;
*zero-duration* gates (single-wire gates when the objective is the two-qubit
depth) take none.

---

## 1. Commutation and equivalent reorderings

**Lemma 1 (axis rule).** Let `A`, `B` be unitaries with shared qubits `S`. Suppose
that for every `q ∈ S` there is one Bloch direction `n_q` such that both
`A` and `B` commute with `P_q = n_q·σ_q`, or one of them acts as the identity
on `q`. Then `AB = BA`.

*Proof.* The operators `{P_q}_{q∈S}` commute pairwise and each has a
non-degenerate spectrum `{±1}` on its qubit. Let `Π_x` (`x ∈ {±1}^S`) be the
joint eigenprojectors. Because `A` commutes with every `P_q`, it is
block-diagonal: `A = Σ_x Π_x ⊗ A_x`, where `A_x` acts on `supp(A)∖S`.
Likewise `B = Σ_x Π_x ⊗ B_x` with `B_x` on `supp(B)∖S`. These two sets are
disjoint, so `A_x ⊗ I` and `I ⊗ B_x` commute, and therefore
`AB = Σ_x Π_x ⊗ A_x B_x = BA`. ∎

For every gate and every qubit it touches, MKCO computes the *axis* `n_q` from
the gate's unitary. It solves the real null space of
`[ [U,X_q], [U,Y_q], [U,Z_q] ]`, which gives `Z`, `X`, `Y`, a general direction,
`I`, or "none". `tests/test_core.py` checks Lemma 1 exhaustively against exact
matrices for every pair of library gates.

**Runs.** On each wire, MKCO groups consecutive gates with the same axis into
maximal *runs*. Gates in consecutive runs of a wire do not commute (by the
rule), so every gate of run `r` must precede every gate of run `r+1`. Call the
resulting partial order `≺`.

**Lemma 2 (trace equivalence).** Every linear extension of `≺` implements the
same unitary as the input, up to global phase. `≺` is exactly the transitive
closure of "`g_i` before `g_j`, they share a wire, and they do not commute by
the rule". It is stored in `O(Σ_g |supp(g)|)` memory, with no quadratic edge
list.

*Proof.* Take the commutation relation of gate instances as the independence
relation of a Mazurkiewicz trace monoid. Two words over the same gate
instances are trace-equivalent iff every pair of dependent instances keeps its
relative order. Trace-equivalent words are connected by swaps of adjacent
independent letters, and each such swap preserves the unitary by Lemma 1.

Now show that the run order generates exactly the dependent pairs.
- Non-commuting gates sharing a wire `w` lie in different runs of `w`, so they
  are ordered by the chain of consecutive runs between them.
- Conversely, each arc between consecutive runs joins gates whose axes differ
  on `w`, so that pair is dependent. ∎

**Corollary (independent audit).** A reordering is correct whenever every pair
of gates whose relative order changed and which share a qubit commutes.
`mkco/verify.py` enumerates exactly those inverted pairs and checks
`[A,B]=0` numerically on their joint support. The check does not use the
run/axis machinery, so it independently verifies the optimizer.

## 2. Depth minimisation = mixed-graph colouring

A *layering* is a map `ℓ : unit gates → {0,…,k−1}` with:
- `ℓ(u) < ℓ(v)` whenever `u ≺ v` (precedence arcs);
- `ℓ(u) ≠ ℓ(v)` whenever `u, v` conflict (edges).

This is a colouring of the *mixed graph* `M = (V, A, E)`.

**Theorem 1.** The minimum depth over all reorderings permitted by Lemma 2
equals the mixed chromatic number `χ(M)`. If `≺` is empty (a commuting
circuit), this is Lee–Jeong–Kim's reduction to vertex colouring (their Claim 7
and Proposition 8).

*Proof.*
- (≤) Sort the gates by `ℓ`, breaking ties by original index. This is a linear
  extension of `≺`, and its ASAP depth is at most `k`, because gates in the same
  layer are pairwise disjoint.
- (≥) The ASAP layering of any linear extension is a valid `ℓ` with
  `k = depth`. ∎

*Zero-duration gates.* Emit with key `(slot, duration, original index)`, where
a zero-duration gate's slot is one past its preceding unit run. Then
precedence is preserved and the weighted ASAP depth is at most `k`. This is
implemented in `schedule.emit_order`, and every output is re-checked
structurally.

## 3. The Max-k-Cut formulation

Weight each conflicting pair by `w(u,v) = |supp(u) ∩ supp(v)|`, which gives the
*conflict multigraph*. For a layering into `k` slots, let `occ[t,q]` be the
number of gates in layer `t` that touch wire `q`.

**Theorem 2.**

`Φ_k(ℓ) := Σ_{t,q} C(occ[t,q], 2) = Σ_{u<v : ℓ(u)=ℓ(v)} w(u,v) = w(E) − Cut_k(ℓ)`.

So a `k`-layer circuit exists iff the precedence-constrained weighted
**Max-k-Cut** of the conflict multigraph cuts all of `w(E)` (equivalently,
`min Φ_k = 0`). Proof: count the pairs `{u,v}` per (layer, wire). ∎

What this buys:
1. **Depth budget.** For a fixed hardware or latency budget `k`, Max-k-Cut
   gives the "least conflicting" `k`-layer schedule. Plain colouring has no
   notion of a near-miss.
2. **Soft constraints.** Any extra pairwise penalty (crosstalk, frequency
   collisions, shared control lines) becomes an edge with weight `0 < w < 1`.
   MKCO adds it as a *soft resource* of capacity 1, so
   `Φ = Σ_r w_r · C(max(0, occ − c_r) + 1, 2)`.
3. **Capacities.** Wire capacity `c_q > 1` models ancilla fan-out copies of a
   diagonal (single-axis) wire. This makes the "parallelisation by extra
   qubits" of Lee et al. (§5.2) a capacitated Max-k-Cut.
4. **Scalability.** `Φ` and its move deltas cost `O(|supp(g)|)` per gate.
   The `O(n²)` conflict graph of Lee et al.'s Algorithm 1 is never built.

**Proposition 3 (repair bound).** Let `ℓ` be a `k`-layering whose
monochromatic graph `H_t` in layer `t` is non-empty. Splitting each layer into
`χ(H_t)` sub-layers gives a valid layering of depth `Σ_t χ(H_t)`, which is at
most `k + Σ_t (½ + √(2|E(H_t)|+¼) − 1)`. A near-feasible Max-k-Cut therefore
certifies a near-optimal circuit.

## 4. Max-Cut is per-wire load balancing (hierarchical Max-Cut)

Split a gate set `S` into an early and a late half with spins `z_i = ±1`. Let
`S_q = Σ_{i ∋ q} z_i` and `n_q = |{i ∈ S : q ∈ supp(i)}|`.

**Theorem 4.** `Σ_{u<v} w(u,v) z_u z_v = ½ Σ_q (S_q² − n_q)`. So maximising
the cut of the conflict multigraph is the same as minimising the per-wire
discrepancy `Σ_q S_q²`. For unequal halves (`K1 ≠ K2` layers), minimising
`Σ_q (S_q − τ_q)²` with `τ_q = n_q (K1−K2)/K` adds only local fields: it is
still an Ising/Max-Cut instance.

**Corollary 5 (when HMC is optimal).** Recursive bisection assigns every gate
a `⌈log₂ K⌉`-bit layer index. If every node of the recursion admits a split in
which each wire puts at most `K1` gates early and at most `K2` gates late,
then the leaves are proper layers. With `K = max_q n_q`, HMC then meets the
lower bound of Lee et al.'s Eq. (2) and is optimal.

*Example.* A commuting circuit of two-qubit gates whose interaction multigraph
is bipartite with maximum degree `Δ = 2^h` admits such splits (Euler
partitions). This recovers König's edge-colouring theorem. It is the case of
Draper's adder core, where HMC returns the optimum `n`.

*Precedence.* Arcs `u → v` become penalties `P·(1−z_u)(1+z_v)/4`. These are
quadratic, so a precedence-constrained bisection is still a QUBO. Local
heads and tails fix spins that cannot be on one side.

**Proposition 6 (qubit-efficient quantum encoding).** A `K`-layering of `n`
gates needs `n⌈log₂ K⌉` spins in total, over `⌈log₂ K⌉` Ising sub-problems
of at most `n` spins each. A one-hot colouring QUBO needs `nK` binary
variables plus penalty terms. Each HMC node can be solved by Goemans–Williamson
(SDP + hyperplane rounding), simulated annealing, QAOA, or a quantum annealer.
`mkco/hmc.py` implements the first three plus exact enumeration, and exports
`(h, J)`.

## 5. Certified lower bounds

Let `head(g)` be the earliest layer `g` can start in, and `tail(g)` the number
of layers that must follow it. A run's members share a wire, so they are
serialised. The earliest completion of a predecessor run is therefore the
single-machine schedule of its members with release dates equal to their
heads (Jackson's rule). Tails are the mirror image.

**Theorem 7.** `LB = max( max_g head(g)+tail(g)+1 , max_q J_q )` is a lower
bound on the depth of every equivalent reordering. Here `J_q` is the optimal
makespan of wire `q`'s gates viewed as unit jobs with release `head` and tail
`tail`, which the largest-tail-first rule solves exactly. `LB` dominates both
the critical path and Lee et al.'s Eq. (2). *Proof:* induction over `≺`
(every bound is a relaxation of the true schedule). ∎

When `depth(output) = LB`, the output is **certified optimal**: no reordering
can do better.

## 6. Window decomposition (general circuits)

**Proposition 8 (window isolation).** Take a feasible layering and a window of
layers `[a,b]`, and let `W` be the gates in it. Every chain between two gates
of `W` stays inside `[a,b]`. Moving `W` into `[a,b−1]` and shifting the later
layers down by one is therefore feasible iff `W` alone admits a
`(b−a)`-colouring of its mixed sub-graph. That is an isolated, small
precedence-constrained Max-k-Cut. MKCO solves these windows with exact
enumeration (or tabu / QAOA) inside a large-neighbourhood search, with
forward–backward justification between sweeps.
