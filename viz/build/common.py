"""Shared paths and baptism details for the visualisation builders.

Run the builders from the repository root. Intermediate files go to
viz/build/work/ (not in git)."""

import os
import pickle
import re
from collections import defaultdict

WORK = "viz/build/work"
THREADS = "viz/threads-of-leiden"
BROWSER = "viz/family-browser"
BAPTISMS = "data/elo-baptisms-before-1811.nt"


def baptism_info():
    """date_of, parents, child_name per baptism record IRI (without <>), cached in WORK.

    parents is "father given + family name & mother given + family name"."""
    os.makedirs(WORK, exist_ok=True)
    cache = f"{WORK}/bapt_info.pkl"
    if os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    date_of, fam, given, par, gender = {}, {}, {}, defaultdict(list), {}
    lit = re.compile(r'^"(.*?)"')
    for line in open(BAPTISMS, encoding="utf-8"):
        s, p, o = line.rstrip(" .\n").split(" ", 2)
        if p == "<https://schema.org/dateCreated>": date_of[s[1:-1]] = o[1:11]
        elif p == "<https://schema.org/familyName>": fam[s] = lit.match(o).group(1)
        elif p == "<https://schema.org/givenName>": given[s] = lit.match(o).group(1)
        elif p == "<https://schema.org/parent>": par[s].append(o)
        elif p == "<https://schema.org/gender>": gender[s] = o
    name = lambda q: (given.get(q, "") + " " + fam.get(q, "")).strip()
    parents, child = {}, {}
    for c, ps in par.items():
        rec = re.sub(r"_Person_.*", ">", c)[1:-1]
        child[rec] = given.get(c, "?")
        f = [q for q in ps if gender.get(q) == "<https://schema.org/Male>"]
        m = [q for q in ps if gender.get(q) == "<https://schema.org/Female>"]
        parents[rec] = (name(f[0]) if f else "?") + " & " + (name(m[0]) if m else "?")
    info = (date_of, parents, child)
    pickle.dump(info, open(cache, "wb"))
    return info
