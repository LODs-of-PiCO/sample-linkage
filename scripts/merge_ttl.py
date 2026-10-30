#!/usr/bin/env python3
"""Merge a directory of Turtle files into one N-Triples file for burgerLinker,
which takes files, not directories, as input."""

import sys
from pathlib import Path

from rdflib import Graph


def main(src_dir, out_file):
    g = Graph()
    files = sorted(Path(src_dir).glob("*.ttl"))
    for f in files:
        g.parse(f, format="turtle")
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=out_file, format="nt", encoding="utf-8")
    print(f"merged {len(files)} files, {len(g)} triples -> {out_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: merge_ttl.py <directory with .ttl files> <output .nt>")
    main(sys.argv[1], sys.argv[2])
