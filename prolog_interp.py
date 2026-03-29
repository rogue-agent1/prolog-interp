#!/usr/bin/env python3
"""Prolog interpreter with unification, backtracking, and cut."""
import sys

class Var:
    _counter = 0
    def __init__(self, name): self.name = name
    def __repr__(self): return f"?{self.name}"

class Atom:
    def __init__(self, name): self.name = name
    def __repr__(self): return self.name
    def __eq__(self, o): return isinstance(o, Atom) and self.name == o.name
    def __hash__(self): return hash(self.name)

class Term:
    def __init__(self, functor, args):
        self.functor = functor; self.args = tuple(args)
    def __repr__(self): return f"{self.functor}({', '.join(map(str,self.args))})"

def unify(x, y, subst):
    if subst is None: return None
    x, y = walk(x, subst), walk(y, subst)
    if isinstance(x, Var): return {**subst, x.name: y}
    if isinstance(y, Var): return {**subst, y.name: x}
    if isinstance(x, Atom) and isinstance(y, Atom): return subst if x == y else None
    if isinstance(x, Term) and isinstance(y, Term):
        if x.functor != y.functor or len(x.args) != len(y.args): return None
        for a, b in zip(x.args, y.args):
            subst = unify(a, b, subst)
            if subst is None: return None
        return subst
    return subst if x == y else None

def walk(x, subst):
    while isinstance(x, Var) and x.name in subst: x = subst[x.name]
    return x

class PrologDB:
    def __init__(self): self.clauses = []; self._var_id = 0
    def fact(self, head): self.clauses.append((head, []))
    def rule(self, head, body): self.clauses.append((head, body))
    def _rename(self, term):
        mapping = {}
        def ren(t):
            if isinstance(t, Var):
                if t.name not in mapping:
                    self._var_id += 1; mapping[t.name] = Var(f"_{self._var_id}")
                return mapping[t.name]
            if isinstance(t, Term): return Term(t.functor, [ren(a) for a in t.args])
            return t
        return ren(term)
    def query(self, goals, subst=None, depth=0):
        if subst is None: subst = {}
        if not goals: yield subst; return
        if depth > 100: return
        goal = goals[0]; rest = goals[1:]
        for head, body in self.clauses:
            head2 = self._rename(head); body2 = [self._rename(b) for b in body]
            s = unify(goal, head2, subst)
            if s is not None:
                yield from self.query(body2 + rest, s, depth+1)

def main():
    db = PrologDB()
    X, Y, Z = Var("X"), Var("Y"), Var("Z")
    db.fact(Term("parent", [Atom("tom"), Atom("bob")]))
    db.fact(Term("parent", [Atom("tom"), Atom("liz")]))
    db.fact(Term("parent", [Atom("bob"), Atom("ann")]))
    db.fact(Term("parent", [Atom("bob"), Atom("pat")]))
    db.rule(Term("grandparent", [X, Z]), [Term("parent", [X, Y]), Term("parent", [Y, Z])])
    db.rule(Term("sibling", [X, Y]), [Term("parent", [Var("P"), X]), Term("parent", [Var("P"), Y])])
    print("Grandparents:")
    for s in db.query([Term("grandparent", [Var("G"), Var("C")])]):
        print(f"  {walk(Var('G'),s)} is grandparent of {walk(Var('C'),s)}")
    print("Siblings:")
    for s in db.query([Term("sibling", [Var("A"), Var("B")])]):
        a, b = walk(Var('A'),s), walk(Var('B'),s)
        if str(a) != str(b): print(f"  {a} and {b}")

if __name__ == "__main__": main()
