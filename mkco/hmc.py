"""Hierarchical Max-Cut (HMC): layering by recursive Ising bisection.

The layer index of a gate is built bit by bit.  At each node of the recursion
the gates S that must fit into K consecutive layers are split into an early
half (K1 = ceil(K/2) layers) and a late half (K2 = K - K1 layers) by solving

    min_z  E(z) = sum_r w_r (sum_{i in S, r in res(i)} z_i - tau_r)^2
                + P * #{dependencies u -> v with u late and v early}

with z_i = +1 (early) / -1 (late) and tau_r = n_r (K1 - K2) / K.  Expanding
the square gives Max-Cut couplings J_uv = sum of shared resource weights plus
local fields: Max-Cut on the conflict multigraph is *exactly* per-wire load
balancing (docs/THEORY.md, Theorem 4).  If every split is perfectly
balanced the leaves are proper layers, so HMC attains the max-load bound.

Every node is an Ising problem with |S| spins (log-encoding: a whole
K-layering needs only n*ceil(log2 K) spins in total, versus n*K for one-hot
colouring QUBOs), so the same code drives classical and quantum solvers:

    'sa'     simulated annealing on resource sums (default, scalable)
    'bm'     Burer-Monteiro rank-r SDP relaxation + Goemans-Williamson rounding
    'qaoa'   QAOA (state-vector simulation, small sub-problems)
    'exact'  exhaustive enumeration (small sub-problems)

Sub-problems can also be exported as (h, J) Ising dictionaries for annealers.
"""
from __future__ import annotations

import math
import time

import numpy as np

from .maxkcut import compact, used_layers


