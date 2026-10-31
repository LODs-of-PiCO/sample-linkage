"""Data for Threads of Leiden: every baptism (date, family, row height) and every
sibling pair, from the union of the four sibling runs with the family-name check.

Writes viz/threads-of-leiden/baptisms.b64.txt, pairs.b64.txt and meta.json.
Binary records, base64-encoded because artifacts only serve text types:
    baptism  <uint32 days since 1550-01-01><uint16 row><uint32 family index>
    pair     <uint32 baptism A><uint32 baptism B><uint8 runs that found it>
Run from the repository root after scripts/sibling_groups.py --family-name-check
has written work/siblings-checked-*.csv."""

import base64, csv, io, json, os, random, struct, sys
from datetime import date
sys.path.insert(0, os.path.dirname(__file__))
from common import THREADS, baptism_info

date_of, par, cn = baptism_info()
ids = sorted(date_of, key=lambda b: date_of[b])
D0 = date(1550, 1, 1).toordinal()


def day(b):
    try:
        return date.fromisoformat(date_of[b]).toordinal() - D0
    except ValueError:  # dates that do not exist, such as 1715-09-31
        y, m, _ = date_of[b].split("-")
        return date(int(y), int(m), 28).toordinal() - D0


idx = {b: i for i, b in enumerate(ids)}
fam = [0] * len(ids)
groups = {}
for r in csv.DictReader(open("work/siblings-checked-groups.csv")):
    groups.setdefault(int(r["group"]), []).append(r["baptism"])
labels = [""]
for g, bs in sorted(groups.items()):
    k = len(labels)
    labels.append(par[min(bs, key=lambda b: date_of[b])])
    for b in bs:
        fam[idx[b]] = k

random.seed(7)
row = {}
def y_of(i):
    f = fam[i]
    if f == 0:
        return random.randint(0, 65535)
    if f not in row:
        row[f] = random.randint(0, 65535)
    return row[f]

RUNS = {"familyname": 1, "familyname-std": 2, "patronym": 4, "patronym-std": 8}
pairs = []
for r in csv.DictReader(open("work/siblings-checked-pairs.csv")):
    pairs.append((idx[r["baptism_A"]], idx[r["baptism_B"]], sum(RUNS[l] for l in r["found_by"].split(";"))))

bb, pb = io.BytesIO(), io.BytesIO()
for i, b in enumerate(ids):
    bb.write(struct.pack("<IHI", day(b), y_of(i), fam[i]))
for a, b, m in pairs:
    pb.write(struct.pack("<IIB", a, b, m))
open(f"{THREADS}/baptisms.b64.txt", "w").write(base64.b64encode(bb.getvalue()).decode())
open(f"{THREADS}/pairs.b64.txt", "w").write(base64.b64encode(pb.getvalue()).decode())
json.dump({"baptisms": len(ids), "pairs": len(pairs), "families": len(groups), "in_families": sum(1 for x in fam if x),
           "day0": "1550-01-01", "first": date_of[ids[0]], "last": date_of[ids[-1]], "labels": labels},
          open(f"{THREADS}/meta.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(ids), "baptisms", len(pairs), "pairs", len(groups), "families")
