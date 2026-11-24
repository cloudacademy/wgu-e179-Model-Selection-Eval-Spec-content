#!/bin/bash
set -Eeuo pipefail
test "$(cat /run/e179/phase)" = 2
view=/home/ec2-user/SageMaker/Assessment
[[ "$1" =~ ^/run/e179/k/kernel-[0-9a-fA-F-]+\.json$ ]]
/usr/bin/python3 -I - "$1" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
c=json.loads(p.read_bytes())
assert c["transport"]=="ipc" and str(c["ip"]).startswith("/run/e179/k/")
PY
# Only isolated Unix-domain sockets cross the kernel boundary. A kernel receives no host home, network, cloud credentials or system bus.
exec /usr/bin/bwrap --unshare-all --die-with-parent --new-session --cap-drop ALL --clearenv \
  --ro-bind /usr /usr --symlink usr/lib /lib --symlink usr/lib64 /lib64 --symlink usr/bin /bin \
  --ro-bind-try /etc/ld.so.cache /etc/ld.so.cache --ro-bind-try /etc/localtime /etc/localtime \
  --proc /proc --dev /dev --tmpfs /tmp --dir /tmp/home --dir /tmp/home/.cache \
  --ro-bind /opt/e179/runtime /opt/e179/runtime --bind /run/e179/k /run/e179/k \
  --bind "$view/Task2" "$view/Task2" --ro-bind "$view/References" "$view/References" --ro-bind "$view/Scenarios" "$view/Scenarios" \
  --setenv HOME /tmp/home --setenv PATH /opt/e179/runtime/venv/bin:/usr/bin --setenv MPLBACKEND Agg \
  --setenv PYTHONNOUSERSITE 1 --setenv OMP_NUM_THREADS 1 --setenv OPENBLAS_NUM_THREADS 1 --setenv NUMBA_NUM_THREADS 1 \
  --setenv NUMBA_CACHE_DIR /tmp/home/.cache --chdir "$view/Task2" \
  /opt/e179/runtime/venv/bin/python -I -m ipykernel_launcher -f "$1"