class IsingSplit:
    """One bisection sub-problem."""

    def __init__(self, model, S, K, res, penalty=None):
        self.model = model
        self.S = list(S)
        self.n = len(self.S)
        self.K = K
        self.K1 = (K + 1) // 2
        self.K2 = K - self.K1
        self.pos = {i: j for j, i in enumerate(self.S)}
        # resources -> local gate lists
        rmap = {}
        for j, i in enumerate(self.S):
            for r in res[i]:
                rmap.setdefault(int(r), []).append(j)
        self.rkeys = list(rmap)
        self.rmembers = [np.array(rmap[r], dtype=np.int64) for r in self.rkeys]
        nr = len(self.rkeys)
        self.tau = np.array([len(m) * (self.K1 - self.K2) / K for m in self.rmembers])
        self.gres = [[] for _ in range(self.n)]
        for ri, mem in enumerate(self.rmembers):
            for j in mem:
                self.gres[j].append(ri)
        self.gres = [np.array(x, dtype=np.int64) for x in self.gres]
        # local precedence through runs: preds/succs restricted to S
        self.lpred = [[] for _ in range(self.n)]
        for j, i in enumerate(self.S):
            for p in model.preds[i]:
                for g in model.run_unit_members[p]:
                    jj = self.pos.get(model.unit_index[g])
                    if jj is not None:
                        self.lpred[j].append(jj)
        self.lsucc = [[] for _ in range(self.n)]
        for j, ps in enumerate(self.lpred):
            for p in ps:
                self.lsucc[p].append(j)
        self.has_prec = any(self.lpred)
        # local heads/tails -> fixings
        order = sorted(range(self.n), key=lambda j: self.S[j])   # original order is topological
        head = np.zeros(self.n, dtype=np.int64)
        for j in order:
            for p in self.lpred[j]:
                head[j] = max(head[j], head[p] + 1)
        tail = np.zeros(self.n, dtype=np.int64)
        for j in reversed(order):
            for s in self.lsucc[j]:
                tail[j] = max(tail[j], tail[s] + 1)
        self.head, self.tail = head, tail
        self.fixed = np.zeros(self.n, dtype=np.int64)   # 0 free, +1 early, -1 late
        self.fixed[head >= self.K1] = -1
        early = tail >= self.K2
        self.infeasible = bool(np.any(early & (self.fixed == -1)))
        self.fixed[early] = 1
        self.P = penalty if penalty is not None else 2.0 + float(nr)

    # ----------------------------------------------------------------- energy
    def energy(self, z):
        e = 0.0
        for ri, mem in enumerate(self.rmembers):
            e += (z[mem].sum() - self.tau[ri]) ** 2
        if self.has_prec:
            v = 0
            for j in range(self.n):
                if z[j] > 0:
                    v += sum(1 for p in self.lpred[j] if z[p] < 0)
            e += self.P * v
        return e

    def ising(self):
        """Return (h, J, offset) with E(z) = offset + sum h_i z_i + sum_{i<j} J_ij z_i z_j."""
        h = np.zeros(self.n)
        J = {}
        off = 0.0
        for ri, mem in enumerate(self.rmembers):
            tau = self.tau[ri]
            off += len(mem) + tau * tau
            for a in range(len(mem)):
                h[mem[a]] += -2 * tau
                for b in range(a + 1, len(mem)):
                    key = (min(mem[a], mem[b]), max(mem[a], mem[b]))
                    J[key] = J.get(key, 0.0) + 2.0
        P = self.P
        for v in range(self.n):
            for u in self.lpred[v]:       # penalty P (1 - z_u)(1 + z_v) / 4
                off += P / 4
                h[v] += P / 4
                h[u] += -P / 4
                key = (min(u, v), max(u, v))
                J[key] = J.get(key, 0.0) - P / 4
        return h, J, off

    def energies_all(self):
        """Energy of all 2^n assignments (small n only)."""
        n = self.n
        idx = np.arange(2 ** n, dtype=np.int64)
        Z = 1 - 2 * ((idx[:, None] >> np.arange(n)[None, :]) & 1)      # bit 0 -> +1 (early)
        E = np.zeros(2 ** n)
        for ri, mem in enumerate(self.rmembers):
            E += (Z[:, mem].sum(axis=1) - self.tau[ri]) ** 2
        if self.has_prec:
            for v in range(n):
                for u in self.lpred[v]:
                    E += self.P * ((Z[:, u] < 0) & (Z[:, v] > 0))
        bad = np.zeros(2 ** n, dtype=bool)
        for j in range(n):
            if self.fixed[j]:
                bad |= Z[:, j] != self.fixed[j]
        E[bad] += 1e6
        return E, Z

    # ---------------------------------------------------------------- solvers
    def solve(self, backend="sa", rng=None, **kw):
        rng = rng or np.random.default_rng(0)
        free = int((self.fixed == 0).sum())
        if free == 0:
            return self.fixed.astype(float).copy()
        if backend == "exact" or (backend in ("sa", "bm") and self.n <= kw.get("exact_limit", 12)):
            return self._exact()
        if backend == "qaoa":
            if self.n <= kw.get("qaoa_limit", 14):
                return self._qaoa(rng, p=kw.get("p", 3))
            backend = "sa"
        if backend == "bm":
            z = self._bm(rng, rank=kw.get("rank", 8), iters=kw.get("bm_iters", 300),
                         rounds=kw.get("rounds", 32))
            return self._sa(rng, z0=z, sweeps=kw.get("polish_sweeps", 20), T0=0.3)
        return self._sa(rng, sweeps=kw.get("sweeps", 120))

    def _exact(self):
        E, Z = self.energies_all()
        return Z[int(np.argmin(E))].astype(float)

    def _flip_delta(self, z, Sr, j, early_cnt, late_cnt):
        zj = z[j]
        rs = self.gres[j]
        d = float((4.0 - 4.0 * zj * (Sr[rs] - self.tau[rs])).sum())
        if self.has_prec:
            lp = late_cnt[j]
            es = early_cnt[j]
            dv = (es - lp) if zj > 0 else (lp - es)
            d += self.P * dv
        return d

    def _sa(self, rng, z0=None, sweeps=120, T0=None):
        n = self.n
        z = np.where(self.fixed != 0, self.fixed, 0).astype(float)
        free = np.flatnonzero(self.fixed == 0)
        if z0 is not None:
            z[free] = np.sign(z0[free]) + (z0[free] == 0)
        else:
            z[free] = rng.choice([-1.0, 1.0], size=len(free))
        Sr = np.array([z[m].sum() for m in self.rmembers])
        # neighbour side counts for precedence (late preds / early succs of each gate)
        late_pred = np.array([sum(1 for p in self.lpred[j] if z[p] < 0) for j in range(n)])
        early_succ = np.array([sum(1 for s in self.lsucc[j] if z[s] > 0) for j in range(n)])
        T0 = T0 if T0 is not None else 2.0 + 0.5 * max(1, max((len(m) for m in self.rmembers), default=1))
        T1 = 0.05
        total = max(1, sweeps)
        best_z, best_e = z.copy(), self.energy(z)
        for sw in range(total):
            T = T0 * (T1 / T0) ** (sw / max(1, total - 1))
            for j in rng.permutation(free):
                d = self._flip_delta(z, Sr, j, early_succ, late_pred)
                if d <= 0 or rng.random() < math.exp(-d / T):
                    old = z[j]
                    z[j] = -old
                    Sr[self.gres[j]] -= 2 * old
                    if self.has_prec:
                        became_late = old > 0
                        for s in self.lsucc[j]:
                            late_pred[s] += 1 if became_late else -1
                        for p in self.lpred[j]:
                            early_succ[p] += -1 if became_late else 1
            e = self.energy(z)
            if e < best_e:
                best_e, best_z = e, z.copy()
        return best_z

    def _bm(self, rng, rank=8, iters=300, rounds=32, lr=0.05):
        """Rank-r Burer-Monteiro relaxation of E(z), then GW hyperplane rounding."""
        n = self.n
        V = rng.normal(size=(n, rank))
        V /= np.linalg.norm(V, axis=1, keepdims=True)
        v0 = np.zeros(rank)
        v0[0] = 1.0
        fixed = self.fixed
        V[fixed != 0] = np.outer(fixed[fixed != 0], v0)
        free = fixed == 0
        P = self.P
        for it in range(iters):
            grad = np.zeros_like(V)
            for ri, mem in enumerate(self.rmembers):
                g = 2 * (V[mem].sum(axis=0) - self.tau[ri] * v0)
                grad[mem] += g
            if self.has_prec:
                for v in range(n):
                    for u in self.lpred[v]:
                        # P/4 (1 + v0.Vv - v0.Vu - Vu.Vv)
                        grad[v] += P / 4 * (v0 - V[u])
                        grad[u] += P / 4 * (-v0 - V[v])
            # Riemannian step on the sphere
            grad -= (grad * V).sum(axis=1, keepdims=True) * V
            V[free] -= lr * grad[free]
            V[free] /= np.linalg.norm(V[free], axis=1, keepdims=True)
        best_z, best_e = None, np.inf
        for _ in range(rounds):
            g = rng.normal(size=rank)
            s0 = 1.0 if v0 @ g >= 0 else -1.0
            z = np.where(V @ g >= 0, 1.0, -1.0) * s0
            z[fixed != 0] = fixed[fixed != 0]
            e = self.energy(z)
            if e < best_e:
                best_e, best_z = e, z
        return best_z

    def _qaoa(self, rng, p=3, restarts=4, shots_top=64):
        """QAOA with exact state-vector simulation; returns the best sampled string."""
        from scipy.optimize import minimize
        E, Z = self.energies_all()
        n = self.n
        valid = E < 1e5
        Emin, Emax = E[valid].min(), E[valid].max()
        En = (E - Emin) / max(Emax - Emin, 1e-9)
        En[~valid] = 2.0                       # penalise fixings softly in the cost layer
        N = 2 ** n

        def state(params):
            g, b = params[:p], params[p:]
            psi = np.full(N, 1 / math.sqrt(N), dtype=complex)
            for layer in range(p):
                psi *= np.exp(-1j * g[layer] * math.pi * En)
                c, s = math.cos(b[layer]), -1j * math.sin(b[layer])
                t = psi.reshape([2] * n)
                for q in range(n):
                    t = c * t + s * np.flip(t, axis=q)
                psi = t.reshape(N)
            return psi

        def cost(params):
            psi = state(params)
            return float((np.abs(psi) ** 2 * En).sum())

        best = None
        for _ in range(restarts):
            x0 = np.concatenate([rng.uniform(0, 1, p) * np.linspace(0.3, 1.0, p),
                                 rng.uniform(0, 0.5, p) * np.linspace(1.0, 0.3, p)])
            r = minimize(cost, x0, method="COBYLA", options={"maxiter": 200})
            if best is None or r.fun < best.fun:
                best = r
        probs = np.abs(state(best.x)) ** 2
        top = np.argsort(-probs)[:shots_top]
        k = top[int(np.argmin(E[top]))]
        self.qaoa_info = {"expected_cost": best.fun, "p": p,
                          "prob_of_optimum": float(probs[E == E.min()].sum()),
                          "best_sampled_is_optimal": bool(E[k] <= E.min() + 1e-9)}
        return Z[k].astype(float)


