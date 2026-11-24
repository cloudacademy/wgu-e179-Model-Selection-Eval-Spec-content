#!/bin/bash
set -Eeuo pipefail
umask 022
base=/home/ec2-user/SageMaker
private=$base/.e179
control=$private/release/control
view=$base/Assessment
run=/opt/e179/runtime
stage=/run/e179
install -d -m 0755 /opt/e179 "$view" "$stage" "$run" "$base/.e179-runtime"
chown root:root "$base" "$view" "$base/.e179-runtime"
chmod 0755 "$base" "$view"
if ! mountpoint -q "$run"; then mount --bind "$base/.e179-runtime" "$run"; fi
if ! test -x /usr/bin/python3.12 || ! test -x /usr/bin/bwrap || ! command -v crontab >/dev/null; then
  dnf -y install python3.12 python3.12-pip bubblewrap cronie
fi
lock=$(sha256sum "$control/requirements.lock.txt" | cut -d' ' -f1)
if ! test -f "$run/.installed-$lock"; then
  /usr/bin/python3.12 -m venv "$run/venv"
  "$run/venv/bin/python" -I -m pip install --disable-pip-version-check -r "$control/requirements.lock.txt"
  "$run/venv/bin/python" -I -m pip check
  touch "$run/.installed-$lock"
fi
install -d -m 0755 /opt/e179/site /opt/e179/config/custom /opt/e179/kernels/e179-assessment
install -m 0755 "$control/"{kernel,health,autostop}.sh /opt/e179/
install -m 0644 "$control/"{agent,autostop,probe_kernel}.py /opt/e179/
install -m 0644 "$control/e179_guard.py" /opt/e179/site/
install -m 0644 "$control/jupyter_server_config.py" /opt/e179/config/
# Disable Git in the managed JupyterLab environment serving the student UI.
lab_prefix=/home/ec2-user/anaconda3/envs/JupyterSystemEnv
"$lab_prefix/bin/jupyter-labextension" disable --level=sys-prefix @jupyterlab/git
install -m 0644 "$control/custom.css" /opt/e179/config/custom/
# LabApp serves custom CSS from its effective config directory on managed images.
install -d -m 0755 /home/ec2-user/.jupyter/custom
install -m 0644 "$control/custom.css" /home/ec2-user/.jupyter/custom/custom.css
# Managed images can start Lab with an explicit config file. Append our root-owned subconfig
# to any such native configuration without replacing its TLS or SageMaker authentication settings.
for name in jupyter_server_config.py jupyter_lab_config.py jupyter_notebook_config.py; do
  native="/home/ec2-user/.jupyter/$name"
  if ! grep -Fqx 'load_subconfig("/opt/e179/config/jupyter_server_config.py")' "$native" 2>/dev/null; then
    printf '\n# E179 assessment workspace\n%s\n' 'load_subconfig("/opt/e179/config/jupyter_server_config.py")' >>"$native"
    chmod a+r "$native"
  fi
done
cat >/opt/e179/kernels/e179-assessment/kernel.json <<'JSON'
{"argv":["/opt/e179/kernel.sh","{connection_file}"],"display_name":"E179 Assessment (CPU)","language":"python","metadata":{"debugger":false}}
JSON
install -d -m 0700 -o ec2-user -g "$(id -gn ec2-user)" "$stage/k"
# Exercise a real kernel, with the same launcher and paths, without showing any genuine task to the browser.
unshare --mount --propagation private /bin/bash -se <<'PROBE'
mount -t tmpfs tmpfs /run/e179
mount -t tmpfs tmpfs /home/ec2-user/SageMaker/Assessment
install -d -m 0700 -o ec2-user -g "$(id -gn ec2-user)" /run/e179/k
printf 2 >/run/e179/phase
cd /home/ec2-user/SageMaker/Assessment
install -d -m 0755 References Scenarios
install -d -m 0700 -o ec2-user -g "$(id -gn ec2-user)" Task2
runuser -u ec2-user -- /opt/e179/runtime/venv/bin/python -I /opt/e179/probe_kernel.py
PROBE
cat >/etc/systemd/system/jupyter-server.service.d/20-e179.conf <<'UNIT'
[Service]
Environment="JUPYTER_CONFIG_PATH=/opt/e179/config"
Environment="PYTHONPATH=/opt/e179/site"
KillMode=control-group
TimeoutStopSec=10
SendSIGKILL=yes
NoNewPrivileges=yes
UNIT
cat >/etc/systemd/system/e179-agent.service <<'UNIT'
[Unit]
Description=E179 notebook checkpoint worker
After=network-online.target
[Service]
Type=simple
ExecStart=/opt/e179/runtime/venv/bin/python -I /opt/e179/agent.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT
# Data volume is mounted by SageMaker on each start; the lifecycle controls startup of both services.
systemctl daemon-reload
touch "$stage/server-enabled"
systemctl start e179-agent.service
cat >/etc/cron.d/e179-autostop <<'CRON'
*/10 * * * * root /opt/e179/autostop.sh >> /var/log/e179-autostop.log 2>&1
CRON
chmod 0644 /etc/cron.d/e179-autostop
systemctl start crond
