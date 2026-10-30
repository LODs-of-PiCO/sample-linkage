#!/usr/bin/env bash
# Link ELO DTB records with burgerLinker.
#
# usage: scripts/run.sh <set-up> <input .nt/.ttl> <workdir> [extra burgerLinker options]
#
#   siblings              parents of a baptism -> parents of another baptism (between_b_m)
#   marriages             parents of a baptism -> bride and groom of a marriage (between_b_m)
#   within-bm             baptised child -> bride or groom of a marriage (within_b_m),
#                         child gets both genders
#   within-bm-bloothooft  same, child's gender from Bloothooft's given-name list
#                         (the input must include data/given-name-gender.nt)
#
# A new workdir gets a fresh RDF store built from the input. To rebuild
# the store of an existing workdir, delete the workdir first.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BL="$ROOT/bin/burgerlinker-v0.8.2"
JAR="$BL/burgerLinker.jar"

if [ $# -lt 3 ]; then
    echo "usage: $0 <siblings|marriages|within-bm|within-bm-bloothooft> <input .nt/.ttl> <workdir> [extra burgerLinker options]" >&2
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
    *)
        echo "unknown set-up '$SETUP': use siblings, marriages, within-bm or within-bm-bloothooft" >&2
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
