"""Verify access control and a real upload/download against the installed service."""
import importlib.util
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import base64

spec = importlib.util.spec_from_file_location("services", sys.argv[1])
services = importlib.util.module_from_spec(spec)
spec.loader.exec_module(services)
with tempfile.TemporaryDirectory(prefix="browser-smoke-") as tmp:
    directory = Path(tmp)
    root = directory / "workspace"
    root.mkdir()
    (root / "private-marker.txt").write_text("private-data", encoding="utf-8")
    password = secrets.token_urlsafe(24)
    config = directory / "browser.conf"
    config.write_text(services.browser_config(root, "tester", password), encoding="utf-8")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = dict(os.environ, XDG_CONFIG_HOME=str(directory / "settings"), APPDATA=str(directory))
    with (directory / "log.txt").open("w", encoding="utf-8") as log:
        child = subprocess.Popen(services.browser_command(config, port, "127.0.0.1"),
                                 env=env, stdout=log, stderr=log)
        base = f"http://127.0.0.1:{port}"
        auth = "Basic " + base64.b64encode(f"tester:{password}".encode()).decode()

        def request(path, data=None, authorized=False, extra_headers=None, method=None):
            headers = {"Authorization": auth} if authorized else {}
            headers.update(extra_headers or {})
            req = urllib.request.Request(base+path, data=data, headers=headers,
                                         method=method or ("PUT" if data is not None else "GET"))
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    return response.status, response.read()
            except urllib.error.HTTPError as error:
                return error.code, error.read()

        try:
            for _ in range(80):
                if child.poll() is not None:
                    raise RuntimeError("File manager failed to start; inspect the private test log")
                try:
                    status, body = request("/private-marker.txt")
                    break
                except (OSError, urllib.error.URLError):
                    time.sleep(0.25)
            else:
                raise RuntimeError("File manager startup timed out")
            assert status in (401, 403, 404) and b"private-data" not in body
            assert request("/private-marker.txt", authorized=True) == (200, b"private-data")
            status, body = request("/upload-test.safetensors", b"dummy-test-data", True)
            assert status in (200, 201, 204), (status, body.decode("utf-8", errors="replace").replace(password, "[redacted]"))
            assert request("/upload-test.safetensors", authorized=True) == (200, b"dummy-test-data")
            proxy = {"Host":"test-8080.proxy.runpod.net", "X-Forwarded-Host":"test-8080.proxy.runpod.net",
                     "X-Forwarded-Proto":"https", "X-Forwarded-For":"203.0.113.10",
                     "Origin":"https://test-8080.proxy.runpod.net", "Sec-Fetch-Site":"same-origin"}
            status, body=request('/proxied-upload.safetensors',b'proxy-test',True,proxy)
            assert status in (200,201,204),(status,body)
            assert request('/proxied-upload.safetensors',authorized=True,extra_headers=proxy)==(200,b'proxy-test')
            status,_=request('/blocked.safetensors',b'blocked',True,{**proxy,'Origin':'https://evil.example','Sec-Fetch-Site':'cross-site'})
            assert status==403, status
            boundary='framekit-smoke-boundary'
            fields={'act':'login','cppwd':password}
            data=''.join(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n' for key,value in fields.items())+f'--{boundary}--\r\n'
            status,body=request('/',data.encode(),False,{**proxy,'Content-Type':f'multipart/form-data; boundary={boundary}'},'POST')
            assert status in (200,302,303),(status,body.decode(errors='replace').replace(password,'[redacted]'))
            assert not (root / "browser.conf").exists()
            if hasattr(os, "symlink"):
                try:
                    (root / "escape").symlink_to(directory, target_is_directory=True)
                except OSError:
                    pass
                else:
                    status, body = request("/escape/browser.conf", authorized=True)
                    assert status != 200 and password.encode() not in body
        except Exception:
            log.flush()
            text = (directory / "log.txt").read_text(encoding="utf-8", errors="replace")
            print(text.replace(password, "[redacted]")[-6000:])
            raise
        finally:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    assert password not in (directory / "log.txt").read_text(encoding="utf-8", errors="replace")
print("File manager smoke passed: anonymous blocked, authenticated upload/download, credentials private")
