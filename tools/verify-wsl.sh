#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
mkdir -p .verification
python3 -u tools/verify_site.py 2>&1 | tee .verification/wsl-verification.log