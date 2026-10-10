"""Boot the shipped ComfyUI, inspect real Manager/UI routes, and restart on Linux."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error

comfy=Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='framekit-boot-') as tmp:
    root=Path(tmp);user=root/'user';user.mkdir();(user/'__manager').mkdir()
    (user/'__manager/config.ini').write_text('[default]\nuse_uv = False\nsecurity_level = normal\nnetwork_mode = offline\n',encoding='utf-8')
    marker=user/'keep-on-restart.txt';marker.write_text('keep')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    env=dict(os.environ)
    env.pop('__COMFY_CLI_SESSION__',None)
    with (root/'boot.log').open('w',encoding='utf-8') as log:
        child=subprocess.Popen([sys.executable,str(comfy/'main.py'),'--cpu','--listen','127.0.0.1',
            '--port',str(port),'--user-directory',str(user),'--enable-manager','--enable-manager-legacy-ui',
            '--disable-auto-launch','--disable-api-nodes'],cwd=comfy,env=env,stdout=log,stderr=log)
        def request(path,headers=None,data=None):
            req=urllib.request.Request(base+path,headers=headers or {},data=data)
            try:
                with urllib.request.urlopen(req,timeout=5) as response:return response.status,response.read()
            except urllib.error.HTTPError as error:return error.code,error.read()
        def ready():
            for _ in range(240):
                if child.poll() is not None:raise RuntimeError('ComfyUI exited during startup')
                try:
                    if request('/v2/manager/version')[0]==200:return
                except (OSError,urllib.error.URLError):pass
                time.sleep(.5)
            raise RuntimeError('Manager startup timed out')
        try:
            ready()
            assert request('/extensions/comfyui-manager-legacy/comfyui-manager.js')[0]==200
            info=json.loads(request('/object_info')[1])
            assert 'FRAMEKITSizes' in info and 'LoadImage' in info
            nav={'Host':'test-8188.proxy.runpod.net','Sec-Fetch-Site':'cross-site',
                 'Sec-Fetch-Mode':'navigate','Sec-Fetch-Dest':'document'}
            assert request('/',nav)[0]==200
            assert request('/object_info',nav)[0]==403
            if os.name=='posix':
                try:request('/v2/manager/reboot',{'Content-Type':'application/json'},b'{}')
                except (OSError,urllib.error.URLError):pass
                time.sleep(1)
                ready()
                assert marker.read_text()=='keep'
            print('Startup smoke passed: actual Manager UI, FRAMEKIT nodes, Console navigation and Linux restart')
        except Exception:
            log.flush();print((root/'boot.log').read_text(encoding='utf-8',errors='replace')[-9000:]);raise
        finally:
            child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait()
