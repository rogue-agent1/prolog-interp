#!/usr/bin/env python3
"""Minimal Prolog interpreter with unification and backtracking."""
import sys, re

class Var:
    def __init__(self, name): self.name = name
    def __repr__(self): return self.name
    def __eq__(self, o): return isinstance(o, Var) and self.name == o.name
    def __hash__(self): return hash(self.name)

class Term:
    def __init__(self, functor, args=None):
        self.functor, self.args = functor, args or []
    def __repr__(self):
        if not self.args: return self.functor
        return f"{self.functor}({', '.join(map(str, self.args))})"

def walk(x, subst):
    while isinstance(x, Var) and x in subst: x = subst[x]
    return x

def unify(x, y, subst):
    if subst is None: return None
    x, y = walk(x, subst), walk(y, subst)
    if isinstance(x, Var): return {**subst, x: y}
    if isinstance(y, Var): return {**subst, y: x}
    if isinstance(x, Term) and isinstance(y, Term):
        if x.functor != y.functor or len(x.args) != len(y.args): return None
        for a, b in zip(x.args, y.args):
            subst = unify(a, b, subst)
            if subst is None: return None
        return subst
    if x == y: return subst
    return None

def rename(term, suffix):
    if isinstance(term, Var): return Var(term.name + suffix)
    if isinstance(term, Term): return Term(term.functor, [rename(a, suffix) for a in term.args])
    return term

def solve(goals, rules, subst, depth=0):
    if not goals: yield subst; return
    if depth > 200: return
    goal = goals[0]; rest = goals[1:]
    sfx = f"_{depth}"
    for head, body in rules:
        h = rename(head, sfx)
        b = [rename(g, sfx) for g in body]
        s = unify(goal, h, subst)
        if s is not None:
            yield from solve(b + rest, rules, s, depth + 1)

def tokenize(s):
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[().,:\-]|:-", s)

def parse_term(tokens, pos):
    t = tokens[pos]; pos += 1
    if t[0].isupper() or t == "_": return Var(t), pos
    if pos < len(tokens) and tokens[pos] == "(":
        pos += 1; args = []
        while tokens[pos] != ")":
            arg, pos = parse_term(tokens, pos)
            args.append(arg)
            if pos < len(tokens) and tokens[pos] == ",": pos += 1
        return Term(t, args), pos + 1
    return Term(t), pos

def parse_clause(s):
    tokens = tokenize(s.strip().rstrip("."))
    head, pos = parse_term(tokens, 0)
    body = []
    if pos < len(tokens) and tokens[pos] == ":-":
        pos += 1
        while pos < len(tokens):
            t, pos = parse_term(tokens, pos)
            body.append(t)
            if pos < len(tokens) and tokens[pos] == ",": pos += 1
    return head, body

def deep_walk(x, subst):
    x = walk(x, subst)
    if isinstance(x, Term): return Term(x.functor, [deep_walk(a, subst) for a in x.args])
    return x

def main():
    rules = []
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("%"):
                    rules.append(parse_clause(line))
    print("?- ", end="", flush=True)
    for line in sys.stdin:
        line = line.strip().rstrip(".")
        if not line: print("?- ", end="", flush=True); continue
        tokens = tokenize(line)
        goals = []
        pos = 0
        while pos < len(tokens):
            g, pos = parse_term(tokens, pos)
            goals.append(g)
            if pos < len(tokens) and tokens[pos] == ",": pos += 1
        qvars = set()
        def collect(t):
            if isinstance(t, Var) and t.name != "_": qvars.add(t)
            elif isinstance(t, Term):
                for a in t.args: collect(a)
        for g in goals: collect(g)
        found = False
        for subst in solve(goals, rules, {}):
            found = True
            if qvars:
                bindings = [f"{v.name} = {deep_walk(v, subst)}" for v in sorted(qvars, key=lambda v: v.name)]
                print(", ".join(bindings))
            else: print("true")
            break
        if not found: print("false")
        print("?- ", end="", flush=True)

if __name__ == "__main__": main()
