"""Exercise the real File Browser login, proxy headers and file API."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

spec=importlib.util.spec_from_file_location("services",sys.argv[1])
services=importlib.util.module_from_spec(spec);spec.loader.exec_module(services)
binary=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else Path("/usr/local/bin/filebrowser")
with tempfile.TemporaryDirectory(prefix="framekit-browser-test-") as temporary:
    base=Path(temporary);root=base/"workspace";root.mkdir()
    database=base/"private"/"filebrowser.db"
    services.initialize_browser(database,root,"admin","adminadmin12",binary)
    before=database.read_bytes()
    services.initialize_browser(database,root,"other","differentpassword12",binary)
    assert database.read_bytes()==before, "Restart overwrote the database"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0));port=sock.getsockname()[1]
    url=f"http://127.0.0.1:{port}"
    proxy={"Host":"test-8080.proxy.runpod.net","Origin":"https://test-8080.proxy.runpod.net",
           "X-Forwarded-Proto":"https","X-Forwarded-Host":"test-8080.proxy.runpod.net",
           "X-Forwarded-For":"203.0.113.7","Sec-Fetch-Site":"same-origin"}
    def request(path,data=None,method=None,token=None):
        headers=dict(proxy)
        if token:headers["X-Auth"]=token
        if path=="/api/login":headers["Content-Type"]="application/json"
        req=urllib.request.Request(url+path,data=data,headers=headers,method=method)
        try:
            with urllib.request.urlopen(req,timeout=5) as response:return response.status,response.read()
        except urllib.error.HTTPError as error:return error.code,error.read()
    with (base/"browser.log").open("wb") as log:
        child=subprocess.Popen(services.browser_command(database,port,"127.0.0.1",root,binary),stdout=log,stderr=log)
        try:
            for _ in range(100):
                if child.poll() is not None:raise RuntimeError("File Browser exited")
                try:
                    if request("/")[0]==200:break
                except (OSError,urllib.error.URLError):pass
                time.sleep(.1)
            else:raise RuntimeError("File Browser startup timed out")
            assert request("/api/resources/")[0] in (401,403)
            assert request("/api/login",json.dumps({"username":"admin","password":"wrongpassword12"}).encode())[0] in (401,403)
            status,body=request("/api/login",json.dumps({"username":"admin","password":"adminadmin12"}).encode())
            assert status==200,(status,body)
            token=body.decode().strip('"')
            assert request("/api/resources/",token=token)[0]==200
            payload=b"FRAMEKIT upload and download test"
            status,body=request("/api/resources/proxy-test.txt",payload,"POST",token)
            assert status in (200,201,204),(status,body)
            assert (root/"proxy-test.txt").read_bytes()==payload
            status,body=request("/api/raw/proxy-test.txt",token=token)
            assert status==200 and body==payload,(status,body)
            assert request("/api/raw/proxy-test.txt")[0] in (401,403)
            assert request("/api/resources/anonymous.txt",b"no", "POST")[0] in (401,403)
            assert not (root/"anonymous.txt").exists()
            assert b"adminadmin12" not in (base/"browser.log").read_bytes()
            print("File Browser smoke passed: default login, Runpod proxy upload/download, anonymous denial, database preserved")
        finally:
            child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait()
