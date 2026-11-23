"""Run as the notebook user in a private scratch mount namespace during bootstrap."""

from pathlib import Path
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

base = Path("/home/ec2-user/SageMaker/Assessment")
manager = KernelManager(
    kernel_name="e179-assessment",
    transport="ipc",
    connection_file="/run/e179/k/kernel-00000000-0000-0000-0000-000000000001.json",
    kernel_spec_manager=KernelSpecManager(
        kernel_dirs=["/opt/e179/kernels"], ensure_native_kernel=False
    ),
)
manager.start_kernel(cwd=str(base / "Task2"))
client = manager.blocking_client()
client.start_channels()
try:
    client.wait_for_ready(timeout=90)
    msg = client.execute("""from pathlib import Path
import socket
import sklearn, shap, lime
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
assert Path.cwd().name == 'Task2'
assert not Path('/etc/e179/account.json').exists()
assert not Path('/home/ec2-user/SageMaker/.e179').exists()
assert not Path('/opt/e179/agent.py').exists()
Path('probe.txt').write_text('ok')
try:
    Path('../References/probe.txt').write_text('x')
except OSError:
    pass
else:
    raise AssertionError('reference write succeeded')
try:
    socket.create_connection(('169.254.169.254', 80), 0.5).close()
except OSError:
    pass
else:
    raise AssertionError('instance metadata reachable')
""")
    while True:
        result = client.get_shell_msg(timeout=90)
        if result["parent_header"].get("msg_id") == msg:
            if result["content"].get("status") != "ok":
                raise RuntimeError("Kernel isolation or import probe failed")
            break
finally:
    client.stop_channels()
    manager.shutdown_kernel(now=True)
