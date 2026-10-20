"""What each lane-analysis output was built from: SHA-256 of every input file and the git commit of the code and
data/, so a result can be traced to, and rebuilt from, exactly those inputs. Raw downloads are pinned in inputs.json
and fetched with fetch_inputs.py.
"""
import hashlib, json, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_memo = {}


def sha256(path):
    """SHA-256 of a file, or of every file in a folder (sorted by name)."""
    path = os.path.abspath(path)
    if path not in _memo:
        h = hashlib.sha256()
        files = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(path) for f in fs) if os.path.isdir(path) else [path]
        for f in files:
            with open(f, "rb") as fh:
                for block in iter(lambda: fh.read(1 << 20), b""): h.update(block)
        _memo[path] = h.hexdigest()
    return _memo[path]


def trips_files(trips_dir):
    """The two 2023 BiciMAD trip files the analysis reads."""
    return [os.path.join(trips_dir, f"trips_23_0{m}.csv") for m in ("1_January", "2_February")]


def record(**paths):
    """{name: {file, sha256}} for the given input files (a list of files is hashed in order), plus the git commit of the
    code and whether pipeline/ had uncommitted changes (data inputs are covered by their own hashes)."""
    out = {}
    for name, p in paths.items():
        ps = p if isinstance(p, (list, tuple)) else [p]
        h = sha256(ps[0]) if len(ps) == 1 else hashlib.sha256("".join(sha256(x) for x in ps).encode()).hexdigest()
        out[name] = {"file": ", ".join(os.path.basename(x) for x in ps), "sha256": h}
    try:
        commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "--", "pipeline"], capture_output=True, text=True).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = "unknown", True
    return {"inputs": out, "git_commit": commit, "uncommitted_changes": dirty}


def check(cached, **expected):
    """Stop if a cache was built from other inputs than `expected` (name -> sha256)."""
    for name, h in expected.items():
        got = (cached or {}).get("inputs", {}).get(name, {}).get("sha256")
        if got != h:
            raise SystemExit(f"cache was built from another {name} ({str(got)[:12]} vs {h[:12]}): run the earlier script again")


def accident_years(data_dir):
    """Years covered by data/madrid_bike_accidents.csv: 1 January of its first year to the latest record that
    refresh.py wrote to refresh_meta.json in the same commit."""
    import pandas as pd
    acc = pd.read_csv(os.path.join(data_dir, "madrid_bike_accidents.csv"), usecols=["year"])
    latest = json.load(open(os.path.join(data_dir, "refresh_meta.json")))["accidents_latest"]
    return (pd.Timestamp(latest) - pd.Timestamp(int(acc.year.min()), 1, 1)).days / 365.25
