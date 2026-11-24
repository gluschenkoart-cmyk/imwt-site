#!/usr/bin/env python3
"""Build the static English home page /en/index.html from the Ukrainian /index.html.

Why: search engines and AI crawlers read the HTML as served and mostly do not run JavaScript,
so an English version that only appears after clicking a JS language toggle is invisible to
them. This script renders it as a real page with its own URL, canonical and hreflang pair.

Source of the English text: tools/home-en.json (keys = data-i18n / data-i18n-html attributes
in index.html). After editing index.html or the translations, run:

    python3 tools/build_en_home.py

The script fails if Cyrillic text is left in the English page, so nothing untranslated slips in.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://imwt.space"

EN_TITLE = "IMWT — International Museum of Water Towers | Open digital museum of water towers"
EN_DESCRIPTION = (
    "IMWT — International Museum of Water Towers: an open digital museum and research "
    "programme on the history, engineering and architecture of water towers worldwide. "
    "Research, an atlas of the water towers of Ukraine, submissions from the public. "
    "Pilot site: Mala Vilshanka, Kyiv Oblast, Ukraine."
)

# Texts that are not covered by data-i18n attributes.
EXTRA = {
    "img_vision_alt": "Concept visualisation of the IMWT museum in the Mala Vilshanka water tower",
}
TEXT = {
    "Перейти до змісту": "Skip to content",
    "15 м": "15 m",
    "Не заповнюйте": "Leave this empty",
}
ARIA = {
    "IMWT — на головну": "IMWT — home",
    "Головна навігація": "Main navigation",
    "Відкрити меню": "Open menu",
    "Мобільне меню": "Mobile menu",
    "Декоративна концепція глобальної карти башт": "Decorative concept of a world map of water towers",
    "Башта в Малій Вільшанці — візуальна концепція": "The Mala Vilshanka water tower — visual concept",
    "Гіперболоїдна башта Шухова в Миколаєві": "Shukhov hyperboloid tower in Mykolaiv",
}

CYRILLIC = re.compile(r"[Ѐ-ӿ]")
# Ukrainian names that legitimately stay in the English page (the museum's own name, etc.).
ALLOWED_CYRILLIC = (
    "Міжнародний музей водонапірних башт",
    "музей водонапірних веж",
    "УКР",
    "Українська версія",
    "Українською",
)

# Relative links that have a dedicated English page.
EN_TARGETS = {
    "history/": "../history/en/",
    "ukraine/": "../ukraine/en/",
    "ukraine/IMWT_Vodonapirni_bashty_Ukrainy_2026.pdf": "../ukraine/en/IMWT_Water_Towers_of_Ukraine_2026.pdf",
    "white-paper/": "../white-paper/en/",
}


def is_relative(url: str) -> bool:
    return not re.match(r"^(?:[a-z][a-z0-9+.-]*:|/|#)", url, re.I)


def rewrite_url(url: str) -> str:
    if not is_relative(url):
        return url
    return EN_TARGETS.get(url, "../" + url)


def set_meta(soup: BeautifulSoup, attr: str, key: str, content: str) -> None:
    tag = soup.find("meta", attrs={attr: key})
    if tag is None:
        tag = soup.new_tag("meta", attrs={attr: key})
        soup.head.append(tag)
    tag["content"] = content


def main() -> int:
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    en = json.loads((ROOT / "tools" / "home-en.json").read_text(encoding="utf-8"))
    soup = BeautifulSoup(src, "html.parser")

    missing: list[str] = []
    for el in soup.select("[data-i18n]"):
        key = el["data-i18n"]
        if key in en:
            el.clear()
            el.append(NavigableString(en[key]))
        else:
            missing.append(key)
    for el in soup.select("[data-i18n-html]"):
        key = el["data-i18n-html"]
        if key in en:
            el.clear()
            el.append(BeautifulSoup(en[key], "html.parser"))
        else:
            missing.append(key)
    for el in soup.select("[data-placeholder-en]"):
        el["placeholder"] = el["data-placeholder-en"]
    if missing:
        print("Missing English keys:", ", ".join(sorted(set(missing))), file=sys.stderr)
        return 1

    for node in soup.find_all(string=True):
        stripped = node.strip()
        if stripped in TEXT:
            node.replace_with(node.replace(stripped, TEXT[stripped]))
    for tag in soup.find_all(attrs={"aria-label": True}):
        tag["aria-label"] = ARIA.get(tag["aria-label"], tag["aria-label"])

    # The «history» teaser has «read in Ukrainian / read in English» buttons: on the English
    # page the main button reads the English study and the secondary one the Ukrainian original.
    for a in soup.select("a.hb-cta"):
        if a.get("href") == "history/":
            a["href"] = "history/en/"
            a.string = "Read the study →"
        elif a.get("href") == "history/en/":
            a["href"] = "/history/"
            a["lang"] = "uk"
            a["hreflang"] = "uk"
            a.string = "Українською →"

    for img in soup.find_all("img"):
        if "imwt-vision" in img.get("src", ""):
            img["alt"] = EXTRA["img_vision_alt"]

    # Language, title, description, social cards.
    soup.html["lang"] = "en"
    soup.title.string = EN_TITLE
    set_meta(soup, "name", "description", EN_DESCRIPTION)
    set_meta(soup, "property", "og:title", EN_TITLE)
    set_meta(soup, "property", "og:description", EN_DESCRIPTION)
    set_meta(soup, "property", "og:url", f"{SITE}/en/")
    set_meta(soup, "property", "og:locale", "en_GB")
    set_meta(soup, "property", "og:locale:alternate", "uk_UA")
    set_meta(soup, "name", "twitter:title", EN_TITLE)
    set_meta(soup, "name", "twitter:description", EN_DESCRIPTION)

    canonical = soup.find("link", rel="canonical")
    canonical["href"] = f"{SITE}/en/"

    # JSON-LD: the page itself is the English WebPage; the organisation keeps its @id.
    for script in soup.find_all("script", type="application/ld+json"):
        data = json.loads(script.string)
        for node in data.get("@graph", []):
            types = node.get("@type")
            types = types if isinstance(types, list) else [types]
            if "WebPage" in types:
                node["@id"] = f"{SITE}/en/#webpage"
                node["url"] = f"{SITE}/en/"
                node["name"] = EN_TITLE
                node["description"] = EN_DESCRIPTION
                node["inLanguage"] = "en"
        script.string = json.dumps(data, ensure_ascii=False)

    # Relative URLs move one level down.
    for tag in soup.find_all(href=True):
        if tag.name == "link" and tag.get("rel") in (["canonical"], ["alternate"]):
            continue
        tag["href"] = rewrite_url(tag["href"])
    for tag in soup.find_all(src=True):
        tag["src"] = rewrite_url(tag["src"])
    for tag in soup.find_all(action=True):
        tag["action"] = rewrite_url(tag["action"])

    # The language switch is a real link to the Ukrainian page.
    toggle = soup.find(id="languageToggle")
    toggle["href"] = "/"
    toggle["hreflang"] = "uk"
    toggle["lang"] = "uk"
    toggle["aria-label"] = "Українська версія"
    soup.find(id="langText").string = "УКР"

    html = str(soup)
    html = html.replace(
        "<!-- IMWT:AUTOGEN -->",
        "<!-- Generated by tools/build_en_home.py from /index.html — edit the source, not this file. -->",
    )

    # Nothing Ukrainian may remain in the visible text.
    text = BeautifulSoup(html, "html.parser")
    for bad in text(["script", "style"]):
        bad.decompose()
    leftovers = []
    for s in text.find_all(string=CYRILLIC):
        chunk = str(s)
        for allowed in ALLOWED_CYRILLIC:
            chunk = chunk.replace(allowed, "")
        if CYRILLIC.search(chunk):
            leftovers.append(str(s).strip()[:90])
    for tag in text.find_all(True):
        for attr in ("alt", "placeholder", "title", "aria-label", "content"):
            value = tag.get(attr)
            if isinstance(value, str) and CYRILLIC.search(value):
                chunk = value
                for allowed in ALLOWED_CYRILLIC:
                    chunk = chunk.replace(allowed, "")
                if CYRILLIC.search(chunk) and not (attr == "content" and tag.get("property") == "og:locale:alternate"):
                    leftovers.append(f"{tag.name}[{attr}]={value[:80]}")
    if leftovers:
        print("Ukrainian text left in /en/index.html:", file=sys.stderr)
        for item in leftovers:
            print("  -", item, file=sys.stderr)
        return 1

    out = ROOT / "en" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(html)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