def hmc_assign(model, K, backend="sa", seed=0, deadline=None, caps=None, **kw):
    """Recursive bisection of all unit gates into K layers (slots may conflict)."""
    rng = np.random.default_rng(seed)
    res = model.unit_resources()
    nu = len(model.unit)
    slots = np.zeros(nu, dtype=np.int64)
    info = {"nodes": 0, "infeasible_nodes": 0, "qaoa": []}

    def rec(S, a, K_):
        if not S or K_ <= 1:
            for i in S:
                slots[i] = a
            return
        if deadline is not None and time.time() > deadline:
            # out of time: spread remaining gates greedily by original order
            for j, i in enumerate(sorted(S)):
                slots[i] = a + min(K_ - 1, j * K_ // max(1, len(S)))
            return
        sp = IsingSplit(model, S, K_, res)
        info["nodes"] += 1
        if sp.infeasible:
            info["infeasible_nodes"] += 1
        z = sp.solve(backend, rng=rng, **kw)
        if backend == "qaoa" and hasattr(sp, "qaoa_info"):
            info["qaoa"].append(sp.qaoa_info)
        early = [sp.S[j] for j in range(sp.n) if z[j] > 0]
        late = [sp.S[j] for j in range(sp.n) if z[j] <= 0]
        rec(early, a, sp.K1)
        rec(late, a + sp.K1, sp.K2)

    rec(list(range(nu)), 0, K)
    return slots, info


def legalize(model, target_slots, caps=None):
    """Serial schedule generation with priority = HMC slot (always feasible)."""
    from .schedule import serial_sgs
    t = np.asarray(target_slots, dtype=float)
    prio = t + np.arange(len(t)) * 1e-9          # ties: original order
    return compact(serial_sgs(model, prio, caps))


def hmc_schedule(model, lb, ub, backend="sa", time_limit=5.0, seed=0, **kw):
    """Try budgets K in [lb, ub]; return the best legalised layering found."""
    t0 = time.time()
    best, best_layers = None, None
    tried = []
    for K in range(max(1, lb), ub + 1):
        if time.time() - t0 > time_limit:
            break
        target, info = hmc_assign(model, K, backend=backend, seed=seed,
                                  deadline=t0 + time_limit, **kw)
        s = legalize(model, target)
        tried.append({"K": K, "layers": used_layers(s), "nodes": info["nodes"]})
        if best is None or used_layers(s) < best_layers:
            best, best_layers = s, used_layers(s)
        if best_layers <= lb:
            break
    return best, {"tried": tried, "time": time.time() - t0}
