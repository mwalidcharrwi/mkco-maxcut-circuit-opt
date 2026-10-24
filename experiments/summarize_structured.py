"""Markdown tables for the commuting-circuit experiments (results/structured/*.json)."""
import json
import os
from collections import defaultdict

D = "results/structured"


def load(name):
    p = os.path.join(D, f"{name}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def main():
    out = []
    A = out.append
    e1 = load("e1")
    if e1:
        A("### E1 - Random commuting multi-controlled-Z circuits (Lee et al. Sec. 4.3)\n")
        A("Mean depth over seeds; 'opt' = instances where the method meets the certified lower bound.\n")
        A("| qubits m | gates n | LB | DSatur (Lee) | Backtracking (Lee, n<=50) | JK'26 | **MKCO** | DSatur opt | JK opt | MKCO opt |")
        A("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        g = defaultdict(list)
        for r in e1:
            g[(r["m"], r["n"])].append(r)
        for (m, n), rs in sorted(g.items()):
            bt = [r["backtracking"] for r in rs if "backtracking" in r]
            A(f"| {m} | {n} | {mean([r['lb'] for r in rs]):.1f} | {mean([r['dsatur'] for r in rs]):.1f} | "
              f"{mean(bt):.1f} | {mean([r['jk'] for r in rs]):.1f} | **{mean([r['mkco'] for r in rs]):.1f}** | "
              f"{sum(r['dsatur'] == r['lb'] for r in rs)}/{len(rs)} | {sum(r['jk'] == r['lb'] for r in rs)}/{len(rs)} | "
              f"{sum(r['mkco'] == r['lb'] for r in rs)}/{len(rs)} |" if bt else
              f"| {m} | {n} | {mean([r['lb'] for r in rs]):.1f} | {mean([r['dsatur'] for r in rs]):.1f} | - | "
              f"{mean([r['jk'] for r in rs]):.1f} | **{mean([r['mkco'] for r in rs]):.1f}** | "
              f"{sum(r['dsatur'] == r['lb'] for r in rs)}/{len(rs)} | {sum(r['jk'] == r['lb'] for r in rs)}/{len(rs)} | "
              f"{sum(r['mkco'] == r['lb'] for r in rs)}/{len(rs)} |")
    e2 = load("e2")
    if e2:
        A("\n### E2 - F(2^n) multiplication, Toffoli-depth of phases 1+3 (Lee et al. Sec. 5.1, Fig. 2)\n")
        A("| n | certified LB (proven optimum for n<=7) | 2n-1 | DSatur (Lee) | JK'26 | **MKCO** |")
        A("|---:|---:|---:|---:|---:|---:|")
        for r in e2:
            A(f"| {r['n']} | {r['lb']} | {r['bound_2n_minus_1']} | {r['dsatur']} | {r['jk']} | **{r['mkco']}** |")
        A(f"\nMeets the certified bound: DSatur {sum(r['dsatur'] == r['lb'] for r in e2)}/{len(e2)}, "
          f"JK {sum(r['jk'] == r['lb'] for r in e2)}/{len(e2)}, MKCO {sum(r['mkco'] == r['lb'] for r in e2)}/{len(e2)}.")
    e3 = load("e3")
    if e3:
        A("\n### E3 - Random CCZ circuits on 10 qubits (Lee et al. Appendix C)\n")
        A("| CCZ gates | LB | DSatur (Lee) | Backtracking (Lee) | JK'26 | **MKCO** | MKCO opt |")
        A("|---:|---:|---:|---:|---:|---:|---:|")
        g = defaultdict(list)
        for r in e3:
            g[r["gates"]].append(r)
        for n, rs in sorted(g.items()):
            bt = [r["backtracking"] for r in rs if "backtracking" in r]
            A(f"| {n} | {mean([r['lb'] for r in rs]):.1f} | {mean([r['dsatur'] for r in rs]):.1f} | "
              f"{mean(bt):.1f} | {mean([r['jk'] for r in rs]):.1f} | **{mean([r['mkco'] for r in rs]):.1f}** | "
              f"{sum(r['mkco'] == r['lb'] for r in rs)}/{len(rs)} |" if bt else
              f"| {n} | {mean([r['lb'] for r in rs]):.1f} | {mean([r['dsatur'] for r in rs]):.1f} | - | "
              f"{mean([r['jk'] for r in rs]):.1f} | **{mean([r['mkco'] for r in rs]):.1f}** | "
              f"{sum(r['mkco'] == r['lb'] for r in rs)}/{len(rs)} |")
    e4 = load("e4")
    if e4:
        A("\n### E4 - Commuting RZZ layers on random d-regular graphs (QAOA cost layer; LB = degree)\n")
        A("| qubits | degree d | DSatur (Lee) | JK'26 | **MKCO** | MKCO = d (optimal) |")
        A("|---:|---:|---:|---:|---:|---:|")
        g = defaultdict(list)
        for r in e4:
            g[(r["qubits"], r["degree"])].append(r)
        for (q, d), rs in sorted(g.items()):
            A(f"| {q} | {d} | {mean([r['dsatur'] for r in rs]):.2f} | {mean([r['jk'] for r in rs]):.2f} | "
              f"**{mean([r['mkco'] for r in rs]):.2f}** | {sum(r['mkco'] == r['lb'] for r in rs)}/{len(rs)} |")
    e5 = load("e5")
    if e5:
        A("\n### E5 - Hierarchical Max-Cut with exact and QAOA sub-solvers\n")
        A("| case | gates | LB | backend | layers | spins (log encoding) | spins (one-hot) | QAOA nodes solved optimally |")
        A("|---|---:|---:|---|---:|---:|---:|---:|")
        for r in e5:
            q = r.get("qaoa") or []
            qs = f"{sum(x['best_sampled_is_optimal'] for x in q)}/{len(q)}" if q else "-"
            A(f"| {r['case']} | {r['n_gates']} | {r['lb']} | {r['backend']} | {r['layers']} | "
              f"{r['spins_log_encoding']} | {r['spins_one_hot']} | {qs} |")
    e6 = load("e6")
    if e6:
        A("\n### E6 - Depth/qubit trade-off by ancilla fan-out (capacitated Max-k-Cut)\n")
        A("| circuit | copies per qubit | qubits | round-robin + DSatur depth | **MKCO depth** |")
        A("|---|---:|---:|---:|---:|")
        for r in e6:
            A(f"| {r['case']} | {r['copies']} | {r['qubits']} | {r['baseline_total']} | **{r['mkco_total']}** |")
    md = "\n".join(out) + "\n"
    open(os.path.join(D, "tables.md"), "w").write(md)
    print(md)


if __name__ == "__main__":
    main()
