#!/usr/bin/env python3
"""Publishes a Sahra Copy release: copies the installer here, signs it, writes update.json.

  python3 publish.py <setup.exe> --version 0.1.1 --build 2 --notes "What changed" \
      --key ../sahra-copy/signing/update-key.pem [--force] [--min BUILD]

--force makes every older copy update before it can be used; --min does that only for
builds below BUILD. The signing key lives in the private code repo, never here.
"""
import argparse, json, os, shutil
from cryptography.hazmat.primitives import serialization

REPO = "moraxdev/sahra-copy-releases"

p = argparse.ArgumentParser()
p.add_argument("setup")
p.add_argument("--version", required=True)
p.add_argument("--build", type=int, required=True)
p.add_argument("--notes", default="")
p.add_argument("--key", required=True)
p.add_argument("--force", action="store_true")
p.add_argument("--min", type=int, default=0)
a = p.parse_args()

here = os.path.dirname(os.path.abspath(__file__))
name = f"SahraCopy-Setup-{a.version}.exe"
os.makedirs(os.path.join(here, "installers"), exist_ok=True)
dest = os.path.join(here, "installers", name)
shutil.copyfile(a.setup, dest)
data = open(dest, "rb").read()
key = serialization.load_pem_private_key(open(a.key, "rb").read(), password=None)
manifest_path = os.path.join(here, "update.json")
manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
old = manifest.get("windows", {})
if old.get("build", 0) >= a.build:
    raise SystemExit(f"build {a.build} is not newer than the published {old.get('build')}")
manifest["windows"] = {
    "version": a.version,
    "build": a.build,
    "notes": a.notes,
    "force": a.force,
    "minBuild": a.min,
    "installer": {
        "url": f"https://raw.githubusercontent.com/{REPO}/main/installers/{name}",
        "signature": key.sign(data).hex(),
        "size": len(data),
    },
}
json.dump(manifest, open(manifest_path, "w"), indent=2)
# Keep only the three newest installers.
files = sorted((f for f in os.listdir(os.path.join(here, "installers")) if f.endswith(".exe")), key=lambda f: os.path.getmtime(os.path.join(here, "installers", f)))
for f in files[:-3]:
    os.remove(os.path.join(here, "installers", f))
print(f"published {a.version} (build {a.build}), {len(data)} bytes")
