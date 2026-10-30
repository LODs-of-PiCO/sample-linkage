#!/usr/bin/env bash
# Link ELO DTB records with burgerLinker's between_b_m.
#
# usage: scripts/run.sh <siblings|marriages> <input .nt/.ttl> <workdir> [extra burgerLinker options]
#
#   siblings   parents of a baptism -> parents of another baptism
#   marriages  parents of a baptism -> bride and groom of a marriage
#
# A new workdir gets a fresh RDF store built from the input. To rebuild
# the store of an existing workdir, delete the workdir first.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BL="$ROOT/bin/burgerlinker-v0.8.2"
JAR="$BL/burgerLinker.jar"

if [ $# -lt 3 ]; then
    echo "usage: $0 <siblings|marriages> <input .nt/.ttl> <workdir> [extra burgerLinker options]" >&2
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
        ;;
    marriages)
        MODEL="$ROOT/models/elo-dtb-marriages.yaml"
        RULESET="$BL/res/rule_sets/LINKS.yaml"
        ;;
    *)
        echo "unknown set-up '$SETUP': use siblings or marriages" >&2
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
    --function between_b_m \
    "$@"
