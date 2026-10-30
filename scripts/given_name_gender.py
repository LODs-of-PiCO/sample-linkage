#!/usr/bin/env python3
"""Make a given name -> gender lookup from Bloothooft's given-name list
(elo-dtb lookup-tables/bloothooft-given-names.nt.gz).

The list has one entry per name and gender, with a count of how often the
name is used (gn_tokens_firstname). Some names occur for both genders, for
example Frans (97496 male, 40 female). This keeps the most used gender per
name and writes it as N-Triples with the name as an @nl literal, so it
joins directly with sdo:givenName in the ELO data:

    <entry> clariahnames:gn "Frans"@nl ; sdo:gender sdo:Male ."""

import gzip
import sys

from rdflib import Graph, Literal, Namespace, URIRef

GN = Namespace("https://linkeddata.cultureelerfgoed.nl/clariahnames/vocab/")
SDO = Namespace("https://schema.org/")


def main(bloothooft, out_nt):
    g = Graph()
    with gzip.open(bloothooft, "rb") as f:
        g.parse(f, format="nt")

    best = {}   # name -> (count, entry, gender)
    for entry, name in g.subject_objects(GN.gn):
        gender = g.value(entry, SDO.gender)
        count = g.value(entry, GN.gn_tokens_firstname)
        count = int(count) if count is not None else 0
        name = str(name)
        if gender is not None and (name not in best or count > best[name][0]):
            best[name] = (count, entry, gender)

    out = Graph()
    for name, (count, entry, gender) in best.items():
        out.add((entry, GN.gn, Literal(name, lang="nl")))
        out.add((entry, SDO.gender, gender))
    out.serialize(out_nt, format="nt", encoding="utf-8")
    print(f"{len(best)} names written to {out_nt}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: given_name_gender.py <bloothooft-given-names.nt.gz> <out.nt>")
    main(sys.argv[1], sys.argv[2])
