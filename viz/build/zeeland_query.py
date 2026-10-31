"""Run the "Zeeland-born brides and grooms married in Leiden" query (matgui.coret.org/s/NSheuzAr,
with extra columns for joining) on the ELO endpoint https://qlever.coret.org/elo and save it as CSV.

usage: zeeland_query.py viz/build/work/zeeland.csv"""
import csv, json, sys, urllib.request, urllib.parse
Q = """PREFIX schema: <https://schema.org/> PREFIX prov: <http://www.w3.org/ns/prov#> PREFIX picom: <https://personsincontext.org/model#>
PREFIX thpg: <https://terms.personsincontext.org/ThesaurusHistorischePersoonsgegevens/>
SELECT ?datum ?s ?naam ?gender ?geborenUri ?geboren ?rec ?sp ?partner ?partnerGeborenUri ?partnerGeboren
WHERE {
  GRAPH <http://lodsofpico/topouris> { ?s schema:birthPlace ?geborenUri . }
  ?geborenUri schema:addressRegion <https://iisg.amsterdam/resource/ListOfToponyms/province/Zeeland_Nederland> ;
              schema:name ?geboren .
  ?s picom:hasRole <https://terms.personsincontext.org/roles/574> ; schema:name ?naam ; prov:hadPrimarySource ?rec .
  OPTIONAL { ?s schema:gender ?gender }
  ?rec schema:additionalType thpg:549 ;
       schema:description "Doop-, trouw-, begraaf- en geboorteboeken Leiden (DTB Leiden)"@nl ;
       schema:dateCreated ?datum .
  OPTIONAL { ?s schema:spouse ?sp . ?sp schema:name ?partner .
    OPTIONAL { GRAPH <http://lodsofpico/topouris> { ?sp schema:birthPlace ?partnerGeborenUri . } ?partnerGeborenUri schema:name ?partnerGeboren . } }
}
ORDER BY ?datum LIMIT 10000"""
req = urllib.request.Request("https://qlever.coret.org/elo", data=urllib.parse.urlencode({"query": Q}).encode(),
                             headers={"Accept": "application/sparql-results+json"})
d = json.load(urllib.request.urlopen(req, timeout=300))
vs = d["head"]["vars"]
with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(vs)
    for b in d["results"]["bindings"]: w.writerow([b[v]["value"] if v in b else "" for v in vs])
print(len(d["results"]["bindings"]), "rows")
