"""Precedence-constrained weighted Max-k-Cut engine.

For a depth budget k we look for a layer map s: gates -> {0..k-1} that

    maximises   sum_{conflicting pairs u,v} w_uv [s(u) != s(v)]      (Max-k-Cut)
    subject to  s(u) < s(v) for every dependency u -> v              (precedence)

which is the same as minimising the weight of monochromatic conflict edges
(Min-k-Partition).  A k-layer circuit exists iff the optimum cuts every hard
edge (docs/THEORY.md, Theorem 2).

Conflicts are never materialised as an edge list.  A gate occupies resources
(its wires, plus optional soft resources such as crosstalk groups); with
capacity c_r and weight w_r per resource the objective is

    Phi(s) = sum_{t, r} w_r * C(max(0, occ[t, r] - c_r) + 1, 2)

For c_r = 1 this is exactly the number of monochromatic edges of the
multigraph with edge multiplicity |res(u) & res(v)|, so Phi = 0 iff the
layering is proper.  Memory and per-move cost are O(arity) instead of O(n).

The search is a TabuCol-style local search (Hertz & de Werra 1987; Galinier &
Hao 1999) generalised with precedence windows, plus k-descent: once a
conflict-free k-layering is found, k is decreased.
"""
from __future__ import annotations

import time

import numpy as np

BIG = 1 << 60


