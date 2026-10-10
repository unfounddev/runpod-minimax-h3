"""Install the pinned official Linux binary with a verified release digest."""
import hashlib
import io
from pathlib import Path
import tarfile
import urllib.request

VERSION = "2.63.23"
SHA256 = "b14db2bb8033caa3f80205eb6578b2ed0744ebd9e716b790bc4a9703ce909e88"
url = f"https://github.com/filebrowser/filebrowser/releases/download/v{VERSION}/linux-amd64-filebrowser.tar.gz"
with urllib.request.urlopen(url, timeout=120) as response:
    data = response.read()
if hashlib.sha256(data).hexdigest() != SHA256:
    raise RuntimeError("File Browser release checksum mismatch")
with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
    member = archive.getmember("filebrowser")
    if not member.isfile():
        raise RuntimeError("Unexpected File Browser archive")
    target = Path("/usr/local/bin/filebrowser")
    target.write_bytes(archive.extractfile(member).read())
    target.chmod(0o755)
