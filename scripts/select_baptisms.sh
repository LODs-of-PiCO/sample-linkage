#!/usr/bin/env bash
# Select the baptisms before a given year from the output of
# extract_child_records.sh, with only the child and its parents.
#
# usage: scripts/select_baptisms.sh <child-records.nt> <out.nt> [before-year, default 1811]
#
# A record is a baptism when one of its sdo:description values contains
# "Doopdatum" (any case). This also finds the baptism books kept in
# municipal archives, which a selection on collection name would miss.
# Only records with a full date (xsd:date of the form YYYY-MM-DD) before
# <before-year> are kept; burgerLinker cannot read a year, a year-month or
# the few broken dates such as "1700-NaN-07".
#
# Each selected record gets sdo:additionalType
# <https://terms.personsincontext.org/ThesaurusHistorischePersoonsgegevens/548>,
# the baptism type used on the ELO endpoint (https://qlever.coret.org/elo),
# so the same data model works on both. Records and persons also get their
# rdf:type (sdo:ArchiveComponent, picom:PersonObservation): burgerLinker's
# dataset summary fails on a store without any rdf:type.

set -euo pipefail

if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    echo "usage: $0 <child-records.nt> <out.nt> [before-year, default 1811]" >&2
    exit 1
fi
IN="$1"
OUT="$2"
BEFORE="${3:-1811}"

awk -v before="$BEFORE" '
# Pass 1: baptism records, the persons to keep and their name blank nodes.
FNR == NR {
    if (!index($1, "_Person_")) {
        if ($2 == "<https://schema.org/description>" && index(tolower($0), "doopdatum"))
            doop[$1] = 1
        else if ($2 == "<https://schema.org/dateCreated>" &&
                 $3 ~ /^"[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]"\^\^<http:\/\/www.w3.org\/2001\/XMLSchema#date>$/ &&
                 substr($3, 2, 4) + 0 < before)
            dated[$1] = 1
    } else if ($2 == "<https://personsincontext.org/model#hasRole>" &&
               $3 == "<https://terms.personsincontext.org/roles/575>") {
        child[$1] = 1
    } else if ($2 == "<https://schema.org/parent>") {
        parentOf[$3] = $1
    } else if ($2 == "<https://schema.org/additionalName>") {
        nameOf[$3] = $1
    }
    next
}
FNR == 1 {
    for (r in doop) if (r in dated) keep[r] = 1
    for (c in child) { r = c; sub(/_Person_.*/, ">", r); if (r in keep) person[c] = 1 }
    for (p in parentOf) if (parentOf[p] in person) parent[p] = 1
    for (p in parent) person[p] = 1
    for (b in nameOf) if (nameOf[b] in person) name[b] = 1
    n = 0; for (r in keep) n++
    printf "baptisms kept: %d\n", n > "/dev/stderr"
}
# Pass 2: write them out.
($1 in keep) {
    if ($2 == "<https://schema.org/dateCreated>") {
        print
        print $1 " <https://schema.org/additionalType> <https://terms.personsincontext.org/ThesaurusHistorischePersoonsgegevens/548> ."
        print $1 " <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://schema.org/ArchiveComponent> ."
    }
    next
}
($1 in person) {
    if ($2 == "<http://www.w3.org/ns/prov#hadPrimarySource>")
        print $1 " <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://personsincontext.org/model#PersonObservation> ."
    if ($2 != "<https://schema.org/name>") print
    next
}
($1 in name) { print }
' "$IN" "$IN" > "$OUT"
echo "triples written: $(wc -l < "$OUT") to $OUT"