class MaxKCutState:
    def __init__(self, model, k, caps=None, soft=None, seed=0):
        """soft: optional list (per unit gate) of extra soft-resource ids and a
        dict {'num': R_soft, 'weight': array} describing them."""
        self.m = model
        self.k = int(k)
        self.rng = np.random.default_rng(seed)
        nu = len(model.unit)
        self.nu = nu
        nw = model.num_wires
        res = [list(r) for r in model.unit_resources()]
        n_soft = 0
        soft_w = np.zeros(0)
        if soft is not None:
            n_soft = soft["num"]
            soft_w = np.asarray(soft["weight"], dtype=float)
            for i, extra in enumerate(soft["res"]):
                res[i].extend(nw + e for e in extra)
        self.res = [np.array(r, dtype=np.int64) for r in res]
        self.R = nw + n_soft
        cap = np.ones(self.R, dtype=np.int64)
        if caps is not None:
            cap[:nw] = np.asarray(caps, dtype=np.int64)
        self.cap = cap
        self.wt = np.concatenate([np.ones(nw), soft_w]).astype(float)
        self.hard = np.concatenate([np.ones(nw, dtype=bool), np.zeros(n_soft, dtype=bool)])
        self.res_cap = [self.cap[r] for r in self.res]
        self.res_wt = [self.wt[r] for r in self.res]
        self.occ = np.zeros((self.k, self.R), dtype=np.int64)
        self.slot = np.full(nu, -1, dtype=np.int64)
        self.cell = {}
        self.over_hard = set()
        self.over_soft = set()
        self.phi_hard = 0.0
        self.phi_soft = 0.0
        nr = model.num_runs
        self.run_cnt = [None] * nr
        for r in model.unit_runs:
            self.run_cnt[r] = {}
        self.run_max = np.full(nr, -1, dtype=np.int64)
        self.run_min = np.full(nr, BIG, dtype=np.int64)
        self.gruns = [model.gate_runs[g] for g in model.unit]
        self.preds = model.preds
        self.succs = model.succs
        self.has_prec = any(len(p) for p in self.preds)
        # static windows: necessary for every feasible k-layering
        self.est = np.asarray(model.head, dtype=np.int64)
        self.lst = self.k - 1 - np.asarray(model.tail, dtype=np.int64)
        # soft precedence: V = number of violated dependency pairs
        self.V = 0
        self.lam = 1.0
        self.vpairs = set()
        self.movable = None          # optional subset of gates the search may move
        self.hard_w_soft = 1000.0    # weight of a hard conflict while optimising soft cost

    # ------------------------------------------------------------- bookkeeping
    def _place(self, i, t):
        self.slot[i] = t
        occ, cap, wt = self.occ, self.cap, self.wt
        for r in self.res[i]:
            o = occ[t, r]
            inc = o - cap[r] + 1
            if inc > 0:
                if self.hard[r]:
                    self.phi_hard += wt[r] * inc
                    self.over_hard.add((t, r))
                else:
                    self.phi_soft += wt[r] * inc
                    self.over_soft.add((t, r))
            occ[t, r] = o + 1
            key = (t, r)
            s = self.cell.get(key)
            if s is None:
                self.cell[key] = {i}
            else:
                s.add(i)
        for r in self.gruns[i]:
            c = self.run_cnt[r]
            c[t] = c.get(t, 0) + 1
            if t > self.run_max[r]:
                self.run_max[r] = t
            if t < self.run_min[r]:
                self.run_min[r] = t

    def _remove(self, i):
        t = self.slot[i]
        occ, cap, wt = self.occ, self.cap, self.wt
        for r in self.res[i]:
            o = occ[t, r]
            dec = o - cap[r]
            if dec > 0:
                if self.hard[r]:
                    self.phi_hard -= wt[r] * dec
                else:
                    self.phi_soft -= wt[r] * dec
            occ[t, r] = o - 1
            if o - 1 <= cap[r]:
                (self.over_hard if self.hard[r] else self.over_soft).discard((t, r))
            self.cell[(t, r)].discard(i)
        for r in self.gruns[i]:
            c = self.run_cnt[r]
            v = c[t] - 1
            if v:
                c[t] = v
            else:
                del c[t]
                if t == self.run_max[r]:
                    self.run_max[r] = max(c) if c else -1
                if t == self.run_min[r]:
                    self.run_min[r] = min(c) if c else BIG
        self.slot[i] = -1

    def move(self, i, t):
        if self.has_prec:
            v_old = self.viol_at(i, int(self.slot[i]))
        self._remove(i)
        self._place(i, t)
        if self.has_prec:
            self.V += self.viol_at(i, t) - v_old
            self._refresh_pairs(i)

    # ------------------------------------------------------ soft precedence
    def viol_at(self, i, t):
        """Violated dependency pairs between gate i (at slot t) and its neighbours."""
        v = 0
        for p in self.preds[i]:
            if self.run_max[p] >= t:
                for s, c in self.run_cnt[p].items():
                    if s >= t:
                        v += c
        for q in self.succs[i]:
            if self.run_min[q] <= t:
                for s, c in self.run_cnt[q].items():
                    if s <= t:
                        v += c
        return v

    def viol_vec(self, i, lo, hi):
        ts = np.arange(lo, hi + 1)
        v = np.zeros(hi - lo + 1)
        for p in self.preds[i]:
            if self.run_max[p] >= lo:
                for s, c in self.run_cnt[p].items():
                    if s >= lo:
                        v[: min(s, hi) - lo + 1] += c
        for q in self.succs[i]:
            if self.run_min[q] <= hi:
                for s, c in self.run_cnt[q].items():
                    if s <= hi:
                        v[max(s, lo) - lo:] += c
        return v

    def _refresh_pairs(self, i):
        nxt, prv = self.m.next_unit_run, self.m.prev_unit_run
        for r in self.gruns[i]:
            p = prv[r]
            if p >= 0:
                key = (int(p), r)
                if self.run_max[p] >= self.run_min[r]:
                    self.vpairs.add(key)
                else:
                    self.vpairs.discard(key)
            q = nxt[r]
            if q >= 0:
                key = (r, int(q))
                if self.run_max[r] >= self.run_min[q]:
                    self.vpairs.add(key)
                else:
                    self.vpairs.discard(key)

    def _violators(self, limit=64):
        out = set()
        m = self.m
        for p, q in self.vpairs:
            lo, hi = self.run_min[q], self.run_max[p]
            for g in m.run_unit_members[p][:limit]:
                j = m.unit_index[g]
                if self.slot[j] >= lo:
                    out.add(j)
            for g in m.run_unit_members[q][:limit]:
                j = m.unit_index[g]
                if self.slot[j] <= hi:
                    out.add(j)
            if len(out) > 4 * limit:
                break
        return out

    def window(self, i):
        lo = 0
        for p in self.preds[i]:
            v = self.run_max[p] + 1
            if v > lo:
                lo = v
        hi = self.k - 1
        for s in self.succs[i]:
            v = self.run_min[s] - 1
            if v < hi:
                hi = v
        return lo, hi

    def costs(self, i, lo, hi, soft_phase=False):
        """Delta of moving gate i to every slot of [lo, hi] (inf at its own slot)."""
        r = self.res[i]
        s = self.slot[i]
        sub = self.occ[lo:hi + 1][:, r]
        cap = self.res_cap[i]
        wt = self.res_wt[i]
        hmask = self.hard[r]
        if soft_phase:      # hard conflicts become (almost) forbidden
            wt = np.where(hmask, self.hard_w_soft, wt)
        elif not hmask.all():
            wt = wt * hmask + wt * (~hmask) * 1e-3
        add = (np.maximum(0, sub - cap + 1) * wt).sum(axis=1)
        stay = (np.maximum(0, self.occ[s, r] - cap) * wt).sum()
        d = add - stay
        if lo <= s <= hi:
            d[s - lo] = np.inf
        return d

    @property
    def phi(self):
        return self.phi_hard

    # ------------------------------------------------------------ construction
    def greedy_init(self, order, target=None):
        """Place gates in a topological `order`, each in its cheapest feasible slot.

        The window is [max pred slot + 1, k - 1 - tail] which is never empty when
        k >= critical path (predecessors end by k-1-tail(p) < k-1-tail(g)).  Ties go to the slot
        closest to `target` (a scaled previous solution) or to the earliest.
        """
        tail = self.m.tail
        for i in order:
            lo = 0
            for p in self.preds[i]:
                v = self.run_max[p] + 1
                if v > lo:
                    lo = v
            hi = self.k - 1 - int(tail[i])
            if hi < lo:
                hi = lo   # only possible when k < critical path
                if hi >= self.k:
                    raise ValueError("depth budget below the critical path")
            r = self.res[i]
            sub = self.occ[lo:hi + 1][:, r]
            add = (np.maximum(0, sub - self.res_cap[i] + 1) * self.res_wt[i]).sum(axis=1)
            if target is not None:
                tie = np.abs(np.arange(lo, hi + 1) - target[i]) * 1e-4
            else:
                tie = np.arange(hi - lo + 1) * 1e-6
            t = lo + int(np.argmin(add + tie))
            self._place(i, t)
        self.recompute_precedence()

    def load_slots(self, slots):
        for i, t in enumerate(slots):
            self._place(i, int(t))
        self.recompute_precedence()

    # ---------------------------------------------------------------- search
    def _conflicting(self, soft_phase=False):
        cells = self.over_soft if soft_phase else self.over_hard
        out = set()
        for key in cells:
            out.update(self.cell[key])
        return out

    def _blockers(self, i, lo, hi, limit=48):
        out = []
        m = self.m
        for p in self.preds[i]:
            if self.run_max[p] + 1 == lo:
                mem = m.run_unit_members[p]
                if len(mem) <= limit:
                    out.extend(m.unit_index[g] for g in mem
                               if self.slot[m.unit_index[g]] == lo - 1)
        for s in self.succs[i]:
            if self.run_min[s] - 1 == hi:
                mem = m.run_unit_members[s]
                if len(mem) <= limit:
                    out.extend(m.unit_index[g] for g in mem
                               if self.slot[m.unit_index[g]] == hi + 1)
        return out

    def tabu_search(self, max_iter=200000, deadline=None, max_cands=400, soft_phase=False,
                    stall_limit=None):
        """Minimise hard conflicts (or soft cost when soft_phase).  Returns True
        when a conflict-free layering (Phi_hard = 0) is reached."""
        rng = self.rng
        tabu = {}
        prec = self.has_prec and not soft_phase
        if soft_phase:
            base = lambda: self.phi_soft + self.hard_w_soft * self.phi_hard  # noqa: E731
        else:
            base = lambda: self.phi_hard  # noqa: E731
        # score used for "best so far": conflicts plus violated dependencies
        score = (lambda: base() + self.V) if prec else base
        best_phi = score()
        best_slot = self.slot.copy()
        best_feasible = self.V == 0
        it = 0
        last_improve = 0
        stall_limit = stall_limit or max(3000, 60 * self.nu)
        while score() > 1e-12 and it < max_iter:
            if (it & 63) == 0 and deadline is not None and time.time() > deadline:
                break
            if it - last_improve > stall_limit:
                break
            conf = self._conflicting(soft_phase)
            cands = set(conf)
            if prec and self.vpairs:
                cands |= self._violators()
            if self.movable is not None:
                cands &= self.movable
            cands = list(cands)
            if len(cands) > max_cands:
                cands = list(rng.choice(cands, size=max_cands, replace=False))
            lam = self.lam
            cur = base() + lam * self.V
            best_val, best_mv = np.inf, None
            for i in cands:
                if prec:
                    lo, hi = int(self.est[i]), int(self.lst[i])
                else:
                    lo, hi = self.window(i)
                if hi <= lo and self.slot[i] == lo:
                    continue
                d = self.costs(i, lo, hi, soft_phase)
                if prec:
                    vv = self.viol_vec(i, lo, hi)
                    d = d + lam * (vv - self.viol_at(i, int(self.slot[i])))
                tb = tabu.get(i)
                if tb:
                    for t, exp in tb.items():
                        if exp > it and lo <= t <= hi and cur + d[t - lo] >= best_phi - 1e-12:
                            d[t - lo] = np.inf
                d = d + rng.random(d.shape[0]) * 1e-6
                j = int(np.argmin(d))
                if d[j] < best_val:
                    best_val, best_mv = d[j], (i, lo + j)
            if best_mv is None or not np.isfinite(best_val):
                movable = [i for i in cands if (self.lst[i] > self.est[i] if prec
                                                else self.window(i)[1] > self.window(i)[0])]
                if not movable:
                    break
                i = movable[rng.integers(len(movable))]
                lo, hi = (int(self.est[i]), int(self.lst[i])) if prec else self.window(i)
                t = int(rng.integers(lo, hi + 1))
                if t != self.slot[i]:
                    self.move(i, t)
                it += 1
                continue
            i, t = best_mv
            old = int(self.slot[i])
            self.move(i, t)
            tenure = int(rng.integers(0, 10)) + int(0.6 * (len(conf) + (len(self.vpairs) if prec else 0)))
            tabu.setdefault(i, {})[old] = it + tenure + 1
            it += 1
            if prec:   # strategic oscillation of the precedence weight
                self.lam = min(64.0, self.lam * 1.01) if self.V > 0 else max(0.5, self.lam * 0.995)
            now = score()
            if now < best_phi - 1e-12:
                best_phi = now
                best_slot = self.slot.copy()
                best_feasible = self.V == 0
                last_improve = it
        if score() > best_phi + 1e-12:
            self.reset_to(best_slot)
        self.iterations = it
        return self.phi_hard <= 1e-12 and self.V == 0

    # ------------------------------------------------------ push (chain) moves
    def push_set(self, i, t, limit=60):
        """Moves needed to put gate i at slot t while keeping every dependency.

        Moving later pushes successors forward, moving earlier pushes
        predecessors back, each by the minimal amount (an ejection chain).
        Returns {gate: new_slot} or None if more than `limit` gates move.
        Never leaves [est, lst] when t is inside gate i's static window.
        """
        m = self.m
        new = {i: t}
        stack = [i]
        fwd = t > self.slot[i]
        while stack:
            x = stack.pop()
            nx = new[x]
            runs = self.succs[x] if fwd else self.preds[x]
            for q in runs:
                if fwd and self.run_min[q] > nx:
                    continue
                if not fwd and self.run_max[q] < nx:
                    continue
                need = nx + 1 if fwd else nx - 1
                for g in m.run_unit_members[q]:
                    y = m.unit_index[g]
                    cur = new.get(y, self.slot[y])
                    if (fwd and cur < need) or (not fwd and cur > need):
                        new[y] = need
                        stack.append(y)
                        if len(new) > limit:
                            return None
        return new

    def apply_moves(self, moves):
        """Apply {gate: slot}; returns the inverse mapping and the hard-cost delta."""
        before = self.phi_hard + self.phi_soft * 1e-3
        undo = {}
        for y, s in moves.items():
            undo[y] = int(self.slot[y])
            self._remove(y)
        for y, s in moves.items():
            self._place(y, s)
        return undo, (self.phi_hard + self.phi_soft * 1e-3) - before

    def push_tabu_search(self, max_iter=200000, deadline=None, max_cands=200, top=6,
                         stall_limit=None):
        """Tabu search with hard precedence and chain-push compound moves."""
        rng = self.rng
        tabu = {}
        best_phi = self.phi_hard
        best_slot = self.slot.copy()
        it = 0
        last_improve = 0
        stall_limit = stall_limit or max(3000, 40 * self.nu)
        while self.phi_hard > 1e-12 and it < max_iter:
            if (it & 31) == 0 and deadline is not None and time.time() > deadline:
                break
            if it - last_improve > stall_limit:
                break
            conf = self._conflicting()
            if self.movable is not None:
                conf &= self.movable
            conf = list(conf)
            if len(conf) > max_cands:
                conf = list(rng.choice(conf, size=max_cands, replace=False))
            # 1) cheap screening with single-gate deltas over the static window
            pool = []
            for i in conf:
                lo, hi = int(self.est[i]), int(self.lst[i])
                if hi <= lo:
                    continue
                d = self.costs(i, lo, hi) + rng.random(hi - lo + 1) * 1e-6
                for j in np.argsort(d)[:3]:
                    if np.isfinite(d[j]):
                        pool.append((d[j], i, lo + int(j)))
            if not pool:
                break
            pool.sort(key=lambda x: x[0])
            # 2) exact evaluation of the best few compound moves
            cur = self.phi_hard
            best_val, best_mv = np.inf, None
            evaluated = 0
            for _, i, t in pool:
                if evaluated >= top:
                    break
                mv = self.push_set(i, t)
                if mv is None:
                    continue
                undo, delta = self.apply_moves(mv)
                self.apply_moves(undo)
                evaluated += 1
                is_tabu = tabu.get((i, t), -1) > it
                if is_tabu and cur + delta >= best_phi - 1e-12:
                    continue
                delta += rng.random() * 1e-6
                if delta < best_val:
                    best_val, best_mv = delta, mv
            if best_mv is None:
                _, i, t = pool[int(rng.integers(len(pool)))]
                best_mv = self.push_set(i, t)
                if best_mv is None:
                    it += 1
                    continue
            undo, _ = self.apply_moves(best_mv)
            tenure = int(rng.integers(0, 10)) + int(0.6 * len(conf))
            for y, s in undo.items():
                tabu[(y, s)] = it + tenure + 1
            it += 1
            if self.phi_hard < best_phi - 1e-12:
                best_phi = self.phi_hard
                best_slot = self.slot.copy()
                last_improve = it
        if self.phi_hard > best_phi + 1e-12:
            self.reset_to(best_slot)
        self.iterations = it
        return self.phi_hard <= 1e-12

    def reset_to(self, slots):
        for i in range(self.nu):
            if self.slot[i] >= 0:
                self._remove(i)
        self.load_slots(slots)

    def recompute_precedence(self):
        self.V = 0
        self.vpairs = set()
        if not self.has_prec:
            return
        for i in range(self.nu):
            t = int(self.slot[i])
            for p in self.preds[i]:
                if self.run_max[p] >= t:
                    self.V += sum(c for s, c in self.run_cnt[p].items() if s >= t)
        for r in self.m.unit_runs:
            q = self.m.next_unit_run[r]
            if q >= 0 and self.run_max[r] >= self.run_min[q]:
                self.vpairs.add((r, int(q)))


