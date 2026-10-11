"""Run ComfyUI and an authenticated container file manager together."""
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time


DEFAULT_BROWSER_USERNAME = "admin"
DEFAULT_BROWSER_PASSWORD = "adminadmin12"


def browser_command(database, port=8080, address="0.0.0.0", root="/", binary="/usr/local/bin/filebrowser"):
    return [str(binary), "--database", str(database), "--root", str(root),
            "--address", address, "--port", str(port), "--disableExec"]


def initialize_browser(database, root, username, password, binary="/usr/local/bin/filebrowser"):
    """Create an account once; preserve users and changed passwords on restart."""
    database = Path(database)
    if database.exists():
        return
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", username):
        raise ValueError("Invalid FILE_BROWSER_USERNAME")
    if not 12 <= len(password) <= 128:
        raise ValueError("FILE_BROWSER_PASSWORD must have 12–128 characters")
    database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix="bootstrap-", dir=database.parent) as temporary:
        staging = Path(temporary) / "filebrowser.db"
        commands = [
            [str(binary), "--database", str(staging), "config", "init", "--root", str(root),
             "--address", "0.0.0.0", "--port", "8080", "--auth.method", "json", "--disableExec"],
            [str(binary), "--database", str(staging), "users", "add", username, password,
             "--perm.admin", "--perm.execute=false"],
        ]
        clean_env = dict(os.environ)
        clean_env.pop("FILE_BROWSER_PASSWORD", None)
        for command in commands:
            result = subprocess.run(command, env=clean_env, capture_output=True, timeout=30)
            if result.returncode:
                raise RuntimeError("File Browser account initialization failed")
        os.replace(staging, database)
        if os.name == "posix":
            database.chmod(0o600)


def main():
    Path("/workspace").mkdir(parents=True, exist_ok=True)
    root = Path("/")
    password = os.environ.get("FILE_BROWSER_PASSWORD", DEFAULT_BROWSER_PASSWORD)
    username = os.environ.get("FILE_BROWSER_USERNAME", DEFAULT_BROWSER_USERNAME)
    children = []
    stopping = False

    def stop(signum=None, frame=None):
        nonlocal stopping
        stopping = True
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    # Preserve the database and existing accounts across service restarts.
    database = Path("/var/lib/framekit-filebrowser/filebrowser.db")
    env = dict(os.environ)
    env.pop("FILE_BROWSER_PASSWORD", None)
    try:
        if os.environ.get("ENABLE_FILE_BROWSER", "1") == "1":
            initialize_browser(database, root, username, password)
            children.append(subprocess.Popen(browser_command(database, root=root), env=env,
                                             start_new_session=True))
            print(f"File Browser starting on HTTP port 8080; user: {username}", flush=True)
        else:
            print("File Browser disabled by ENABLE_FILE_BROWSER=0.", flush=True)
        children.append(subprocess.Popen(["bash", "/opt/template/startup.sh"], env=env,
                                         start_new_session=True))
        result = 0
        try:
            while not stopping:
                for child in children:
                    code = child.poll()
                    if code is not None:
                        result = code or (1 if child is not children[-1] else 0)
                        if child is not children[-1]:
                            print("File manager stopped unexpectedly; stopping the Pod services.", flush=True)
                        stop()
                        break
                time.sleep(0.25)
        finally:
            stop()
            for child in children:
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
        return result
    except Exception:
        stop()
        raise


if __name__ == "__main__":
    sys.exit(main())
