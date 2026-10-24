"""OpenQASM 2.0 parser (self-contained; no Qiskit dependency)."""
from __future__ import annotations

import math
import os
import re

from . import gates as G
from .circuit import Circuit, CustomGateDef, Gate

_TOKEN = re.compile(r"""
    (?P<ws>\s+|//[^\n]*|/\*.*?\*/)
  | (?P<num>(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?)
  | (?P<id>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<str>"[^"]*")
  | (?P<sym>->|==|[;,()\[\]{}+\-*/^])
""", re.VERBOSE | re.DOTALL)

_FUNCS = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "exp": math.exp,
          "ln": math.log, "sqrt": math.sqrt, "asin": math.asin, "acos": math.acos,
          "atan": math.atan}


class QasmError(Exception):
    pass


def tokenize(text):
    pos, out = 0, []
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            line = text.count("\n", 0, pos) + 1
            raise QasmError(f"unexpected character {text[pos]!r} on line {line}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        out.append((kind, m.group(kind), m.start()))
    return out


def eval_expr(e, env):
    t = e[0]
    if t == "num":
        return e[1]
    if t == "var":
        if e[1] == "pi":
            return math.pi
        if e[1] not in env:
            raise QasmError(f"unknown parameter {e[1]!r}")
        return env[e[1]]
    if t == "neg":
        return -eval_expr(e[1], env)
    if t == "call":
        return _FUNCS[e[1]](eval_expr(e[2], env))
    a, b = eval_expr(e[2], env), eval_expr(e[3], env)
    return {"+": a + b, "-": a - b, "*": a * b, "/": a / b if b else math.inf, "^": a ** b}[e[1]]


class _Parser:
    def __init__(self, text, base_dir, expand_custom, max_composite_qubits):
        self.toks = tokenize(text)
        self.i = 0
        self.text = text
        self.base_dir = base_dir
        self.expand_custom = expand_custom
        self.max_composite = max_composite_qubits
        self.qregs, self.cregs = [], []
        self.qoff, self.coff = {}, {}
        self.nq = self.nc = 0
        self.circ = Circuit(0)
        self.opaque = set()
        self.ops = []

    # -- token helpers ----------------------------------------------------
    def peek(self, k=0):
        j = self.i + k
        return self.toks[j] if j < len(self.toks) else (None, None, len(self.text))

    def next(self):
        t = self.peek()
        self.i += 1
        return t

    def expect(self, val):
        t = self.next()
        if t[1] != val:
            line = self.text.count("\n", 0, t[2]) + 1
            raise QasmError(f"expected {val!r} but found {t[1]!r} on line {line}")
        return t

    def accept(self, val):
        if self.peek()[1] == val:
            self.i += 1
            return True
        return False

    def ident(self):
        t = self.next()
        if t[0] != "id":
            raise QasmError(f"expected identifier, found {t[1]!r}")
        return t[1]

    # -- expressions --------------------------------------------------------
    def expr(self):
        e = self.term()
        while self.peek()[1] in ("+", "-"):
            op = self.next()[1]
            e = ("bin", op, e, self.term())
        return e

    def term(self):
        e = self.factor()
        while self.peek()[1] in ("*", "/"):
            op = self.next()[1]
            e = ("bin", op, e, self.factor())
        return e

    def factor(self):
        if self.accept("-"):
            return ("neg", self.factor())
        if self.accept("+"):
            return self.factor()
        base = self.atom()
        if self.accept("^"):
            return ("bin", "^", base, self.factor())
        return base

    def atom(self):
        t = self.next()
        if t[0] == "num":
            return ("num", float(t[1]))
        if t[0] == "id":
            if t[1] in _FUNCS and self.peek()[1] == "(":
                self.expect("(")
                e = self.expr()
                self.expect(")")
                return ("call", t[1], e)
            return ("var", t[1])
        if t[1] == "(":
            e = self.expr()
            self.expect(")")
            return e
        raise QasmError(f"bad expression token {t[1]!r}")

    def exprlist(self):
        out = []
        if self.peek()[1] == ")":
            return out
        out.append(self.expr())
        while self.accept(","):
            out.append(self.expr())
        return out

    # -- statements ----------------------------------------------------------
    def parse(self):
        if self.peek()[1] == "OPENQASM":
            self.next()
            self.next()
            self.expect(";")
        while self.peek()[0] is not None:
            self.statement()
        c = self.circ
        c.num_qubits, c.num_clbits = self.nq, self.nc
        c.qregs, c.cregs = list(self.qregs), list(self.cregs)
        c.gates = self.ops
        return c

    def statement(self):
        kw = self.peek()[1]
        if kw == "include":
            self.next()
            fname = self.next()[1].strip('"')
            self.expect(";")
            if fname != "qelib1.inc":
                self.include(fname)
        elif kw in ("qreg", "creg"):
            self.next()
            name = self.ident()
            self.expect("[")
            size = int(self.next()[1])
            self.expect("]")
            self.expect(";")
            if kw == "qreg":
                self.qregs.append((name, size))
                self.qoff[name] = (self.nq, size)
                self.nq += size
            else:
                self.cregs.append((name, size))
                self.coff[name] = (self.nc, size)
                self.nc += size
        elif kw == "gate":
            self.gate_def()
        elif kw == "opaque":
            self.next()
            name = self.ident()
            if self.accept("("):
                while not self.accept(")"):
                    self.next()
            while not self.accept(";"):
                self.next()
            self.opaque.add(name)
        elif kw == "if":
            self.next()
            self.expect("(")
            creg = self.ident()
            self.expect("==")
            val = int(self.next()[1])
            self.expect(")")
            off, size = self.coff[creg]
            self.qop(cond=(creg, val, tuple(range(off, off + size))))
        else:
            self.qop()

    def include(self, fname):
        path = os.path.join(self.base_dir or ".", fname)
        if not os.path.exists(path):
            raise QasmError(f"include file not found: {fname}")
        with open(path) as fh:
            sub = _Parser(fh.read(), self.base_dir, self.expand_custom, self.max_composite)
        sub.circ = self.circ
        while sub.peek()[0] is not None:
            if sub.peek()[1] == "gate":
                sub.gate_def()
            else:
                sub.statement()

    def gate_def(self):
        start = self.peek()[2]
        self.expect("gate")
        name = self.ident()
        pnames = []
        if self.accept("("):
            if self.peek()[1] != ")":
                pnames.append(self.ident())
                while self.accept(","):
                    pnames.append(self.ident())
            self.expect(")")
        qnames = [self.ident()]
        while self.accept(","):
            qnames.append(self.ident())
        self.expect("{")
        body = []
        while not self.accept("}"):
            gname = self.ident()
            pe = []
            if self.accept("("):
                pe = self.exprlist()
                self.expect(")")
            args = [self.ident()]
            while self.accept(","):
                args.append(self.ident())
            self.expect(";")
            if gname == "barrier":
                continue
            body.append((gname, pe, args))
        end = self.toks[self.i - 1][2] + 1
        defn = CustomGateDef(name, pnames, qnames, body, self.text[start:end], self.circ)
        if name not in self.circ.custom:
            self.circ.custom_order.append(name)
        self.circ.custom[name] = defn

    def arg(self, kind):
        name = self.ident()
        table = self.qoff if kind == "q" else self.coff
        if name not in table:
            raise QasmError(f"unknown register {name!r}")
        off, size = table[name]
        if self.accept("["):
            idx = int(self.next()[1])
            self.expect("]")
            if idx >= size:
                raise QasmError(f"index {idx} out of range for {name}")
            return [off + idx], False
        return list(range(off, off + size)), True

    def arglist(self, kind="q"):
        out = [self.arg(kind)]
        while self.accept(","):
            out.append(self.arg(kind))
        return out

    def qop(self, cond=None):
        kw = self.peek()[1]
        if kw == "measure":
            self.next()
            qs, qreg = self.arg("q")
            self.expect("->")
            cs, _ = self.arg("c")
            self.expect(";")
            for q, c in zip(qs, cs):
                self.ops.append(Gate("measure", [q], (), clbits=[c], cond=cond, kind="measure"))
            return
        if kw == "reset":
            self.next()
            qs, _ = self.arg("q")
            self.expect(";")
            for q in qs:
                self.ops.append(Gate("reset", [q], (), cond=cond, kind="reset"))
            return
        if kw == "barrier":
            self.next()
            args = self.arglist("q")
            self.expect(";")
            qs = sorted({q for a, _ in args for q in a})
            self.ops.append(Gate("barrier", qs, (), kind="barrier"))
            return
        name = self.ident()
        params = []
        if self.accept("("):
            params = [eval_expr(e, {}) for e in self.exprlist()]
            self.expect(")")
        args = self.arglist("q")
        self.expect(";")
        sizes = {len(a) for a, isreg in args if isreg}
        if len(sizes) > 1:
            raise QasmError(f"register size mismatch in {name}")
        reps = sizes.pop() if sizes else 1
        for r in range(reps):
            qs = [a[r] if isreg else a[0] for a, isreg in args]
            self.emit(name, params, qs, cond)

    def emit(self, name, params, qs, cond):
        circ = self.circ
        if name in circ.custom:
            d = circ.custom[name]
            if len(qs) != d.num_qubits:
                raise QasmError(f"{name} expects {d.num_qubits} qubits")
            if self.expand_custom or d.num_qubits > self.max_composite:
                for g in d.expand(params, qs):
                    g.cond = cond
                    self.ops.append(g)
                return
            self.ops.append(Gate(name, qs, params, cond=cond))
            return
        if G.is_library_gate(name):
            nq, npar = G.library_arity(name)
            if nq is not None and nq != len(qs):
                raise QasmError(f"{name} expects {nq} qubits, got {len(qs)}")
            if len(params) != npar:
                raise QasmError(f"{name} expects {npar} parameters, got {len(params)}")
            self.ops.append(Gate(name, qs, params, cond=cond))
            return
        if name in self.opaque:
            self.ops.append(Gate(name, qs, params, cond=cond))
            return
        raise QasmError(f"unknown gate {name!r}")


def parse_qasm(text, base_dir=None, expand_custom=False, max_composite_qubits=8):
    """Parse OpenQASM 2.0 source into a Circuit.

    User-defined gates are kept as single composite instructions (so their
    commutation structure is analysed exactly from their unitary) unless
    `expand_custom` is set or they act on more than `max_composite_qubits`.
    """
    return _Parser(text, base_dir, expand_custom, max_composite_qubits).parse()


def load_qasm(path, **kw):
    with open(path) as fh:
        text = fh.read()
    c = parse_qasm(text, base_dir=os.path.dirname(os.path.abspath(path)), **kw)
    c.name = os.path.splitext(os.path.basename(path))[0]
    return c
