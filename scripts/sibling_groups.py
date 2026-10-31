#!/usr/bin/env python3
"""Combine the sibling links of several burgerLinker runs into one set of
sibling pairs and sibling groups.

Each run is given as <label>=<BETWEEN_B-M csv>, for example

    familyname=work/familyname/between_b-m-maxLev-4/results/BETWEEN_B-M-maxLev-4.csv

A pair of baptisms is a sibling pair when at least one run links them (the
union of the runs). Self-links (certificate_A = certificate_B) are dropped,
and A-B and B-A count as one pair. Sibling groups are the connected groups
of baptisms: if A-B and B-C are pairs, A, B and C form one group.

Family-name check (--family-name-check <baptisms.nt>): a pair found only by
runs whose label contains "patronym" is dropped when the fathers, or the
mothers, of the two baptisms both have a family name and those names differ.
Common patronyms ("Pieter Jansz & Marij Jans") otherwise join different
couples into one group. The surname without prefix (pnv:baseSurname) is
compared, ignoring case, with burgerLinker's tolerance for the length of the
shorter name: 1 letter 0, 2-5 letters 1, 6-8 letters 2, 9-11 letters 3,
12+ letters 4; the first letter must be the same.

Writes
    <out>-pairs.csv   baptism_A, baptism_B, year_diff, found_by (labels, ";")
    <out>-groups.csv  group, size, baptism

usage: sibling_groups.py [--family-name-check <baptisms.nt>] <out> <label>=<csv> [<label>=<csv> ...]"""

import csv
import re
import sys
from collections import Counter, defaultdict

SDO = "<https://schema.org/"
PNV_BASE = "<https://w3id.org/pnv#baseSurname>"
LITERAL = re.compile(r'^"(.*)"')


def read_parent_surnames(path):
    """record IRI -> (father's surname, mother's surname), None when unknown."""
    family, base, name_node, parents, gender, children = {}, {}, {}, defaultdict(list), {}, []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s, p, o = line.rstrip(" .\n").split(" ", 2)
            if p == SDO + "familyName>":
                family[s] = LITERAL.match(o).group(1)
            elif p == PNV_BASE:
                base[s] = LITERAL.match(o).group(1)
            elif p == SDO + "additionalName>":
                name_node[s] = o
            elif p == SDO + "parent>":
                parents[s].append(o)
            elif p == SDO + "gender>":
                gender[s] = o
    surname = lambda person: base.get(name_node.get(person)) or family.get(person)
    result = {}
    for child, ps in parents.items():
        father = next((q for q in ps if gender.get(q) == SDO + "Male>"), None)
        mother = next((q for q in ps if gender.get(q) == SDO + "Female>"), None)
        result[child[1:child.index("_Person_")]] = (surname(father), surname(mother))
    return result


def levenshtein(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def names_differ(a, b):
    if not a or not b:
        return False
    a, b = a.lower(), b.lower()
    n = min(len(a), len(b))
    limit = 0 if n <= 1 else 1 if n <= 5 else 2 if n <= 8 else 3 if n <= 11 else 4
    return a[0] != b[0] or levenshtein(a, b) > limit


def read_pairs(path):
    pairs = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            a, b = row["certificate_A"], row["certificate_B"]
            if a != b:
                pairs[tuple(sorted((a, b)))] = abs(int(row["year_diff"]))
    return pairs


def connected_groups(pairs):
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        parent[find(a)] = find(b)
    groups = defaultdict(list)
    for x in parent:
        groups[find(x)].append(x)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: (-len(g), g[0]))


def main(out, runs, check_data=None):
    found_by = defaultdict(list)
    year_diff = {}
    for label, path in runs:
        pairs = read_pairs(path)
        print(f"{label}: {len(pairs)} pairs")
        for pair, diff in pairs.items():
            found_by[pair].append(label)
            year_diff[pair] = diff

    if check_data:
        surnames = read_parent_surnames(check_data)
        dropped = 0
        for pair, labels in list(found_by.items()):
            if not all("patronym" in label for label in labels):
                continue
            (fa, ma), (fb, mb) = (surnames.get(b, (None, None)) for b in pair)
            if names_differ(fa, fb) or names_differ(ma, mb):
                del found_by[pair]
                dropped += 1
        print(f"family-name check: {dropped} patronym-only pairs dropped")

    with open(f"{out}-pairs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["baptism_A", "baptism_B", "year_diff", "found_by"])
        for pair in sorted(found_by):
            w.writerow([*pair, year_diff[pair], ";".join(found_by[pair])])

    groups = connected_groups(found_by)
    with open(f"{out}-groups.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "size", "baptism"])
        for i, g in enumerate(groups, 1):
            for baptism in g:
                w.writerow([i, len(g), baptism])

    print(f"union: {len(found_by)} pairs")
    for combo, n in Counter(";".join(v) for v in found_by.values()).most_common():
        print(f"  found by {combo}: {n}")
    sizes = Counter(len(g) for g in groups)
    print(f"{len(groups)} sibling groups with {sum(len(g) for g in groups)} baptisms; "
          "sizes " + ", ".join(f"{s}: {n}" for s, n in sorted(sizes.items())))
    print(f"written: {out}-pairs.csv, {out}-groups.csv")


if __name__ == "__main__":
    args = sys.argv[1:]
    check_data = None
    if args[:1] == ["--family-name-check"] and len(args) > 1:
        check_data, args = args[1], args[2:]
    if len(args) < 2 or any("=" not in a for a in args[1:]):
        sys.exit("usage: sibling_groups.py [--family-name-check <baptisms.nt>] <out> <label>=<csv> [<label>=<csv> ...]")
    main(args[0], [a.split("=", 1) for a in args[1:]], check_data)
