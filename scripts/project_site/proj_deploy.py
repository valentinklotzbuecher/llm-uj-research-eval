"""File-digest deploy to the historical project site: replace only the edited HTML pages,
keep every other file hash from the current production deploy."""
import hashlib, json, pathlib, time, urllib.request

SITE = "7c50da14-8f61-4212-8928-321519e33b0e"
SCR = pathlib.Path(__import__("os").environ.get("PROJ_SITE_DIR", "/tmp/uj_project_site_build"))
mf = json.loads((SCR / "manifest.json").read_text())
files = dict(mf["files"])
cfg = json.loads(pathlib.Path.home().joinpath("Library/Preferences/netlify/config.json").read_text())


def req(url, method="GET", data=None, ctype="application/json", tok=None):
    h = {"Authorization": "Bearer " + tok}
    if data is not None:
        h["Content-Type"] = ctype
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read() or b"{}")


tok = None
for u in cfg.get("users", {}).values():
    t = u.get("auth", {}).get("token")
    try:
        site = req(f"https://api.netlify.com/api/v1/sites/{SITE}", tok=t)
        tok = t
        break
    except Exception:
        pass
assert site["published_deploy"]["id"] == mf["deploy"], "live deploy changed since baseline; stop"

new = {}
for p in sorted((SCR / "new").glob("*.html")):
    b = p.read_bytes()
    sha = hashlib.sha1(b).hexdigest()
    files["/" + p.name] = sha
    new["/" + p.name] = b
print("replacing:", sorted(new))

dep = req(f"https://api.netlify.com/api/v1/sites/{SITE}/deploys", "POST",
          json.dumps({"files": files, "title": "Fold notices, add Hypothes.is signpost (Nov 5 2026)"}).encode(), tok=tok)
did = dep["id"]
print("deploy", did, "required", len(dep.get("required", [])))
sha_to_path = {sha: p for p, sha in files.items()}
for sha in dep.get("required", []):
    path = sha_to_path[sha]
    if path not in new:
        raise SystemExit(f"Netlify asked for unchanged file {path}; aborting")
    req(f"https://api.netlify.com/api/v1/deploys/{did}/files{path}", "PUT", new[path],
        "application/octet-stream", tok=tok)
    print("uploaded", path)
for _ in range(60):
    d = req(f"https://api.netlify.com/api/v1/deploys/{did}", tok=tok)
    if d["state"] in ("ready", "error"):
        break
    time.sleep(3)
print("state", d["state"], "url", d.get("ssl_url"))
