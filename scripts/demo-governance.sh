#!/usr/bin/env bash

echo
echo "=== DEMO 1: Approved API ==="
if ! python scripts/validate-governance.py tests/fixtures/catalogue-approved.json; then
  echo "ERROR: Approved API should have passed."
  exit 1
fi

echo
echo "=== DEMO 2: Pending approval ==="
if python scripts/validate-governance.py tests/fixtures/catalogue-pending.json; then
  echo "ERROR: Pending publication unexpectedly passed."
  exit 1
else
  echo "EXPECTED RESULT: Pending publication was rejected."
fi

echo
echo "=== DEMONSTRATION COMPLETE ==="
