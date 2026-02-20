#!/usr/bin/env bash
# Convenience wrapper: seed from claw_manuals index (testing/demo).
# Requires PDFs to exist under claw_manuals/root/claw_manuals/ (or set SEED_BASE_PATH).
#
# Usage:
#   ./scripts/seed_claw_manuals.sh
#   ./scripts/seed_claw_manuals.sh --dry-run
#   ./scripts/seed_claw_manuals.sh --limit 5

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

export SEED_INDEX_PATH="${SEED_INDEX_PATH:-$ROOT/claw_manuals/root/claw_manuals/manual_index.json}"
export SEED_BASE_PATH="${SEED_BASE_PATH:-$ROOT/claw_manuals/root/claw_manuals}"
export SEED_TENANT_SLUG="${SEED_TENANT_SLUG:-claw-demo}"
export SEED_TENANT_NAME="${SEED_TENANT_NAME:-Claw manuals demo}"

exec python scripts/seed_from_index.py "$@"
