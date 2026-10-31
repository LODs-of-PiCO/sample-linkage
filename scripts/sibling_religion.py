#!/usr/bin/env python3
"""Add the denomination of each baptism (elo-religion.nt.gz: picom:hasReligion on
the baptised child, IISG TaxonomyOfReligions) to the sibling groups, and flag
groups whose baptisms took place in different churches.

Siblings were usually baptised in the same church, so a group that mixes
denominations (say Nederduitse Gereformeerde Kerk and Rooms-Katholieke Kerk)
may join different families, or show a family that changed church.

Writes <out>.csv: group, size, with_religion, religions (name:count, ";"),
mixed (yes/no).

usage: sibling_religion.py <religion.nt.gz> <groups.csv> <out.csv>"""

import csv
import gzip
import sys
from collections import Counter, defaultdict


def main(religion_nt, groups_csv, out_csv):
    religion = {}
    with gzip.open(religion_nt, "rt", encoding="utf-8") as f:
        for line in f:
            s, p, o = line.rstrip(" .\n").split(" ", 2)
            if "_Person_" in s and p == "<https://personsincontext.org/model#hasReligion>":
                religion[s[1:s.index("_Person_")]] = o.rsplit("/", 1)[1][:-1].replace("-", " ")
    groups = defaultdict(list)
    with open(groups_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            groups[r["group"]].append(r["baptism"])
    stats = Counter()
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "size", "with_religion", "religions", "mixed"])
        for g, bs in groups.items():
            c = Counter(religion[b] for b in bs if b in religion)
            mixed = len(c) > 1
            stats["mixed" if mixed else "one" if c else "none"] += 1
            w.writerow([g, len(bs), sum(c.values()), ";".join(f"{k}:{v}" for k, v in c.most_common()), "yes" if mixed else "no"])
    print(f"{len(religion)} baptisms with a denomination; sibling groups: "
          f"one denomination {stats['one']}, mixed {stats['mixed']}, none known {stats['none']}")
    print(f"written: {out_csv}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: sibling_religion.py <religion.nt.gz> <groups.csv> <out.csv>")
    main(*sys.argv[1:])
