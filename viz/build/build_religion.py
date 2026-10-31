"""Denomination per baptism for Threads of Leiden (viz/threads-of-leiden/religion.b64.txt).

One byte per baptism, in the same order as baptisms.b64.txt (sorted by date),
base64-encoded:
    0 Nederduitse Gereformeerde Kerk
    1 Rooms-Katholieke Kerk
    2 Remonstrantse Broederschap
    3 other or unknown (Doopsgezinden, Oud-Katholieke Kerk, Anglicaanse Kerk,
      Waalse Kerk, or no denomination recorded)
The denomination is picom:hasReligion on the baptised child in data/elo-religion.nt.gz.
Run from the repository root."""

import base64, collections, gzip, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import THREADS, baptism_info

CODE = {"Nederduitse-Gereformeerde-Kerk": 0, "Rooms-Katholieke-Kerk": 1, "Remonstrantse-Broederschap": 2}
date_of, par, cn = baptism_info()
ids = sorted(date_of, key=lambda b: date_of[b])
rel = {}
with gzip.open("data/elo-religion.nt.gz", "rt", encoding="utf-8") as f:
    for line in f:
        s, p, o = line.rstrip(" .\n").split(" ", 2)
        if "_Person_" in s:
            rel[s[1:s.index("_Person_")]] = CODE.get(o.rsplit("/", 1)[1][:-1], 3)
codes = bytes(rel.get(b, 3) for b in ids)
open(f"{THREADS}/religion.b64.txt", "w").write(base64.b64encode(codes).decode())
print(len(codes), "baptisms:", dict(collections.Counter(codes)))
