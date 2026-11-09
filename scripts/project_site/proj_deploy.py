"""File-digest deploy to the historical project site: replace only the files staged by
proj_build.py, keep every other file hash from the current production deploy.
The /working-paper/ copy is replaced as a whole (files no longer in the paper are dropped).

Usage: python3 proj_deploy.py "deploy title"
"""
import hashlib, json, os, pathlib, sys, time, urllib.parse, urllib.request

SITE = "7c50da14-8f61-4212-8928-321519e33b0e"
SCR = pathlib.Path(os.environ.get("PROJ_SITE_DIR", "/tmp/uj_project_site_build"))
WP = "/working-paper/"
title = sys.argv[1] if len(sys.argv) > 1 else "Project site update"
mf = json.loads((SCR / "manifest.json").read_text())
files = dict(mf["files"])
cfg = json.loads(pathlib.Path.home().joinpath("Library/Preferences/netlify/config.json").read_text())


def req(url, method="GET", data=None, ctype="application/json", tok=None):
    h = {"Authorization": "Bearer " + tok}
    if data is not None:
        h["Content-Type"] = ctype
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=300) as resp:
        return json.loads(resp.read() or b"{}")


tok = None
for u in cfg.get("users", {}).values():
    t = u.get("auth", {}).get("token")
    if not t:
        continue
    try:
        site = req(f"https://api.netlify.com/api/v1/sites/{SITE}", tok=t)
        tok = t
        break
    except Exception:
        pass
assert site["published_deploy"]["id"] == mf["deploy"], "live deploy changed since baseline; stop"

new = {}
staged = SCR / "new"
for p in sorted(staged.rglob("*")):
    if p.is_file():
        new["/" + p.relative_to(staged).as_posix()] = p.read_bytes()
if any(k.startswith(WP) for k in new):
    dropped = [k for k in files if k.startswith(WP) and k not in new]
    for k in dropped:
        del files[k]
    print("dropped stale working-paper files:", len(dropped))
for k, b in new.items():
    files[k] = hashlib.sha1(b).hexdigest()
print("replacing/adding", len(new), "files; total", len(files))

dep = req(f"https://api.netlify.com/api/v1/sites/{SITE}/deploys", "POST",
          json.dumps({"files": files, "title": title}).encode(), tok=tok)
did = dep["id"]
required = set(dep.get("required", []))
print("deploy", did, "required", len(required))
done = set()
for path, b in new.items():
    sha = files[path]
    if sha in required and sha not in done:
        req(f"https://api.netlify.com/api/v1/deploys/{did}/files{urllib.parse.quote(path)}", "PUT", b,
            "application/octet-stream", tok=tok)
        done.add(sha)
missing = required - done
if missing:
    raise SystemExit(f"Netlify asked for {len(missing)} files not staged; deploy {did} left unpublished")
print("uploaded", len(done))
for _ in range(100):
    d = req(f"https://api.netlify.com/api/v1/deploys/{did}", tok=tok)
    if d["state"] in ("ready", "error"):
        break
    time.sleep(3)
print("state", d["state"], "url", d.get("ssl_url"))
