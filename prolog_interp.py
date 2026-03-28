#!/usr/bin/env python3
"""prolog_interp - Minimal Prolog interpreter with unification."""
import argparse, re, copy

def tokenize(s):
    return re.findall(r'[A-Za-z_]\w*|[().,:\-]|:-', s)

class Var:
    def __init__(self, name): self.name = name
    def __repr__(self): return self.name
    def __eq__(self, o): return isinstance(o, Var) and self.name == o.name
    def __hash__(self): return hash(self.name)

class Term:
    def __init__(self, functor, args=None):
        self.functor = functor; self.args = args or []
    def __repr__(self):
        if not self.args: return self.functor
        return f"{self.functor}({', '.join(map(str, self.args))})"

def parse_term(tokens, pos):
    name = tokens[pos]; pos += 1
    if name[0].isupper() or name[0] == '_': return Var(name), pos
    if pos < len(tokens) and tokens[pos] == '(':
        pos += 1; args = []
        while tokens[pos] != ')':
            arg, pos = parse_term(tokens, pos)
            args.append(arg)
            if tokens[pos] == ',': pos += 1
        return Term(name, args), pos + 1
    return Term(name), pos

def unify(x, y, subst):
    if subst is None: return None
    if x == y: return subst
    if isinstance(x, Var):
        if x in subst: return unify(subst[x], y, subst)
        return {**subst, x: y}
    if isinstance(y, Var): return unify(y, x, subst)
    if isinstance(x, Term) and isinstance(y, Term):
        if x.functor != y.functor or len(x.args) != len(y.args): return None
        for a, b in zip(x.args, y.args):
            subst = unify(a, b, subst)
            if subst is None: return None
        return subst
    return None

def substitute(term, subst):
    if isinstance(term, Var):
        if term in subst: return substitute(subst[term], subst)
        return term
    if isinstance(term, Term):
        return Term(term.functor, [substitute(a, subst) for a in term.args])
    return term

counter = [0]
def rename_vars(clause):
    counter[0] += 1
    mapping = {}
    def rename(t):
        if isinstance(t, Var):
            if t.name not in mapping: mapping[t.name] = Var(f"{t.name}_{counter[0]}")
            return mapping[t.name]
        if isinstance(t, Term): return Term(t.functor, [rename(a) for a in t.args])
        return t
    return [rename(t) for t in clause]

def solve(goals, clauses, subst, depth=0):
    if depth > 100: return
    if not goals: yield subst; return
    goal = substitute(goals[0], subst)
    for clause in clauses:
        renamed = rename_vars(clause)
        head, body = renamed[0], renamed[1:]
        new_subst = unify(goal, head, dict(subst))
        if new_subst is not None:
            yield from solve(body + goals[1:], clauses, new_subst, depth + 1)

def main():
    p = argparse.ArgumentParser(description="Minimal Prolog")
    p.add_argument("file", nargs="?")
    args = p.parse_args()
    clauses = []
    if args.file:
        text = open(args.file).read()
        for line in text.split('.'):
            line = line.strip()
            if not line: continue
            if ':-' in line:
                head_s, body_s = line.split(':-', 1)
                tokens = tokenize(head_s)
                head, _ = parse_term(tokens, 0)
                body = []
                for part in body_s.split(','):
                    t, _ = parse_term(tokenize(part.strip()), 0)
                    body.append(t)
                clauses.append([head] + body)
            else:
                head, _ = parse_term(tokenize(line), 0)
                clauses.append([head])
    print("Prolog - Ctrl+D to exit")
    while True:
        try:
            q = input("?- ").strip().rstrip('.')
            if not q: continue
            goals = []
            for part in q.split(','):
                t, _ = parse_term(tokenize(part.strip()), 0)
                goals.append(t)
            found = False
            for subst in solve(goals, clauses, {}):
                found = True
                vars_in_query = set()
                for g in goals:
                    def collect(t):
                        if isinstance(t, Var): vars_in_query.add(t)
                        elif isinstance(t, Term):
                            for a in t.args: collect(a)
                    collect(g)
                bindings = {v.name: substitute(v, subst) for v in vars_in_query}
                if bindings:
                    print(", ".join(f"{k} = {v}" for k, v in bindings.items()))
                else:
                    print("true")
                break
            if not found: print("false")
        except (EOFError, KeyboardInterrupt): break
        except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    main()
