"""Data for the Zeeland view of Threads of Leiden (viz/threads-of-leiden/zeeland.json): Zeeland-born
brides and grooms (zeeland_query.py) joined to the marriage -> baptism links of scripts/sibling_marriages.py.
Run from the repository root."""
import csv, json, pickle, collections
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import WORK, THREADS, BROWSER, baptism_info
# approximate coordinates (lat, lon) per municipality, from general knowledge; good enough for a regional map
C={"Middelburg":(51.499,3.614),"Vlissingen":(51.442,3.573),"Goes":(51.504,3.889),"Zierikzee":(51.650,3.919),"Hulst":(51.280,4.052),
"Veere":(51.548,3.667),"Tholen":(51.532,4.221),"Axel":(51.266,3.908),"Sas-van-Gent":(51.227,3.798),"Brouwershaven":(51.726,3.912),
"Aardenburg":(51.273,3.447),"Arnemuiden":(51.502,3.674),"Scherpenisse":(51.546,4.103),"Domburg":(51.563,3.497),"Nieuwerkerk":(51.651,4.003),
"Breskens":(51.396,3.555),"Koudekerke":(51.482,3.556),"Noordgouwe":(51.689,3.949),"Cadzand":(51.367,3.389),"Oostkapelle":(51.566,3.551),
"IJzendijke":(51.322,3.617),"Bruinisse":(51.660,4.090),"Sluis":(51.308,3.386),"Kapelle":(51.487,3.958),"Renesse":(51.733,3.775),
"s-Heerenhoek":(51.457,3.766),"Haamstede":(51.700,3.743),"Oud-Vossemeer":(51.570,4.200),"s-Heer-Hendrikskinderen":(51.493,3.866),
"Nisse":(51.465,3.903),"Bommenede":(51.700,4.050),"s-Heer-Arendskerke":(51.494,3.823),"Baarland":(51.398,3.904),"Ovezande":(51.432,3.825),
"Philippine":(51.284,3.749),"Eede":(51.256,3.454),"Heille":(51.290,3.385),"Poortvliet":(51.544,4.143),"Oostburg":(51.326,3.488),
"Groede":(51.383,3.502),"Kattendijke":(51.500,3.948),"Wolphaartsdijk":(51.545,3.810),"Meliskerke":(51.520,3.509),
"Hoedekenskerke":(51.416,3.919),"Kruiningen":(51.447,4.034),"Yerseke":(51.494,4.050),"Ouwerkerk":(51.620,3.987),"Heinkenszand":(51.473,3.811)}
LEIDEN=(52.160,4.497)
date_of, par, cn = baptism_info()
mdate={}
for line in open("data/elo-marriages-before-1811.nt",encoding="utf-8"):
    if "dateCreated" in line: mdate[line.split(" ",1)[0][1:-1]]=line.split('"')[1]
links=collections.defaultdict(set)
for r in csv.DictReader(open("work/sibling-marriages-links.csv")): links[r["marriage"]].add(r["baptism"])
persons={}
for r in csv.DictReader(open(f"{WORK}/zeeland.csv")):
    p=r["s"]
    if p in persons: continue
    mun=r["geborenUri"].rsplit("/",1)[1].split("_")[1]
    pg=r["partnerGeborenUri"].rsplit("/",1)[1].split("_")[1].replace("-"," ") if r["partnerGeborenUri"] else ""
    persons[p]=dict(name=r["naam"],g="F" if r["gender"].endswith("Female") else "M",mun=mun,born=r["geboren"],
                    rec=r["rec"],date=mdate.get(r["rec"],r["datum"][:10]),partner=r["partner"],pborn=pg)
marr={}
for p in persons.values():
    m=marr.setdefault(p["rec"],{"date":p["date"],"z":[],"kids":[]})
    m["z"].append(p)
for rec,m in marr.items():
    m["kids"]=sorted((date_of[b],cn[b],par[b]) for b in links.get(rec,()))
places=collections.Counter(p["mun"] for p in persons.values())
out={"leiden":LEIDEN,
 "places":{k:[C[k][0],C[k][1],v,next(p["born"] for p in persons.values() if p["mun"]==k)] for k,v in places.items() if k in C},
 "marriages":[]}
missing=[k for k in places if k not in C]
for rec,m in sorted(marr.items(),key=lambda x:x[1]["date"]):
    out["marriages"].append({"id":rec.rsplit("_",1)[1],"d":m["date"],
        "z":[[p["name"],p["g"],p["mun"],p["partner"],p["pborn"]] for p in m["z"]],
        "k":[[d,c,pa] for d,c,pa in m["kids"]]})
json.dump(out,open(f"{THREADS}/zeeland.json","w"),ensure_ascii=False,separators=(",",":"))
print("persons",len(persons),"marriages",len(marr),"with kids",sum(1 for m in marr.values() if m["kids"]),"kids",sum(len(m["kids"]) for m in marr.values()),"missing coords",missing)
