"""Jupyter Server policy for the managed notebook. Only the Task 2 kernel may execute learner code."""

import json
import os
import pwd
import re
from pathlib import Path
from urllib.parse import unquote

from jupyter_client.kernelspec import KernelSpecManager
from jupyter_server.auth import Authorizer
from jupyter_server.base.handlers import APIHandler
from jupyter_server.services.contents.filemanager import AsyncFileContentsManager
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager
from tornado import web

VIEW = Path("/home/ec2-user/SageMaker/Assessment")
RUN = Path("/run/e179")
LEARNER = "ec2-user"
SPEC_DIR = Path("/opt/e179/kernels")
CARDS = {"Scenarios/Cardinal_Trust_Financial.md", "Scenarios/Anchorline_Systems.md"}


def phase():
    try:
        return int((RUN / "phase").read_text())
    except (OSError, ValueError):
        return -1


def clean(path):
    return not any(
        x in (".", "..") or "\\" in x or any(ord(v) < 32 for v in x) for x in path.split("/")
    )


def path_safe(path):
    if not clean(path):
        return False
    point = VIEW
    for segment in path.strip("/").split("/"):
        point = point / segment
        if point.is_symlink():
            return False
    return True


def writable(path, n):
    return n in (1, 2, 3) and path.startswith(f"Task{n}/") and clean(path)


class Contents(AsyncFileContentsManager):
    def _get_os_path(self, path):
        if not path_safe(path):
            raise web.HTTPError(403)
        return super()._get_os_path(path)

    async def rename_file(self, old_path, new_path):
        n = phase()
        if not (writable(old_path, n) and writable(new_path, n)):
            raise web.HTTPError(403)
        return await super().rename_file(old_path, new_path)


class Specs(KernelSpecManager):
    def __init__(self, **kwargs):
        super().__init__(
            kernel_dirs=[str(SPEC_DIR)],
            allowed_kernelspecs={"e179-assessment"},
            ensure_native_kernel=False,
            **kwargs,
        )


class Manager(AsyncMappingKernelManager):
    def __init__(self, **kwargs):
        kwargs["connection_dir"] = str(RUN / "k")
        super().__init__(**kwargs)

    async def start_kernel(self, *, kernel_id=None, path=None, **kwargs):
        if phase() != 2 or kwargs.get("kernel_name", "e179-assessment") != "e179-assessment":
            raise web.HTTPError(403)
        return await super().start_kernel(kernel_id=kernel_id, path=path, **kwargs)


class Gate(Authorizer):
    def is_authorized(self, handler, user, action, resource):
        if resource in {"terminals", "nbconvert"}:
            return False
        if action in {"write", "execute"} and resource in {"kernels", "sessions"}:
            return phase() == 2
        return True


class Denied(web.RequestHandler):
    def prepare(self):
        raise web.HTTPError(403)


class NoKernels(APIHandler):
    @web.authenticated
    def get(self):
        self.finish({"default": "", "kernelspecs": {}})


class Health(APIHandler):
    @web.authenticated
    def get(self):
        app = self.settings
        actual = Path(self.contents_manager.root_dir).resolve()
        ok = (
            os.geteuid() == pwd.getpwnam(LEARNER).pw_uid
            and actual == VIEW
            and isinstance(self.authorizer, Gate)
            and isinstance(self.contents_manager, Contents)
            and isinstance(self.kernel_manager, Manager)
            and isinstance(self.kernel_spec_manager, Specs)
            and set(self.kernel_spec_manager.find_kernel_specs()) == {"e179-assessment"}
            and self.kernel_spec_manager.get_kernel_spec("e179-assessment").argv
            == ["/opt/e179/kernel.sh", "{connection_file}"]
            and not app.get("terminals_available", False)
        )
        self.finish({"guard": bool(ok), "phase": phase(), "version": 1})


def permits(method, path, n):
    path = unquote(path).strip("/")
    if not clean(path) or "%" in path:
        return False
    read = method in ("GET", "HEAD")
    if path == "e179/health":
        return read
    if n < 0:
        return False
    if not path or path in {
        "lab",
        "tree",
        "api",
        "api/status",
        "api/me",
        "api/spec.yaml",
        "api/kernelspecs",
        "favicon.ico",
    }:
        return read
    if path == "api/contents" or path.startswith("api/contents/"):
        rel = path[len("api/contents") :].strip("/")
        if not path_safe(rel):
            return False
        if read:
            return True
        if n == 0:
            return method == "DELETE" and rel in CARDS
        # POST creates a document within the named directory; PATCH/PUT/DELETE address the document.
        if method == "POST" and rel == f"Task{n}" and n in (1, 2, 3):
            return True
        return writable(rel, n)
    if path.startswith("files/"):
        return read and path_safe(path[6:])
    if re.fullmatch(r"api/(sessions|kernels)(/.*)?", path):
        return read if n != 2 else True
    if path.startswith("api/kernelspecs/") or path.startswith("kernelspecs/"):
        return read
    if path.startswith("lab/api/workspaces"):
        return read or method in {"PUT", "DELETE"}
    if path.startswith(
        (
            "lab/tree/",
            "lab/workspaces/",
            "lab/api/settings",
            "lab/api/themes",
            "lab/api/translations",
            "lab/api/listings",
            "static/",
            "lab/static/",
            "custom/",
            "api/config/",
            "lab/extensions/",
        )
    ):
        return read
    return False


def _load_jupyter_server_extension(serverapp):
    app = serverapp.web_app
    base = app.settings["base_url"].rstrip("/")
    app.add_handlers(".*$", [(base + "/e179/health", Health)])
    previous = app.find_handler

    def find(request, **kwargs):
        path = request.path
        if request.method == "GET" and path == base + "/api/kernelspecs" and phase() != 2:
            return app.get_handler_delegate(request, NoKernels)
        if (not base or path == base or path.startswith(base + "/")) and permits(
            request.method, path[len(base) :], phase()
        ):
            return previous(request, **kwargs)
        return app.get_handler_delegate(request, Denied)

    app.find_handler = find


def _jupyter_server_extension_points():
    return [{"module": "e179_guard"}]
