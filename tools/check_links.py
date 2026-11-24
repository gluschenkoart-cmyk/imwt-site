#!/usr/bin/env python3
"""Check that every local link, image, script and stylesheet on the site exists."""
import sys, re
from pathlib import Path
from urllib.parse import unquote, urlparse
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parent.parent
bad = []
for page in sorted(ROOT.rglob("*.html")):
    if ".git" in page.parts or "tools" in page.parts:
        continue
    soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
    ids = {t.get("id") for t in soup.find_all(id=True)}
    for tag in soup.find_all(["a", "link", "img", "script", "source", "form"]):
        for attr in ("href", "src", "action"):
            url = tag.get(attr)
            if not url or re.match(r"^(mailto:|tel:|data:|javascript:)", url):
                continue
            u = urlparse(url)
            if u.scheme in ("http", "https") and u.netloc != "imwt.space":
                continue
            path = unquote(u.path)
            if not path and u.fragment:
                if u.fragment not in ids:
                    bad.append(f"{page.relative_to(ROOT)}: #{u.fragment} not found")
                continue
            target = (ROOT / path.lstrip("/")) if path.startswith("/") or u.netloc else (page.parent / path)
            if target.is_dir() or path.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                bad.append(f"{page.relative_to(ROOT)}: {attr}={url}")
for b in bad:
    print(b)
print(f"{len(bad)} broken")
sys.exit(1 if bad else 0)