class CommutingTabu:
    """Vectorised Max-k-Cut tabu search for fully commuting segments.

    With the gate/resource incidence matrix A (n x R) and the marginal-cost
    matrix M[t, r] = w_r * max(0, occ[t, r] - c_r + 1), the cost of moving
    every candidate gate to every layer is one matrix product A_C @ M^T.
    """

    def __init__(self, res_lists, R, k, slots, caps=None, weights=None, seed=0):
        self.nu = len(res_lists)
        self.R = R
        self.k = int(k)
        self.rng = np.random.default_rng(seed)
        self.A = np.zeros((self.nu, R))
        for i, r in enumerate(res_lists):
            self.A[i, r] += 1.0
        self.res = [np.asarray(r, dtype=np.int64) for r in res_lists]
        self.cap = np.ones(R) if caps is None else np.asarray(caps, dtype=float)
        self.wt = np.ones(R) if weights is None else np.asarray(weights, dtype=float)
        self.slot = np.asarray(slots, dtype=np.int64).copy()
        self.occ = np.zeros((self.k, R))
        for i in range(self.nu):
            self.occ[self.slot[i], self.res[i]] += 1
        self.tabu = np.zeros((self.nu, self.k), dtype=np.int64)

    def phi(self):
        e = np.maximum(0.0, self.occ - self.cap)
        return float((self.wt * e * (e + 1) / 2).sum())

    def _set(self, i, t):
        r = self.res[i]
        self.occ[self.slot[i], r] -= 1
        self.occ[t, r] += 1
        self.slot[i] = t

    @staticmethod
    def drop_layer(res_lists, R, slots, caps=None, weights=None, rng=None):
        """k -> k-1 warm start: delete the emptiest layer, re-insert its gates greedily."""
        slots = np.asarray(slots, dtype=np.int64)
        k = int(slots.max()) + 1
        counts = np.bincount(slots, minlength=k)
        cand = np.flatnonzero(counts == counts.min())
        t_del = int(cand[rng.integers(len(cand))]) if rng is not None else int(cand[0])
        moved = np.flatnonzero(slots == t_del)
        new = slots.copy()
        new[new > t_del] -= 1
        cap = np.ones(R) if caps is None else np.asarray(caps, dtype=float)
        wt = np.ones(R) if weights is None else np.asarray(weights, dtype=float)
        occ = np.zeros((k - 1, R))
        keep = np.flatnonzero(slots != t_del)
        for i in keep:
            occ[new[i], res_lists[i]] += 1
        for i in moved:
            r = res_lists[i]
            cost = (wt[r] * np.maximum(0, occ[:, r] - cap[r] + 1)).sum(axis=1)
            cost = cost + (rng.random(k - 1) * 1e-6 if rng is not None else 0)
            t = int(np.argmin(cost))
            new[i] = t
            occ[t, r] += 1
        return new

    def search(self, max_iter=10 ** 7, deadline=None, stall_limit=None):
        rng = self.rng
        cur = self.phi()
        best_phi, best_slot = cur, self.slot.copy()
        it = 0
        last = 0
        stall_limit = stall_limit or 10 ** 9
        ar = np.arange(self.nu)
        while cur > 1e-9 and it < max_iter:
            if (it & 127) == 0 and deadline is not None and time.time() > deadline:
                break
            if it - last > stall_limit:
                break
            over = self.occ > self.cap
            conf = np.flatnonzero((self.A * over[self.slot]).sum(axis=1) > 0)
            Ac = self.A[conf]
            M = self.wt * np.maximum(0.0, self.occ - self.cap + 1)
            gam = Ac @ M.T
            stay = (Ac * (self.wt * np.maximum(0.0, self.occ[self.slot[conf]] - self.cap))).sum(axis=1)
            delta = gam - stay[:, None]
            delta[np.arange(len(conf)), self.slot[conf]] = np.inf
            tab = self.tabu[conf] > it
            delta = np.where(tab & (cur + delta >= best_phi - 1e-9), np.inf, delta)
            noisy = delta + rng.random(delta.shape) * 1e-6
            flat = int(np.argmin(noisy))
            ci, t = divmod(flat, self.k)
            if not np.isfinite(delta[ci, t]):
                ci = int(rng.integers(len(conf)))
                t = int(rng.integers(self.k))
                if t == self.slot[conf[ci]]:
                    it += 1
                    continue
                i = conf[ci]
                old = self.slot[i]
                self._set(i, t)
                cur = self.phi()
            else:
                i = conf[ci]
                old = self.slot[i]
                cur += float(delta[ci, t])
                self._set(i, t)
            self.tabu[i, old] = it + int(rng.integers(0, 10)) + int(0.6 * len(conf)) + 1
            it += 1
            if cur < best_phi - 1e-9:
                best_phi, best_slot, last = cur, self.slot.copy(), it
        del ar
        self.iterations = it
        if cur > best_phi + 1e-9:
            self.slot = best_slot
        return best_phi <= 1e-9


