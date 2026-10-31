"""Data for the Family Browser (viz/family-browser/browser4.json): union sibling groups of the four runs,
per pair which runs found it and whether the family-name check drops it, plus the parents' patronyms.
Run from the repository root."""
import csv, json, pickle, random
from collections import defaultdict
from datetime import date
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import WORK, THREADS, BROWSER, baptism_info
RUNS=["familyname","familyname-std","patronym","patronym-std"]
date_of, par, cn = baptism_info()
def read_patronyms(path):
    """record IRI -> (father's patronym, mother's patronym), "" when there is none."""
    pat, node, parents, gender = {}, {}, defaultdict(list), {}
    for line in open(path, encoding="utf-8"):
        s, p, o = line.rstrip(" .\n").split(" ", 2)
        if p == "<https://w3id.org/pnv#patronym>": pat[s] = o[1:o.rindex('"')]
        elif p == "<https://schema.org/additionalName>": node[s] = o
        elif p == "<https://schema.org/parent>": parents[s].append(o)
        elif p == "<https://schema.org/gender>": gender[s] = o
    out = {}
    for child, ps in parents.items():
        f = next((q for q in ps if gender.get(q) == "<https://schema.org/Male>"), None)
        m = next((q for q in ps if gender.get(q) == "<https://schema.org/Female>"), None)
        out[child[1:child.index("_Person_")]] = (pat.get(node.get(f), ""), pat.get(node.get(m), ""))
    return out
patr = read_patronyms("data/elo-baptisms-before-1811.nt")
groups=defaultdict(list)
for r in csv.DictReader(open("work/siblings-groups.csv")): groups[int(r["group"])].append(r["baptism"])
kept={(r["baptism_A"],r["baptism_B"]) for r in csv.DictReader(open("work/siblings-checked-pairs.csv"))}
random.seed(1811)
big=[g for g,v in groups.items() if len(v)>=10]
small=[g for g,v in groups.items() if len(v)<10]
pick=set(big)|set(random.sample(small,4000))
inpick={b for g in pick for b in groups[g]}
pairs=defaultdict(list)
for r in csv.DictReader(open("work/siblings-pairs.csv")):
    a,b=r["baptism_A"],r["baptism_B"]
    if a in inpick:
        m=sum(1<<RUNS.index(l) for l in r["found_by"].split(";"))
        if (a,b) not in kept: m|=16
        pairs[a].append((b,m))
def lv(a,b):
    p=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        c=[i]
        for j,y in enumerate(b,1): c.append(min(p[j]+1,c[j-1]+1,p[j-1]+(x!=y)))
        p=c
    return p[-1]
recs=[]; G=[]
for g in sorted(pick,key=lambda g:(-len(groups[g]),g)):
    bs=sorted(groups[g],key=lambda b:(date_of[b],cn[b]))
    idx={}
    for b in bs:
        f,m=(par[b].split(" & ",1)+["?"])[:2]
        idx[b]=len(recs); recs.append([date_of[b],cn[b],f,m,b.rsplit("record_elo_",1)[-1],*patr.get(b,("",""))])
    E=[[idx[a],idx[b],m] for a in bs for b,m in pairs[a] if b in idx]
    flags=[]
    try:
        dd=sorted(date.fromisoformat(date_of[b]) for b in bs)
        if any(0<(dd[i+1]-dd[i]).days<=270 for i in range(len(dd)-1)): flags.append("gap")
        if (dd[-1]-dd[0]).days>25*365.25: flags.append("span")
    except ValueError: pass
    if len(bs)<=60:
        same=[(i,j) for i in range(len(bs)) for j in range(i+1,len(bs)) if date_of[bs[i]]==date_of[bs[j]]]
        if any(lv(cn[bs[i]].lower(),cn[bs[j]].lower())<=2 for i,j in same): flags.append("dup")
        if any(lv(cn[bs[i]].lower(),cn[bs[j]].lower())>2 for i,j in same): flags.append("twin")
    if any(e[2]&16 for e in E): flags.append("check")
    if any(e[2]&3 for e in E) and any(e[2]&12 for e in E): flags.append("both")
    G.append([g,[idx[b] for b in bs],E,flags])
json.dump({"runs":RUNS,"recs":recs,"groups":G,"total_groups":len(groups),"total_baptisms":sum(len(v) for v in groups.values()),"total_pairs":sum(len(v) for v in pairs.values())},open(f"{BROWSER}/browser4.json","w"),separators=(",",":"),ensure_ascii=False)
print(len(G),"groups",len(big),"big",len(recs),"records",sum(len(x[2]) for x in G),"pairs")
