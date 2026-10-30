#!/usr/bin/env python3
"""Add a standardised given name to every person in an N-Triples file, using
Bloothooft's given-name list (elo-dtb lookup-tables/bloothooft-given-names.nt.gz).

For each sdo:givenName this writes one extra triple

    <person> <https://github.com/LODs-of-PiCO/sample-linkage#standardGivenName> "johannes heimrijk"@nl .

so the original name stays in the data and a data model can choose which
one burgerLinker compares.

How a given name is standardised:
  1. "N.n." (nomen nescio, name unknown) gets no standardised name.
  2. "*" is removed; brackets inside a word are dropped ("Cath(arina)" ->
     "Catharina"); a name in brackets after a space is an extra given name
     ("Grietje (Margrietgen)" -> "Grietje Margrietgen").
  3. The name is split on spaces and hyphens. Each part is looked up in the
     list (ignoring case) and replaced by its standard form (gn_standard).
     When a part occurs more than once in the list, the standard of the most
     used entry (gn_tokens_firstname) is taken. Parts that are not in the
     list, or have no standard, are kept, in lower case.
  4. The parts are joined again with a space, in the original order.

usage: standardise_given_names.py <bloothooft-given-names.nt.gz> <in.nt> <out.nt>

out.nt is in.nt plus the extra triples."""

import gzip
import re
import sys
from collections import Counter

GIVEN = "<https://schema.org/givenName>"
STANDARD = "<https://github.com/LODs-of-PiCO/sample-linkage#standardGivenName>"
VOCAB = "https://linkeddata.cultureelerfgoed.nl/clariahnames/vocab/"
LITERAL = re.compile(r'^"(.*)"(@[a-z]+|\^\^<[^>]+>)?$')


def load_standards(path):
    """name (lower case) -> standard form of its most used entry."""
    name, standard, count = {}, {}, {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            s, p, o = line.rstrip(" .\n").split(" ", 2)
            p = p[1:-1]
            if not p.startswith(VOCAB):
                continue
            key = p[len(VOCAB):]
            m = LITERAL.match(o)
            value = m.group(1) if m else o
            if key == "gn":
                name[s] = value
            elif key == "gn_standard":
                standard[s] = value
            elif key == "gn_tokens_firstname":
                count[s] = int(value)
    best = {}
    for entry, n in name.items():
        if entry not in standard:
            continue
        k = n.lower()
        if k not in best or count.get(entry, 0) > best[k][0]:
            best[k] = (count.get(entry, 0), standard[entry])
    return {k: v for k, (_, v) in best.items()}


def standardise(given, standards, stats):
    if given.strip().lower() in ("n.n.", "n.n", "nn"):
        stats["unknown (N.n.)"] += 1
        return None
    g = given.replace("*", "")
    g = re.sub(r"(\w)\((\w+)\)", r"\1\2", g)   # Cath(arina) -> Catharina
    g = g.replace("(", " ").replace(")", " ")
    parts = [p for p in re.split(r"[\s\-]+", g) if p]
    out = []
    for part in parts:
        std = standards.get(part.lower())
        stats["parts found" if std else "parts not found"] += 1
        out.append(std if std else part.lower())
    return " ".join(out) if out else None


def main(bloothooft, in_nt, out_nt):
    standards = load_standards(bloothooft)
    print(f"{len(standards)} names with a standard form in the list")
    stats = Counter()
    with open(in_nt, encoding="utf-8") as fin, open(out_nt, "w", encoding="utf-8") as fout:
        for line in fin:
            fout.write(line)
            s, p, o = line.rstrip(" .\n").split(" ", 2)
            if p != GIVEN:
                continue
            m = LITERAL.match(o)
            given = m.group(1) if m else o
            std = standardise(given, standards, stats)
            stats["given names"] += 1
            if std:
                std = std.replace("\\", "\\\\").replace('"', '\\"')
                fout.write(f'{s} {STANDARD} "{std}"@nl .\n')
    for k, v in stats.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: standardise_given_names.py <bloothooft-given-names.nt.gz> <in.nt> <out.nt>")
    main(*sys.argv[1:])
