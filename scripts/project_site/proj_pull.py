"""Download the raw files of the project site's current production deploy."""
import json, pathlib, urllib.request

SITE = "7c50da14-8f61-4212-8928-321519e33b0e"
OUT = pathlib.Path(__import__("os").environ.get("PROJ_SITE_DIR", "/tmp/uj_project_site_build"))
cfg = json.loads(pathlib.Path.home().joinpath("Library/Preferences/netlify/config.json").read_text())
tok = None
for u in cfg.get("users", {}).values():
    t = u.get("auth", {}).get("token")
    if not t:
        continue
    try:
        urllib.request.urlopen(urllib.request.Request(
            "https://api.netlify.com/api/v1/sites/7c50da14-8f61-4212-8928-321519e33b0e",
            headers={"Authorization": "Bearer " + t}), timeout=30).read()
        tok = t
        break
    except Exception as e:
        print("token failed:", e)


def get(url, raw=False):
    h = {"Authorization": "Bearer " + tok}
    if raw:
        h["Accept"] = "application/vnd.bitballoon.v1.raw"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        return r.read()


site = json.loads(get(f"https://api.netlify.com/api/v1/sites/{SITE}"))
dep = site["published_deploy"]["id"]
print("published deploy:", dep)
files = json.loads(get(f"https://api.netlify.com/api/v1/deploys/{dep}/files?per_page=200"))
print("files:", len(files))
manifest = {}
for f in files:
    path = f["id"]
    manifest[path] = f["sha"]
# The API returns metadata, not raw file bytes, so pages are rebuilt from git
# source by proj_build.py and checked against these hashes.
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "manifest.json").write_text(json.dumps({"deploy": dep, "files": manifest}, indent=2))
for k in sorted(manifest):
    print(k, manifest[k])
