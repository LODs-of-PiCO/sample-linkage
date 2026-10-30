#!/usr/bin/env bash
# Cut the records with a child (role 575: baptised or newborn child) out
# of the full ELO PiCo dump, keeping only the triples burgerLinker and our
# checks need.
#
# usage: scripts/extract_child_records.sh <elo-pico.nt.gz> <out.nt>
#
# Kept:
#   record   sdo:dateCreated, sdo:description, sdo:name, sdo:additionalType
#   person   prov:hadPrimarySource, picom:hasRole, sdo:gender, sdo:name,
#            sdo:givenName, sdo:familyName, sdo:parent, sdo:additionalName
#   name     pnv:patronym, pnv:baseSurname, pnv:surnamePrefix (blank nodes)
#
# Person IRIs are the record IRI followed by _Person_<id>, which is how a
# person is tied to its record in the first pass.

set -euo pipefail

if [ $# -ne 2 ]; then
    echo "usage: $0 <elo-pico.nt.gz> <out.nt>" >&2
    exit 1
fi
DUMP="$1"
OUT="$2"
RECORDS="$(mktemp)"
trap 'rm -f "$RECORDS"' EXIT

# Pass 1: records that have a person with role 575.
zcat "$DUMP" | awk '
$2 == "<https://personsincontext.org/model#hasRole>" &&
$3 == "<https://terms.personsincontext.org/roles/575>" {
    rec = $1; sub(/_Person_.*/, ">", rec); print rec
}' | sort -u > "$RECORDS"
echo "records with a child: $(wc -l < "$RECORDS")"

# Pass 2: the triples of those records and their persons, and all name parts.
zcat "$DUMP" | awk -v records="$RECORDS" '
BEGIN {
    while ((getline r < records) > 0) keep[r] = 1
    split("dateCreated description name additionalType", a, " ")
    for (i in a) recPred["<https://schema.org/" a[i] ">"] = 1
    split("gender name givenName familyName parent additionalName", a, " ")
    for (i in a) perPred["<https://schema.org/" a[i] ">"] = 1
    perPred["<http://www.w3.org/ns/prov#hadPrimarySource>"] = 1
    perPred["<https://personsincontext.org/model#hasRole>"] = 1
    split("patronym baseSurname surnamePrefix", a, " ")
    for (i in a) namePred["<https://w3id.org/pnv#" a[i] ">"] = 1
}
substr($1, 1, 2) == "_:" { if ($2 in namePred) print; next }
($1 in keep) { if ($2 in recPred) print; next }
index($1, "_Person_") {
    rec = $1; sub(/_Person_.*/, ">", rec)
    if ((rec in keep) && ($2 in perPred)) print
}' > "$OUT"
echo "triples written: $(wc -l < "$OUT") to $OUT"
