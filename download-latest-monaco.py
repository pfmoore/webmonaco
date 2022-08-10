import io
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile


def get_urls():
    with urlopen("https://api.github.com/repos/pfmoore/builder-monaco/releases/latest") as f:
        latest = json.load(f)
    latest_version = None
    urls = {}

    for asset in latest["assets"]:
        name = asset["name"]
        url = asset["browser_download_url"]
        if not name.endswith(".zip"):
            continue
        parts = name[:-4].split("-")
        assert len(parts) == 3, f"Invalid name {name}"
        monaco, platform, version = parts
        assert monaco == "monaco", f"Invalid name {name}"
        if latest_version is None:
            latest_version = version
        else:
            assert version == latest_version, f"Found unexpected version {version} (expected {latest_version})"
        urls[platform] = url

    return latest_version, urls

def get_zip_item(url, name):
    with urlopen(url) as f:
        zip_data = f.read()
    with ZipFile(io.BytesIO(zip_data)) as z:
        return z.read(name)

if __name__ == "__main__":
    version, urls = get_urls()
    print(f"Found version {version}")
    binaries = {
        "webmonaco/bin/linux/monaco": get_zip_item(urls["linux"], "monaco"),
        "webmonaco/bin/win32/monaco.exe": get_zip_item(urls["windows"], "monaco.exe"),
    }
    for k, v in binaries.items():
        Path(k).write_bytes(v)
