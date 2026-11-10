#!/usr/bin/env python3
"""Builds the son's practice app (docs/, served by GitHub Pages) from a Szófüzet data export.

Usage: python3 build/build.py data.json

data.json is what the Szófüzet artifact's database holds:
  {"words": [{"id": ..., "en": ..., "hu": ..., "book": ..., "lesson": ..., "created": ..., ...}],
   "usage": [{"id": "YYYY-MM-DD", "sec": ..., "ans": ..., "ok": ..., "ses": ..., "xp": ..., "fz": ...}],
   "facts": {"updated": ..., "past": [...], "now": [...]}}

It mirrors kidHtml() in the Szófüzet page: same word fields, same lesson order.
Prints CHANGED or UNCHANGED, so a caller knows whether a commit is needed.
"""
import datetime
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
SITE = ROOT / "docs"
TOPICS = {"Család és barátok", "Iskola", "Sport", "Étel és ital", "Utazás", "Időjárás", "Természet és állatok", "Otthon",
          "Város és közlekedés", "Munka", "Érzések", "Test és egészség", "Szabadidő", "Technika", "Ruha", "Idő és dátum", "Egyéb"}


def nat_key(s):
    """Natural, accent-insensitive order, like localeCompare(..., "hu", {numeric: true})."""
    base = unicodedata.normalize("NFD", (s or "").lower())
    base = "".join(c for c in base if not unicodedata.combining(c))
    return [(0, int(t), "") if t.isdigit() else (1, 0, t) for t in re.split(r"(\d+)", base) if t]


def num(v):
    try:
        return float(v) if v not in (None, "") else 0
    except (TypeError, ValueError):
        return 0


def build(data):
    words = []
    for w in data.get("words", []):
        en, hu = str(w.get("en") or "").strip(), str(w.get("hu") or "").strip()
        if not en or not hu:
            continue
        topic = str(w.get("topic") or "").strip()
        words.append({
            "en": en, "hu": hu, "pos": w.get("pos") or "", "example": w.get("example") or "",
            "book": w.get("book") or "Egyéb", "lesson": w.get("lesson") or "Lecke nélkül",
            "topic": topic if topic else "Egyéb", "c": num(w.get("created")), "known": bool(w.get("known") or w.get("kk")), "enAlt": [str(x) for x in (w.get("enAlt") or [])],
            # practice data stays out of the public site; a new phone gets it back from the parents' restore code
            "kb": 0, "kr": 0, "kw": 0, "kl": 0,
        })
    words.sort(key=lambda w: (nat_key(w["book"]), nat_key(w["lesson"]), w["c"]))
    log = {}  # the daily practice log stays private too
    facts = data.get("facts") or {}
    facts = {"past": facts.get("past") or [], "now": facts.get("now") or [], "updated": facts.get("updated") or ""}
    payload = {"words": words, "log": log, "facts": facts}

    # only rebuild when the content changed, so Netlify is not redeployed for nothing
    # a new app version (template or static files) also counts as a change
    code = hashlib.sha256((BUILD / "template.html").read_bytes()
                          + b"".join(f.read_bytes() for f in sorted((BUILD / "static").iterdir()))).hexdigest()
    stamp = json.dumps({"code": code, "data": payload}, ensure_ascii=False, sort_keys=True)
    old = (SITE / ".content.json").read_text() if (SITE / ".content.json").exists() else ""
    if stamp == old and (SITE / "index.html").exists():
        return False

    payload["date"] = datetime.date.today().strftime("%Y. %m. %d.")
    tpl = (BUILD / "template.html").read_text()
    js = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    if tpl.count("__DATA__") != 1:
        sys.exit("template.html must contain __DATA__ exactly once")
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(BUILD / "static", SITE)
    (SITE / ".nojekyll").write_text("")  # serve the files as they are, without GitHub's Jekyll step
    (SITE / "index.html").write_text(tpl.replace("__DATA__", js))
    (SITE / ".content.json").write_text(stamp)
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    data = json.loads(Path(sys.argv[1]).read_text())
    print("CHANGED" if build(data) else "UNCHANGED",
          f"({len(data.get('words', []))} words, {len(data.get('usage', []))} days, "
          f"{len((data.get('facts') or {}).get('now') or [])} current facts)")
