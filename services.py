"""Run ComfyUI and an authenticated workspace file manager together."""
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time


def browser_config(root, username, password):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", username):
        raise ValueError("FILE_BROWSER_USERNAME must use letters, numbers, underscores or hyphens")
    if not re.fullmatch(r"[A-Za-z0-9!@$_.+-]{12,128}", password):
        raise ValueError("FILE_BROWSER_PASSWORD needs 12–128 characters: letters, numbers or !@$_.+-")
    if "\n" in str(root) or "\r" in str(root):
        raise ValueError("Invalid workspace path")
    return f"[accounts]\n  {username}: {password}\n\n[/]\n  {root}\n  accs:\n    rwmd: {username}\n"


def browser_command(config, port=8080, address="0.0.0.0"):
    return [sys.executable, "-m", "copyparty", "-c", str(config), "-i", address,
            "-p", str(port), "--http-only", "--xvol", "--no-robots",
            "--no-html", "--no-readme", "--no-logues", "--no-reload",
            "--no-voldump", "--no-thumb", "--no-mtag-ff", "--no-dav", "--unpost", "0"]


def main():
    root = Path("/workspace")
    root.mkdir(parents=True, exist_ok=True)
    password = os.environ.get("FILE_BROWSER_PASSWORD", "")
    username = os.environ.get("FILE_BROWSER_USERNAME", "admin")
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
    with tempfile.TemporaryDirectory(prefix="nexus-services-") as directory:
        env = dict(os.environ)
        env.pop("FILE_BROWSER_PASSWORD", None)
        # Private credentials and service configuration stay outside the served folder.
        env["XDG_CONFIG_HOME"] = directory
        if os.environ.get("ENABLE_FILE_BROWSER", "1") == "1" and password:
            config = Path(directory) / "browser.conf"
            content = browser_config(root, username, password)
            config.write_text(content, encoding="utf-8")
            config.chmod(0o600)
            children.append(subprocess.Popen(browser_command(config), env=env,
                                             start_new_session=True))
            print(f"File manager starting on HTTP port 8080; user: {username}", flush=True)
        else:
            print("File manager disabled. Set FILE_BROWSER_PASSWORD to enable port 8080.", flush=True)
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


if __name__ == "__main__":
    sys.exit(main())
