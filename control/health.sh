#!/bin/bash
set -eu
for n in $(seq 1 45); do
  if curl -kfSs --max-time 3 https://localhost:8443/e179/health 2>/dev/null |
    /usr/bin/python3 -I -c 'import json,sys; x=json.load(sys.stdin); assert x["guard"] is True and x["phase"]==int(sys.argv[1])' "$1" 2>/dev/null; then
    exit 0
  fi
  sleep 1
done
echo "The SageMaker Jupyter guard did not attest to the expected phase." >&2
exit 1
