"""Root-only notebook checkpoint worker. The release and private state live on the notebook data volume."""

import contextlib
import hashlib
import io
import json
import logging
import os
import pwd
import re
import shutil
import stat
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

BASE = Path("/home/ec2-user/SageMaker")
PRIVATE = BASE / ".e179"
VIEW = BASE / "Assessment"
RELEASE = PRIVATE / "release/content"
STATE = PRIVATE / "state.json"
RUN = Path("/run/e179")
SERVICE = "jupyter-server.service"
CLIENTS = {"Cardinal": "Cardinal_Trust_Financial.md", "Anchorline": "Anchorline_Systems.md"}
MAX_BYTES = 32 * 1024**2
MAX_FILES = 128


class CheckError(Exception):
    """A message suitable for the learner."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def atomic(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as out:
        temp = Path(out.name)
        try:
            os.fchmod(out.fileno(), mode)
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
            os.replace(temp, path)
            fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            temp.unlink(missing_ok=True)


def command(*args):
    subprocess.run(args, check=True, stdin=subprocess.DEVNULL)


def account_user():
    account = pwd.getpwnam("ec2-user")
    return account.pw_uid, account.pw_gid


def initial_state():
    return {"version": 1, "stage": 0, "client": None, "session": None, "receipts": {}}


def state():
    return json.loads(STATE.read_bytes())


def put_state(s):
    atomic(STATE, canonical(s))


def read_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reset_cards():
    src = PRIVATE / "choices"
    src.mkdir(exist_ok=True)
    for obj in src.iterdir():
        if obj.is_symlink() or not obj.is_dir():
            obj.unlink()
        else:
            shutil.rmtree(obj)
    for name, filename in CLIENTS.items():
        atomic(src / filename, (RELEASE / name / "Selection.md").read_bytes(), 0o444)
    os.chown(src, 0, account_user()[1])
    src.chmod(0o775)


def bind(src, dst, readonly=False):
    dst.mkdir(exist_ok=True)
    command("mount", "--bind", str(src), str(dst))
    if readonly:
        command("mount", "-o", "remount,bind,ro,nosuid,nodev", str(dst))


def unmount_views():
    for name in ("Scenarios", "References", "Task1", "Task2", "Task3"):
        path = VIEW / name
        if os.path.ismount(path) or subprocess.run(["mountpoint", "-q", str(path)]).returncode == 0:
            command("umount", str(path))
        if path.exists():
            path.rmdir()


def make_work(n):
    work = PRIVATE / "work" / f"Task{n}"
    if not work.exists():
        tmp = work.with_name(work.name + ".new")
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        target = tmp / f"Task{n}.ipynb"
        shutil.copyfile(RELEASE / "common" / target.name, target)
        uid, gid = account_user()
        os.chown(target, uid, gid)
        os.chown(tmp, uid, gid)
        tmp.chmod(0o700)
        tmp.rename(work)
    return work


def project(s):
    """Recreate the view from trusted state; never repopulate an old or submitted notebook."""
    unmount_views()
    n = s["stage"]
    if n == 0:
        if not (PRIVATE / "choices").exists():
            reset_cards()
        bind(PRIVATE / "choices", VIEW / "Scenarios")
    else:
        client = s["client"]
        chosen = PRIVATE / "selected"
        chosen.mkdir(exist_ok=True)
        chosen.chmod(0o555)
        atomic(chosen / CLIENTS[client], (RELEASE / client / "Selection.md").read_bytes(), 0o444)
        bind(chosen, VIEW / "Scenarios", True)
        if n in (1, 2, 3):
            refs = PRIVATE / "views" / f"{client}-{n}"
            if not refs.exists():
                temp = refs.with_name(refs.name + ".new")
                if temp.exists():
                    shutil.rmtree(temp)
                temp.mkdir(parents=True)
                emitted = [(client, "Deployment.md")]
                if n == 1:
                    emitted += [("common", "Candidate_profiles.md")]
                if n == 2:
                    emitted += [
                        ("common", "Tool_syntax.md"),
                        (client, "Model_and_data.md"),
                        (client, "evaluation"),
                    ]
                if n == 3:
                    emitted += [(client, "Vendor.md"), ("common", "Framework_reference.md")]
                for track, item in emitted:
                    src = RELEASE / track / item
                    if src.is_dir():
                        shutil.copytree(src, temp / item)
                    else:
                        shutil.copyfile(src, temp / item)
                for entry in temp.rglob("*"):
                    entry.chmod(0o555 if entry.is_dir() else 0o444)
                temp.chmod(0o555)
                temp.rename(refs)
            bind(refs, VIEW / "References", True)
            bind(make_work(n), VIEW / f"Task{n}")
    status = (
        "Select one client in Scenarios. Delete the other selection card, then use the scenario check on the lab platform."
        if n == 0
        else "All three tasks are complete. Submit your downloaded reports to WGU GitLab."
        if n == 4
        else f"Task {n} is open. Use the platform instructions and the files in References."
    )
    atomic(VIEW / "STATUS.md", ("# Assessment status\n\n" + status + "\n").encode(), 0o444)
    atomic(RUN / "phase", str(n).encode(), 0o444)


def resume(s):
    project(s)
    command("systemctl", "start", SERVICE)
    command("/opt/e179/health.sh", str(s["stage"]))


@contextlib.contextmanager
def quiesce():
    atomic(RUN / "phase", b"-1", 0o444)
    command("systemctl", "stop", SERVICE)
    try:
        yield
    finally:
        resume(state())


def selected():
    src = PRIVATE / "choices"
    names = {p.name for p in src.iterdir() if p.name != ".ipynb_checkpoints"}
    if len(names) == 2 and names == set(CLIENTS.values()):
        raise CheckError(
            "Both clients are present. Delete the selection card for the client you will not use."
        )
    for key, filename in CLIENTS.items():
        p = src / filename
        if (
            names == {filename}
            and not p.is_symlink()
            and p.is_file()
            and read_hash(p) == read_hash(RELEASE / key / "Selection.md")
        ):
            return key
    reset_cards()
    raise CheckError(
        "The selection was empty or invalid. Both cards have been restored. Delete one and run the check again."
    )


def snapshot(n, include_bytes):
    root = PRIVATE / "work" / f"Task{n}"
    files = []
    buf = io.BytesIO()
    total = 0
    report = f"Task{n}.ipynb"

    def walk_failed(error):
        raise error

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=4) as archive:
        for parent, dirs, names in os.walk(root, followlinks=False, onerror=walk_failed):
            dirs.sort()
            if ".ipynb_checkpoints" in dirs:
                dirs.remove(".ipynb_checkpoints")
            for name in dirs:
                if (Path(parent) / name).is_symlink():
                    raise CheckError("Remove linked directories from the task folder and retry.")
            for name in sorted(names):
                p = Path(parent) / name
                rel = p.relative_to(root).as_posix()
                info = p.lstat()
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_nlink != 1
                    or len(rel.encode()) > 512
                    or any(ord(c) < 32 or c == "\\" for c in rel)
                ):
                    raise CheckError(
                        "The task contains a linked, special or unsupported filename. Use ordinary files and retry."
                    )
                total += info.st_size
                if total > MAX_BYTES or len(files) >= MAX_FILES:
                    raise CheckError(
                        "The task exceeds the checkpoint limit of 32 MiB or 128 files. Reduce large outputs and retry."
                    )
                data = p.read_bytes()
                if len(data) != info.st_size:
                    raise CheckError("The saved file size changed; save and retry.")
                if rel == report:
                    try:
                        note = json.loads(data)
                        assert note["nbformat"] == 4 and isinstance(note["cells"], list)
                    except (ValueError, AssertionError, KeyError, TypeError):
                        raise CheckError(
                            "The required task notebook is invalid. Save a valid notebook and retry."
                        ) from None
                files.append(
                    {"path": rel, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                )
                if include_bytes:
                    archive.writestr("files/" + rel, data)
        if report not in [x["path"] for x in files]:
            raise CheckError(f"Save {report} in the task folder before submitting.")
        files.sort(key=lambda f: f["path"])
        manifest = {"version": 1, "task": n, "files": files}
        if include_bytes:
            archive.writestr("manifest.json", canonical(manifest))
    return hashlib.sha256(canonical(manifest)).hexdigest(), buf.getvalue()


def handle(req, s3, bucket):
    sid, op, n = req.get("session"), req.get("op"), req.get("task")
    if not isinstance(sid, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", sid):
        raise CheckError("Invalid session identity.")
    if (
        type(n) is not int
        or n not in range(4)
        or (n == 0 and op != "select")
        or (n > 0 and op not in ("prepare", "commit"))
    ):
        raise CheckError("Invalid checkpoint request.")
    s = state()
    if s["session"] not in (None, sid):
        raise CheckError("This notebook is bound to a different lab session.")
    if n == 0:
        if s["stage"] == 0:
            with quiesce():
                s.update(session=sid, client=selected(), stage=1)
                put_state(s)
        return {"client": s["client"], "stage": s["stage"]}
    if str(n) in s["receipts"]:
        return {"accepted": s["receipts"][str(n)], "client": s["client"]}
    if s["stage"] != n:
        raise CheckError("This task is not open. Complete the preceding platform check first.")
    with quiesce():
        digest, archive = snapshot(n, op == "prepare")
        if op == "commit":
            if req.get("digest") != digest:
                raise CheckError(
                    "Your saved files changed during backup. Download the new version and run this check again."
                )
            s["receipts"][str(n)] = digest
            s["stage"] = n + 1
            put_state(s)
    if op == "prepare":
        s3.put_object(Bucket=bucket, Key=f"snap/{n}/{digest}.zip", Body=archive)
        return {"prepared": digest, "client": s["client"]}
    return {"accepted": digest, "client": s["client"]}


def missing(error):
    return error.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound")


def process(s3, bucket, key):
    leaf = key.removeprefix("req/")
    if not re.fullmatch(r"[0-9a-f]{32}\.json", leaf):
        return
    reply = "resp/" + leaf
    try:
        s3.head_object(Bucket=bucket, Key=reply)
    except ClientError as ex:
        if not missing(ex):
            raise
    else:
        s3.delete_object(Bucket=bucket, Key=key)
        return
    req = json.loads(s3.get_object(Bucket=bucket, Key=key)["Body"].read(8193))
    try:
        if req.get("expires", 0) < time.time():
            raise CheckError("The request expired. Run the same check again.")
        body = {"ok": True, **handle(req, s3, bucket)}
    except CheckError as ex:
        body = {"ok": False, "message": str(ex)}
    s3.put_object(Bucket=bucket, Key=reply, Body=canonical(body))
    s3.delete_object(Bucket=bucket, Key=key)


def main():
    logging.basicConfig(level=logging.INFO)
    conf = json.loads(Path("/etc/e179/account.json").read_bytes())
    s3 = boto3.client(
        "s3",
        region_name=conf["region"],
        config=Config(
            connect_timeout=4, read_timeout=15, retries={"max_attempts": 4, "mode": "standard"}
        ),
    )
    VIEW.mkdir(exist_ok=True)
    if not STATE.exists():
        # Only a genuinely empty installation may initialize progress.
        if (PRIVATE / "work").exists() or (PRIVATE / "selected").exists():
            raise RuntimeError("Missing progress journal; operator recovery required")
        put_state(initial_state())
    with quiesce():
        pass
    boto3.client("sagemaker", region_name=conf["region"]).add_tags(
        ResourceArn=conf["notebook"], Tags=[{"Key": "E179Access", "Value": "ready"}]
    )
    atomic(VIEW / "E179_SETUP_STATUS.txt", b"READY\n", 0o444)
    delay = 2
    while True:
        try:
            objects = s3.list_objects_v2(Bucket=conf["bucket"], Prefix="req/", MaxKeys=100).get(
                "Contents", []
            )
            for obj in objects:
                process(s3, conf["bucket"], obj["Key"])
            delay = 2
            time.sleep(2 if objects else 4)
        except (BotoCoreError, ClientError) as ex:
            # A transient mailbox failure must not recycle Jupyter or its running learner kernel.
            logging.warning(
                "Checkpoint storage unavailable (%s); retry in %ss", type(ex).__name__, delay
            )
            time.sleep(delay)
            delay = min(delay * 2, 30)


if __name__ == "__main__":
    main()