def used_layers(slots):
    return int(slots.max()) + 1 if len(slots) else 0


def compact(slots):
    """Remove empty layers (keeps relative order, so precedence stays valid)."""
    if len(slots) == 0:
        return slots
    uniq = np.unique(slots)
    remap = {int(t): j for j, t in enumerate(uniq)}
    return np.array([remap[int(t)] for t in slots], dtype=np.int64)


def kdescent(model, init_slots, lb, time_limit=10.0, caps=None, soft=None, seed=0,
             max_iter_per_k=200000, restarts=2, log=None):
    """Max-k-Cut k-descent: repeatedly ask for a conflict-free (k-1)-layering.

    Starts from a feasible `init_slots`; returns (best_slots, stats).
    """
    t0 = time.time()
    deadline = t0 + time_limit
    best = compact(np.asarray(init_slots, dtype=np.int64))
    best_k = used_layers(best)
    stats = {"start_k": best_k, "attempts": [], "lb": int(lb)}
    k = best_k - 1
    rng = np.random.default_rng(seed)
    commuting = not any(len(p) for p in model.preds) and soft is None
    if commuting:
        res_lists = model.unit_resources()
        R = model.num_wires
        while k >= max(lb, 1) and time.time() < deadline:
            init = CommutingTabu.drop_layer(res_lists, R, best, caps, rng=rng)
            tb = CommutingTabu(res_lists, R, k, init, caps=caps, seed=int(rng.integers(1 << 30)))
            init_phi = tb.phi()
            ok = tb.search(max_iter=10 ** 9, deadline=deadline)
            stats["attempts"].append({"k": k, "init_phi": init_phi, "final_phi": tb.phi(),
                                      "iters": tb.iterations, "ok": ok})
            if log:
                log(f"  k={k} init_phi={init_phi:.0f} -> {tb.phi():.0f} in {tb.iterations} it")
            if not ok:
                break
            best = compact(tb.slot.copy())
            best_k = used_layers(best)
            k = best_k - 1
        stats["final_k"] = best_k
        stats["time"] = time.time() - t0
        return best, stats
    while k >= max(lb, 1) and time.time() < deadline:
        success = False
        for attempt in range(restarts):
            if time.time() >= deadline:
                break
            st = MaxKCutState(model, k, caps=caps, soft=soft, seed=int(rng.integers(1 << 30)))
            order = np.lexsort((np.arange(len(best)), best))
            target = best * (k / max(best_k, 1)) if attempt == 0 else (
                best * (k / max(best_k, 1)) + rng.normal(0, 1.0, len(best)))
            st.greedy_init(order, target)
            init_phi = st.phi_hard
            if st.has_prec:
                ok = st.push_tabu_search(max_iter=max_iter_per_k, deadline=deadline)
            else:
                ok = st.tabu_search(max_iter=max_iter_per_k, deadline=deadline)
            stats["attempts"].append({"k": k, "init_phi": float(init_phi),
                                      "final_phi": float(st.phi_hard), "iters": st.iterations,
                                      "ok": ok})
            if log:
                log(f"  k={k} attempt={attempt} init_phi={init_phi:.0f} -> {st.phi_hard:.0f} "
                    f"in {st.iterations} it")
            if ok:
                best = compact(st.slot.copy())
                best_k = used_layers(best)
                success = True
                break
        if not success:
            break
        k = best_k - 1
    stats["final_k"] = best_k
    stats["time"] = time.time() - t0
    return best, stats
