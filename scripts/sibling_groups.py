#!/usr/bin/env python3
"""Combine the sibling links of several burgerLinker runs into one set of
sibling pairs and sibling groups.

Each run is given as <label>=<BETWEEN_B-M csv>, for example

    familyname=work/familyname/between_b-m-maxLev-4/results/BETWEEN_B-M-maxLev-4.csv

A pair of baptisms is a sibling pair when at least one run links them (the
union of the runs). Self-links (certificate_A = certificate_B) are dropped,
and A-B and B-A count as one pair. Sibling groups are the connected groups
of baptisms: if A-B and B-C are pairs, A, B and C form one group.

Writes
    <out>-pairs.csv   baptism_A, baptism_B, year_diff, found_by (labels, ";")
    <out>-groups.csv  group, size, baptism

usage: sibling_groups.py <out> <label>=<csv> [<label>=<csv> ...]"""

import csv
import sys
from collections import Counter, defaultdict


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


def main(out, runs):
    found_by = defaultdict(list)
    year_diff = {}
    for label, path in runs:
        pairs = read_pairs(path)
        print(f"{label}: {len(pairs)} pairs")
        for pair, diff in pairs.items():
            found_by[pair].append(label)
            year_diff[pair] = diff

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
    if len(sys.argv) < 3 or any("=" not in a for a in sys.argv[2:]):
        sys.exit("usage: sibling_groups.py <out> <label>=<csv> [<label>=<csv> ...]")
    main(sys.argv[1], [a.split("=", 1) for a in sys.argv[2:]])
