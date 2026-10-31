"""Marriage records per year for the counters of Threads of Leiden
(viz/threads-of-leiden/marriage-counts.json): all ELO DTB marriages before 1811
(scripts/select_marriages.sh) and those linked to at least one baptism
(scripts/sibling_marriages.py). Run from the repository root."""

import collections, csv, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import THREADS

year = {}
for line in open("data/elo-marriages-before-1811.nt", encoding="utf-8"):
    if "<https://schema.org/dateCreated>" in line:
        year[line.split(" ", 1)[0][1:-1]] = int(line.split('"')[1][:4])
linked = {r["marriage"] for r in csv.DictReader(open("work/sibling-marriages-links.csv"))}
y0, y1 = min(year.values()), max(year.values())
allc, linkc = collections.Counter(year.values()), collections.Counter(year[m] for m in linked if m in year)
json.dump({"first": y0, "all": [allc[y] for y in range(y0, y1 + 1)], "linked": [linkc[y] for y in range(y0, y1 + 1)]},
          open(f"{THREADS}/marriage-counts.json", "w"), separators=(",", ":"))
print(f"{len(year)} marriage records {y0}-{y1}, {sum(linkc.values())} linked to baptisms")
