"""Permit only the Runpod Console's initial document navigation, preserving CSRF checks."""
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "server.py"
source = path.read_text(encoding="utf-8")
old = "            if sec_fetch_site == 'cross-site':\n                return web.Response(status=403)"
new = '''            # A Console link is a cross-site navigation. Only permit the root
            # document; cross-site APIs, writes and WebSockets retain the guard.
            runpod_navigation = (
                request.method == "GET" and request.path == "/"
                and request.headers.get("Sec-Fetch-Mode") == "navigate"
                and request.headers.get("Sec-Fetch-Dest") == "document"
                and (urllib.parse.urlsplit("//" + request.headers.get("Host", "")).hostname or "").endswith(".proxy.runpod.net")
            )
            if sec_fetch_site == 'cross-site' and not runpod_navigation:
                return web.Response(status=403)'''
if source.count(old) != 1:
    raise RuntimeError("ComfyUI origin middleware changed; review the proxy patch before building")
path.write_text(source.replace(old, new), encoding="utf-8")
