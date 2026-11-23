import sys

sys.path.insert(0, "/opt/e179/site")
from e179_guard import Gate, Contents, Manager, Specs

c = get_config()
c.ServerApp.root_dir = "/home/ec2-user/SageMaker/Assessment"
c.ServerApp.default_url = "/lab"
c.ServerApp.authorizer_class = Gate
c.ServerApp.contents_manager_class = Contents
c.ServerApp.kernel_manager_class = Manager
c.ServerApp.kernel_spec_manager_class = Specs
c.ServerApp.terminals_enabled = False
c.ServerApp.allow_external_kernels = False
c.ServerApp.jpserver_extensions.update(
    {
        "e179_guard": True,
        "jupyter_server_terminals": False,
        "jupyter_server_proxy": False,
        "jupyterlab_git": False,
    }
)
c.ServerApp.tornado_settings.update({"headers": {"Cache-Control": "no-store"}})
c.FileContentsManager.delete_to_trash = False
c.FileContentsManager.always_delete_dir = False
c.MappingKernelManager.default_kernel_name = "e179-assessment"
c.KernelManager.transport = "ipc"
c.LabApp.custom_css = True
