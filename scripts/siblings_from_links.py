#!/usr/bin/env python3
"""Group baptisms into sibling groups from burgerLinker's between_b_m links
to marriages: baptisms whose parents link to the same marriage are siblings.

Writes one row per (marriage, baptism) and prints a summary, including
baptisms that link to more than one marriage (ambiguous links)."""

import csv
import sys
from collections import defaultdict


def short(uri):
    return uri.rsplit(":", 1)[-1]


def main(links_csv, out_csv):
    marriages_of = defaultdict(set)   # baptism -> marriages
    baptisms_of = defaultdict(set)    # marriage -> baptisms
    year_diff = {}
    with open(links_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            baptism, marriage = row["certificate_A"], row["certificate_B"]
            if baptism == marriage:
                continue
            marriages_of[baptism].add(marriage)
            baptisms_of[marriage].add(baptism)
            year_diff[(marriage, baptism)] = row["year_diff"]

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["marriage", "baptism", "years_after_marriage",
                    "siblings_in_group", "baptism_links_to_n_marriages"])
        for marriage in sorted(baptisms_of):
            for baptism in sorted(baptisms_of[marriage]):
                w.writerow([marriage, baptism, year_diff[(marriage, baptism)],
                            len(baptisms_of[marriage]), len(marriages_of[baptism])])

    groups = {m: b for m, b in baptisms_of.items() if len(b) > 1}
    ambiguous = {b: m for b, m in marriages_of.items() if len(m) > 1}
    print(f"marriages with at least one baptism: {len(baptisms_of)}")
    print(f"baptisms linked to a marriage:       {len(marriages_of)}")
    print(f"sibling groups (2+ baptisms):        {len(groups)}")
    for m, bs in sorted(groups.items()):
        print(f"  {short(m)}: " + ", ".join(short(b) for b in sorted(bs)))
    print(f"baptisms linked to 2+ marriages:     {len(ambiguous)}")
    for b, ms in sorted(ambiguous.items()):
        print(f"  {short(b)}: " + ", ".join(short(m) for m in sorted(ms)))
    print(f"written: {out_csv}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: siblings_from_links.py <burgerLinker BETWEEN_B-M csv> <output csv>")
    main(sys.argv[1], sys.argv[2])
