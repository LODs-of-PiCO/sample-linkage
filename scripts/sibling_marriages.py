#!/usr/bin/env python3
"""Combine burgerLinker's baptism -> marriage links per sibling group, and
compare the place of each baptism with the place of the marriage.

Each run is given as <label>=<BETWEEN_B-M csv>, in which certificate_A is a
baptism and certificate_B a marriage. A baptism links to a marriage when at
least one run links them (the union of the runs).

Sibling groups come from sibling_groups.py (<groups.csv>: group, size,
baptism). A baptism that is in no group is its own group of one. Per group
the marriages its baptisms link to are counted:

    one marriage     all linked baptisms point to the same marriage
    several          the baptisms point to different marriages; the
                     marriage with most baptisms is given as the best
    none             no baptism of the group links to a marriage

Places are IISG toponyms (…/ListOfToponyms/location/Place_Municipality_
Province_Country). Baptism: the place of the baptism event, otherwise where
the record was made, from oa-pico-toponiemen.nt.gz. Marriage: the place of the
marriage event, otherwise of the ondertrouw, from dtb_trouwen.nt.gz. Two
places are "same municipality" when their municipality part is equal.

Writes
    <out>-links.csv   baptism, marriage, year_diff, found_by, group,
                      baptism_place, marriage_place, same_municipality
    <out>-groups.csv  group, size, linked_baptisms, status, marriage,
                      baptisms_to_marriage, other_marriages, marriage_place

usage: sibling_marriages.py <out> <groups.csv> <toponiemen.nt.gz> <dtb_trouwen.nt.gz> <label>=<csv> [<label>=<csv> ...]"""

import csv
import gzip
import sys
from collections import Counter, defaultdict

TOPONYM = "<https://iisg.amsterdam/resource/ListOfToponyms/location/"
EVENT_PLACE = "<https://personsincontext.org/model#eventPlace>"
LOCATION_CREATED = "<https://schema.org/locationCreated>"


def read_places(path, events):
    """record IRI -> toponym name, preferring the events in order."""
    found = defaultdict(dict)
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            s, p, o = line.rstrip(" .\n").split(" ", 2)
            if not o.startswith(TOPONYM) or not s.startswith("<"):
                continue
            place = o[len(TOPONYM):-1]
            if p == EVENT_PLACE:
                for kind in events:
                    if s.endswith(f"_{kind}_event>"):
                        found[s[1:-len(f"_{kind}_event>")]][kind] = place
            elif p == LOCATION_CREATED and "_Person_" not in s:
                found[s[1:-1]]["record"] = place
    order = list(events) + ["record"]
    return {r: next(k[e] for e in order if e in k) for r, k in found.items()}


def municipality(place):
    parts = place.split("_") if place else []
    return parts[1] if len(parts) > 1 else None


def main(out, groups_csv, toponiemen, trouwen, runs):
    group_of, size = {}, {}
    with open(groups_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            group_of[row["baptism"]] = row["group"]
            size[row["group"]] = int(row["size"])

    found_by = defaultdict(list)
    year_diff = {}
    for label, path in runs:
        n = 0
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pair = (row["certificate_A"], row["certificate_B"])
                found_by[pair].append(label)
                year_diff[pair] = int(row["year_diff"])
                n += 1
        print(f"{label}: {n} links")
    print(f"union: {len(found_by)} baptism-marriage links")

    baptism_place = read_places(toponiemen, ["doop"])
    marriage_place = read_places(trouwen, ["huwelijk", "ondertrouw"])

    links_of = defaultdict(list)
    same = Counter()
    with open(f"{out}-links.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["baptism", "marriage", "year_diff", "found_by", "group",
                    "baptism_place", "marriage_place", "same_municipality"])
        for (b, m), labels in sorted(found_by.items()):
            g = group_of.get(b, "single:" + b)
            bp, mp = baptism_place.get(b), marriage_place.get(m)
            s = "" if not (bp and mp) else "yes" if municipality(bp) == municipality(mp) else "no"
            same[s or "unknown"] += 1
            w.writerow([b, m, year_diff[(b, m)], ";".join(labels), g, bp or "", mp or "", s])
            links_of[g].append((b, m))

    status = Counter()
    with open(f"{out}-groups.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "size", "linked_baptisms", "status", "marriage",
                    "baptisms_to_marriage", "other_marriages", "marriage_place"])
        for g in sorted(set(size) | set(links_of), key=lambda g: (g.startswith("single:"), g)):
            links = links_of.get(g, [])
            votes = Counter()
            for b, m in set(links):
                votes[m] += 1
            linked = len({b for b, _ in links})
            if not votes:
                st, best, n_best = "none", "", 0
            else:
                best, n_best = votes.most_common(1)[0]
                st = "one marriage" if len(votes) == 1 else "several"
            kind = "single" if g.startswith("single:") else "group"
            status[(kind, st)] += 1
            w.writerow([g, size.get(g, 1), linked, st, best, n_best,
                        len(votes) - 1 if votes else 0, marriage_place.get(best, "")])

    print("baptism and marriage in the same municipality: " +
          ", ".join(f"{k} {v}" for k, v in same.most_common()))
    for kind in ("group", "single"):
        print(f"{'sibling groups' if kind == 'group' else 'baptisms in no group (linked ones only)'}: " +
              ", ".join(f"{st} {status[(kind, st)]}" for st in ("one marriage", "several", "none") if status[(kind, st)]))
    print(f"written: {out}-links.csv, {out}-groups.csv")


if __name__ == "__main__":
    if len(sys.argv) < 6 or any("=" not in a for a in sys.argv[5:]):
        sys.exit("usage: sibling_marriages.py <out> <groups.csv> <toponiemen.nt.gz> <dtb_trouwen.nt.gz> <label>=<csv> [<label>=<csv> ...]")
    main(*sys.argv[1:5], [a.split("=", 1) for a in sys.argv[5:]])
