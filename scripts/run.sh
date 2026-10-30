#!/usr/bin/env bash
# Link siblings in ELO DTB baptisms with burgerLinker.
#
# usage: scripts/run.sh <input .nt/.ttl> <workdir> [extra burgerLinker options]
#
# A new workdir gets a fresh RDF store built from the input. To rebuild
# the store of an existing workdir, delete the workdir first.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
JAR="$ROOT/bin/burgerlinker-v0.8.2/burgerLinker.jar"

if [ $# -lt 2 ]; then
    echo "usage: $0 <input .nt/.ttl> <workdir> [extra burgerLinker options]" >&2
    exit 1
fi
INPUT="$(realpath "$1")"
WORKDIR="$2"
shift 2

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
    --model "$ROOT/models/elo-dtb-siblings.yaml" \
    --ruleset "$ROOT/rules/siblings.yaml" \
    --function between_b_m \
    "$@"
