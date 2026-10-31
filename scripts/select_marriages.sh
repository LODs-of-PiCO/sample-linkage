#!/usr/bin/env bash
# Make the ELO DTB marriage set for burgerLinker: every marriage record
# (ondertrouw and/or huwelijk) with a usable date before a given year, with
# its bride and groom.
#
# usage: scripts/select_marriages.sh <elo-pico.nt.gz> <dtb_trouwen.nt.gz> <out.nt> [before-year, default 1811]
#
# The full ELO dump has the names, but its marriage records have no record
# type and no date field (the date is only in the description text).
# dtb_trouwen.nt.gz adds both: sdo:additionalType sourcetypes/549 and an
# ondertrouw event (eventtypes/99) and/or a marriage event (eventtypes/83)
# with picom:eventDate.
#
# Date: the marriage date when there is one, otherwise the ondertrouw date.
# The dates are plain strings ("1674-03-27"@nl); some have text in front
# ("Pro Deo\n1694-08-06"), in which case the date at the end is taken.
# Dates that are only a year or year-month, or that do not exist
# (1715-09-31), are left out: burgerLinker cannot read them.
#
# Written per record: sdo:additionalType sourcetypes/549, sdo:dateCreated as
# xsd:date and rdf:type sdo:ArchiveComponent. Per bride and groom (role 574):
# rdf:type, prov:hadPrimarySource, picom:hasRole, sdo:gender, sdo:givenName,
# sdo:familyName, sdo:additionalName, sdo:spouse, and their name blank nodes
# (pnv:patronym, pnv:baseSurname, pnv:surnamePrefix).

set -euo pipefail

if [ $# -lt 3 ] || [ $# -gt 4 ]; then
    echo "usage: $0 <elo-pico.nt.gz> <dtb_trouwen.nt.gz> <out.nt> [before-year, default 1811]" >&2
    exit 1
fi
DUMP="$1"
TROUWEN="$2"
OUT="$3"
BEFORE="${4:-1811}"
DATES="$(mktemp)"
PERSONS="$(mktemp)"
trap 'rm -f "$DATES" "$PERSONS"' EXIT

# Pass 1 (dtb_trouwen): one date per record.
zcat "$TROUWEN" | awk -v before="$BEFORE" '
function valid(d,   y, m, n) {
    y = substr(d, 1, 4) + 0; m = substr(d, 6, 2) + 0; n = substr(d, 9, 2) + 0
    if (m < 1 || m > 12 || n < 1) return 0
    if (m == 2) return n <= ((y % 4 == 0 && (y % 100 != 0 || y % 400 == 0)) ? 29 : 28)
    return n <= ((m == 4 || m == 6 || m == 9 || m == 11) ? 30 : 31)
}
$2 == "<https://personsincontext.org/model#eventDate>" {
    rec = $1; kind = ($1 ~ /_huwelijk_event>$/) ? "h" : "o"
    sub(/_[a-z]+_event>$/, ">", rec)
    v = $0; sub(/"@nl \.$/, "", v)
    if (match(v, /[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$/)) {
        d = substr(v, RSTART, 10)
        if (valid(d)) date[rec, kind] = d; else bad++
    }
    seen[rec] = 1
}
END {
    for (r in seen) {
        d = ((r, "h") in date) ? date[r, "h"] : (((r, "o") in date) ? date[r, "o"] : "")
        if (d == "") nodate++
        else if (substr(d, 1, 4) + 0 < before) { print r, d; kept++ }
        else late++
    }
    printf "marriage records: %d kept, %d dated %d or later, %d without a usable date (%d dates that do not exist)\n", kept, late, before, nodate, bad > "/dev/stderr"
}' > "$DATES"

# Pass 2 (dump): brides and grooms of those records and their name nodes.
zcat "$DUMP" | awk -v dates="$DATES" '
BEGIN { while ((getline line < dates) > 0) { split(line, a, " "); keep[a[1]] = 1 } }
index($1, "_Person_") {
    rec = $1; sub(/_Person_.*/, ">", rec)
    if (!(rec in keep)) next
    if ($2 == "<https://personsincontext.org/model#hasRole>" && $3 == "<https://terms.personsincontext.org/roles/574>") spouse[$1] = 1
    else if ($2 == "<https://schema.org/additionalName>") node[$1] = $3
}
END {
    for (p in spouse) { print p; if (p in node) print node[p]; n++ }
    printf "brides and grooms: %d\n", n > "/dev/stderr"
}' > "$PERSONS"

# Pass 3 (dump): write the records, persons and name nodes.
zcat "$DUMP" | awk -v dates="$DATES" -v persons="$PERSONS" '
BEGIN {
    while ((getline line < dates) > 0) { split(line, a, " "); date[a[1]] = a[2] }
    while ((getline p < persons) > 0) keep[p] = 1
    split("type hadPrimarySource hasRole gender givenName familyName additionalName spouse", a, " ")
    for (i in a) pred[a[i]] = 1
    split("patronym baseSurname surnamePrefix", a, " ")
    for (i in a) part[a[i]] = 1
    for (r in date) {
        print r " <https://schema.org/additionalType> <https://terms.personsincontext.org/sourcetypes/549> ."
        print r " <https://schema.org/dateCreated> \"" date[r] "\"^^<http://www.w3.org/2001/XMLSchema#date> ."
        print r " <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://schema.org/ArchiveComponent> ."
    }
}
($1 in keep) {
    p = $2; sub(/^<.*[#\/]/, "", p); sub(/>$/, "", p)
    if ((substr($1, 1, 2) == "_:") ? (p in part) : (p in pred)) print
}' > "$OUT"
echo "triples written: $(wc -l < "$OUT") to $OUT"
