#!/usr/bin/env bash
# Link ELO DTB records with burgerLinker.
#
# usage: scripts/run.sh <set-up> <input .nt/.ttl> <workdir> [extra burgerLinker options]
#
#   siblings              parents of a baptism -> parents of another baptism (between_b_m)
#   siblings-bloot        same, with the parents' given names from sdo:givenNameBloot
#                         (the input must be made with scripts/standardise_given_names.py)
#   marriages             parents of a baptism -> bride and groom of a marriage (between_b_m)
#   within-bm             baptised child -> bride or groom of a marriage (within_b_m),
#                         child gets both genders
#   within-bm-bloothooft  same, child's gender from Bloothooft's given-name list
#                         (the input must include data/given-name-gender.nt)
#   siblings-familyname   full ELO baptisms: parents -> parents, surname = family name
#   siblings-patronym     full ELO baptisms: parents -> parents, surname = patronym
#   siblings-familyname-std, siblings-patronym-std
#                         same, with standardised given names (the input must be
#                         made with scripts/standardise_given_names.py)
#   marriages-familyname-std, marriages-patronym-std
#                         full ELO baptisms -> ELO DTB marriages: parents -> bride and
#                         groom, standardised given names, surname = family name or
#                         patronym (input: select_baptisms.sh plus select_marriages.sh
#                         output, both through standardise_given_names.py)
#
# A new workdir gets a fresh RDF store built from the input. To rebuild
# the store of an existing workdir, delete the workdir first.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BL="$ROOT/bin/burgerlinker-v0.8.2"
JAR="$BL/burgerLinker.jar"

if [ $# -lt 3 ]; then
    echo "usage: $0 <set-up> <input .nt/.ttl> <workdir> [extra burgerLinker options]" >&2
    exit 1
fi
SETUP="$1"
INPUT="$(realpath "$2")"
WORKDIR="$3"
shift 3

case "$SETUP" in
    siblings)
        MODEL="$ROOT/models/elo-dtb-siblings.yaml"
        RULESET="$ROOT/rules/siblings.yaml"
        FUNCTION=between_b_m
        ;;
    siblings-bloot)
        MODEL="$ROOT/models/elo-dtb-siblings-bloot.yaml"
        RULESET="$ROOT/rules/siblings.yaml"
        FUNCTION=between_b_m
        ;;
    marriages)
        MODEL="$ROOT/models/elo-dtb-marriages.yaml"
        RULESET="$BL/res/rule_sets/LINKS.yaml"
        FUNCTION=between_b_m
        ;;
    within-bm)
        MODEL="$ROOT/models/elo-dtb-within-bm.yaml"
        RULESET="$BL/res/rule_sets/LINKS.yaml"
        FUNCTION=within_b_m
        ;;
    within-bm-bloothooft)
        MODEL="$ROOT/models/elo-dtb-within-bm-bloothooft.yaml"
        RULESET="$BL/res/rule_sets/LINKS.yaml"
        FUNCTION=within_b_m
        ;;
    siblings-familyname)
        MODEL="$ROOT/models/elo-baptisms-familyname.yaml"
        RULESET="$ROOT/rules/siblings.yaml"
        FUNCTION=between_b_m
        ;;
    siblings-patronym)
        MODEL="$ROOT/models/elo-baptisms-patronym.yaml"
        RULESET="$ROOT/rules/siblings.yaml"
        FUNCTION=between_b_m
        ;;
    siblings-familyname-std)
        MODEL="$ROOT/models/elo-baptisms-familyname-std.yaml"
        RULESET="$ROOT/rules/siblings.yaml"
        FUNCTION=between_b_m
        ;;
    siblings-patronym-std)
        MODEL="$ROOT/models/elo-baptisms-patronym-std.yaml"
        RULESET="$ROOT/rules/siblings.yaml"
        FUNCTION=between_b_m
        ;;
    marriages-familyname-std)
        MODEL="$ROOT/models/elo-baptisms-marriages-familyname-std.yaml"
        RULESET="$BL/res/rule_sets/LINKS.yaml"
        FUNCTION=between_b_m
        ;;
    marriages-patronym-std)
        MODEL="$ROOT/models/elo-baptisms-marriages-patronym-std.yaml"
        RULESET="$BL/res/rule_sets/LINKS.yaml"
        FUNCTION=between_b_m
        ;;
    *)
        echo "unknown set-up '$SETUP': use siblings, siblings-bloot, marriages, within-bm, within-bm-bloothooft, siblings-familyname, siblings-patronym or their -std variants, marriages-familyname-std, marriages-patronym-std" >&2
        exit 1
        ;;
esac

if [ ! -f "$JAR" ]; then
    echo "burgerLinker jar not found at $JAR (see README)" >&2
    exit 1
fi

INPUT_OPT=()
if [ ! -d "$WORKDIR/store" ]; then
    INPUT_OPT=(--input "$INPUT")
fi

java -jar "$JAR" \
    "${INPUT_OPT[@]}" \
    --workdir "$WORKDIR" \
    --model "$MODEL" \
    --ruleset "$RULESET" \
    --function "$FUNCTION" \
    "$@"
