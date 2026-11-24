#!/bin/bash
set -eu
root=/home/ec2-user/SageMaker
# A written task has no kernel connections. A recent saved edit or a checkpoint keeps the instance awake.
if ! test -f "$root/Assessment/E179_SETUP_STATUS.txt"; then exit 0; fi
if find "$root/.e179/work" "$root/.e179/state.json" -type f -mmin -30 -print -quit 2>/dev/null | grep -q .; then exit 0; fi
if [[ "$(cat /run/e179/phase)" == "-1" ]]; then exit 0; fi
exec /opt/e179/runtime/venv/bin/python -I /opt/e179/autostop.py --time 1800 --strategy connections
