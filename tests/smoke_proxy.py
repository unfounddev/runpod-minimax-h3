"""Exercise the patched ComfyUI middleware without a GPU or inference."""
import ast
import asyncio
import ipaddress
from pathlib import Path
import socket
import sys
import urllib.parse
import logging
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

source = ast.parse((Path(sys.argv[1])/'server.py').read_text(encoding='utf-8'))
functions = [node for node in source.body if isinstance(node, ast.FunctionDef)
             and node.name in ('is_loopback', 'create_origin_only_middleware')]
scope = dict(web=web, ipaddress=ipaddress, socket=socket, urllib=urllib, logging=logging)
exec(compile(ast.Module(body=functions,type_ignores=[]),'<actual ComfyUI middleware>','exec'),scope)
middleware = scope['create_origin_only_middleware']()
async def handler(request):
    return web.Response(text='ok')
async def check(method,path,headers,want):
    response=await middleware(make_mocked_request(method,path,headers=headers),handler)
    assert response.status==want,(method,path,response.status,want)
async def main():
    nav={'Host':'test-8188.proxy.runpod.net','Sec-Fetch-Site':'cross-site',
         'Sec-Fetch-Mode':'navigate','Sec-Fetch-Dest':'document'}
    await check('GET','/',nav,200)
    await check('POST','/',nav,403)
    await check('GET','/prompt',nav,403)
    await check('POST','/v2/manager/reboot',nav,403)
    await check('GET','/',{**nav,'Sec-Fetch-Mode':'cors'},403)
    await check('GET','/',{**nav,'Host':'evil.example'},403)
    await check('GET','/',{'Host':nav['Host'],'Sec-Fetch-Site':'same-origin'},200)
    await check('POST','/prompt',{'Host':'127.0.0.1','Origin':'https://evil.example'},403)
asyncio.run(main())
import importlib.metadata
assert importlib.metadata.version('comfyui-manager') == '4.2.2'
print('Proxy smoke passed: Runpod root navigation allowed; cross-site APIs and writes blocked; Manager installed')
