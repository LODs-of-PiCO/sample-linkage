"""Extra data for Threads of Leiden.

marriages.json      family index -> [marriage day (since 1550-01-01), groom, bride,
                    marriage place, baptisms to this marriage, linked baptisms,
                    other candidate marriages, groom's birth place, bride's birth place]
                    for every sibling group linked to a marriage (scripts/sibling_marriages.py).
zeeland-lens.json   baptism indices and family indices of the families whose parents
                    married with a bride or groom born in Zeeland (zeeland_query.py).

Birth places come from data/oa-pico-toponiemen.nt.gz (IISG toponyms). Run from the
repository root after build_overview.py, sibling_marriages.py and zeeland_query.py."""

import collections, csv, gzip, json, os, sys
from datetime import date
sys.path.insert(0, os.path.dirname(__file__))
from common import THREADS, WORK, baptism_info

date_of, par, cn = baptism_info()
ids = sorted(date_of, key=lambda b: date_of[b])
bidx = {b: i for i, b in enumerate(ids)}
gids = sorted({int(r["group"]) for r in csv.DictReader(open("work/siblings-checked-groups.csv"))})
fidx = {str(g): k for k, g in enumerate(gids, 1)}
group_of = {r["baptism"]: r["group"] for r in csv.DictReader(open("work/siblings-checked-groups.csv"))}

# brides and grooms: names with patronym, gender
mdate, P, node, pat = {}, collections.defaultdict(dict), {}, {}
for line in open("data/elo-marriages-before-1811.nt", encoding="utf-8"):
    s, p, o = line.rstrip(" .\n").split(" ", 2)
    if p == "<https://schema.org/dateCreated>": mdate[s[1:-1]] = o.split('"')[1]
    elif p == "<https://w3id.org/pnv#patronym>": pat[s] = o.split('"')[1]
    elif "_Person_" in s:
        if p == "<https://schema.org/additionalName>": node[s] = o
        elif p in ("<https://schema.org/givenName>", "<https://schema.org/familyName>"): P[s][p.rsplit("/", 1)[1][:-1]] = o.split('"')[1]
        elif p == "<https://schema.org/gender>": P[s]["g"] = o
role = {s: ("groom" if d.get("g") == "<https://schema.org/Male>" else "bride") for s, d in P.items()}
names = collections.defaultdict(dict)
for s, d in P.items():
    names[s[1:s.index("_Person_")]][role[s]] = " ".join(x for x in (d.get("givenName", ""), pat.get(node.get(s), ""), d.get("familyName", "")) if x)

# birth places of brides and grooms
T = "<https://iisg.amsterdam/resource/ListOfToponyms/location/"
born = collections.defaultdict(dict)
with gzip.open("data/oa-pico-toponiemen.nt.gz", "rt", encoding="utf-8") as f:
    for line in f:
        s, p, o = line.rstrip(" .\n").split(" ", 2)
        if p == "<https://schema.org/birthPlace>" and s in role and o.startswith(T):
            parts = o[len(T):-1].split("_")
            name, region, country = parts[0].replace("-", " "), parts[-2], parts[-1]
            if country != "Nederland": name += f" ({'Belgium' if country == 'Belgie' else country.replace('-', ' ')})"
            elif region != "Zuid-Holland": name += f" ({region.replace('-', ' ')})"
            born[s[1:s.index("_Person_")]][role[s]] = name

D0 = date(1550, 1, 1).toordinal()
out = {}
for r in csv.DictReader(open("work/sibling-marriages-groups.csv")):
    if r["group"].startswith("single:") or not r["marriage"] or r["marriage"] not in mdate:
        continue
    m = r["marriage"]
    place = r["marriage_place"].split("_")[0].replace("-", " ") if r["marriage_place"] else ""
    out[fidx[r["group"]]] = [date.fromisoformat(mdate[m]).toordinal() - D0, names[m].get("groom", ""), names[m].get("bride", ""), place,
                             int(r["baptisms_to_marriage"]), int(r["linked_baptisms"]), int(r["other_marriages"]),
                             born[m].get("groom", ""), born[m].get("bride", "")]
json.dump(out, open(f"{THREADS}/marriages.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "families with a marriage")

# Zeeland families
zborn = collections.defaultdict(set)
for r in csv.DictReader(open(f"{WORK}/zeeland.csv")):
    zborn[r["rec"]].add(("mother" if r["gender"].endswith("Female") else "father") + " born in " + r["geboren"])
bset, zfam = set(), {}
for r in csv.DictReader(open("work/sibling-marriages-links.csv")):
    if r["marriage"] in zborn:
        bset.add(bidx[r["baptism"]])
        g = group_of.get(r["baptism"])
        if g:
            zfam[fidx[g]] = " · ".join(sorted(zborn[r["marriage"]]))
json.dump({"b": sorted(bset), "fam": zfam}, open(f"{THREADS}/zeeland-lens.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(bset), "Zeeland baptisms in", len(zfam), "families")
