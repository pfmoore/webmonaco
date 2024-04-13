import io
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

API_URL = "https://api.github.com/repos/pfmoore/builder-monaco/releases"
TARGET = Path("app/bin")

if len(sys.argv) < 2:
    raise SystemExit("Must provide a tag name")
tag = sys.argv[1]
print(f"Getting Monaco version {tag}")

with urlopen(Request(API_URL, headers={"Accept": "application/vnd.github+json"})) as f:
    data = json.load(f)

for r in data:
    if r["tag_name"] != tag:
        continue
    for asset in r["assets"]:
        name = asset["name"]
        print(name)
        with urlopen(asset["browser_download_url"]) as a:
            content = io.BytesIO(a.read())
        z = ZipFile(content)
        print(z.namelist())
        if name.startswith("monaco-windows"):
            (TARGET / "win32/monaco.exe").write_bytes(z.read("monaco.exe"))
        if name.startswith("monaco-linux"):
            (TARGET / "linux/monaco").write_bytes(z.read("monaco"))
