"""Scan of each baptism and marriage record, for the scan icons in Threads of Leiden.

Records link to their scans through schema:associatedMedia; each scan has a
schema:position and a schema:thumbnailUrl on Erfgoed Leiden's IIIF server
(https://elo.memorix.io/resources/iiif/3/<id>/full/!250,250/0/default.jpg).
The first scan (lowest position) of a record is kept, as its IIIF id.

Writes, in viz/threads-of-leiden/:
    scans.b64.txt   16 bytes per baptism (the IIIF id as a UUID, zero when the
                    record has no scan), in the order of baptisms.b64.txt, base64
    and adds the marriage scan id and record id to every entry of marriages.json
    (index 9 and 10)
    and to the marriages and children in zeeland.json.
Run from the repository root after the other builders."""

import base64, csv, gzip, json, os, re, sys, uuid
sys.path.insert(0, os.path.dirname(__file__))
from common import THREADS, baptism_info

UUID = re.compile(r"/iiif/3/([0-9a-f-]{36})/")
media, pos, thumb = {}, {}, {}
with gzip.open("data/elo-pico.nt.gz", "rt", encoding="utf-8") as f:
    for line in f:
        if "associatedMedia" in line or "position" in line or "thumbnailUrl" in line:
            s, p, o = line.rstrip(" .\n").split(" ", 2)
            if p == "<https://schema.org/associatedMedia>" and "_Person_" not in s:
                media.setdefault(s[1:-1], []).append(o)
            elif p == "<https://schema.org/position>":
                pos[s] = int(o.split('"')[1])
            elif p == "<https://schema.org/thumbnailUrl>":
                m = UUID.search(o)
                if m: thumb[s] = m.group(1)


def scan_of(rec):
    nodes = [n for n in media.get(rec, []) if n in thumb]
    return thumb[min(nodes, key=lambda n: pos.get(n, 0))] if nodes else ""


date_of, par, cn = baptism_info()
ids = sorted(date_of, key=lambda b: date_of[b])
raw = b"".join(uuid.UUID(scan_of(b)).bytes if scan_of(b) else bytes(16) for b in ids)
open(f"{THREADS}/scans.b64.txt", "w").write(base64.b64encode(raw).decode())
print(f"baptisms with a scan: {sum(1 for b in ids if scan_of(b))} of {len(ids)}")

# marriages per family: same order of groups as build_overview_extras.py
gids = sorted({int(r["group"]) for r in csv.DictReader(open("work/siblings-checked-groups.csv"))})
fidx = {str(g): k for k, g in enumerate(gids, 1)}
best = {fidx[r["group"]]: r["marriage"] for r in csv.DictReader(open("work/sibling-marriages-groups.csv"))
        if not r["group"].startswith("single:") and r["marriage"]}
mj = json.load(open(f"{THREADS}/marriages.json"))
for k, v in mj.items():
    m = best.get(int(k), "")
    mj[k] = v[:9] + [scan_of(m), m.rsplit("record_elo_", 1)[-1]]
json.dump(mj, open(f"{THREADS}/marriages.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(f"family marriages with a scan: {sum(1 for v in mj.values() if v[9])} of {len(mj)}")

# Zeeland view: marriage and children scans (children matched on date, name and parents)
key = {(date_of[b], cn.get(b, "?"), par.get(b, "?")): b for b in ids}
zj = json.load(open(f"{THREADS}/zeeland.json"))
for m in zj["marriages"]:
    m["s"] = scan_of("https://www.openarchieven.nl/id/record_elo_" + m["id"])
    for k in m["k"]:
        b = key.get((k[0], k[1], k[2]), "")
        k[3:] = [scan_of(b) if b else "", b.rsplit("record_elo_", 1)[-1] if b else ""]
json.dump(zj, open(f"{THREADS}/zeeland.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("Zeeland marriages with a scan:", sum(1 for m in zj["marriages"] if m["s"]), "of", len(zj["marriages"]))
