#!/usr/bin/env python3
"""Veille des marchés : agrège les flux RSS de sources officielles dans veille.json.

Exécuté côté serveur par la GitHub Action « veille » (aucune clé, aucune requête
depuis le navigateur des visiteurs). Si aucun flux ne répond, l'ancien fichier
est conservé : le site n'affiche jamais d'actualité inventée, seulement un état
« indisponible » quand le fichier manque ou est vide.

Usage : python3 scripts/veille.py <fichier_sortie> [<fichier_precedent>]
"""
import email.utils
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

FEEDS = [
    # (source affichée, URL du flux officiel)
    ("BCE", "https://www.ecb.europa.eu/rss/press.html"),
    ("AMF", "https://www.amf-france.org/fr/flux-rss/display/23"),
]
MAX_ITEMS = 30
TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; veille-sodara/1.0; +https://sodara-cpu.github.io/Mywebsite/)"
ATOM = "{http://www.w3.org/2005/Atom}"


def clean(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def parse_date(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        d = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def parse_feed(source, data):
    root = ET.fromstring(data)
    items = []
    for it in root.iter("item"):  # RSS 2.0
        items.append((it.findtext("title"), it.findtext("link"), it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")))
    for it in root.iter(ATOM + "entry"):  # Atom
        link = it.find(ATOM + "link")
        items.append((it.findtext(ATOM + "title"), link.get("href") if link is not None else "", it.findtext(ATOM + "updated") or it.findtext(ATOM + "published")))
    out = []
    for title, link, date in items:
        title, link, d = clean(title), (link or "").strip(), parse_date(date)
        if not title or not link.startswith("https://") or d is None:
            continue  # un élément sans titre, lien sûr ou date n'est pas publié
        out.append({"title": title[:220], "link": link, "source": source, "date": d.isoformat(timespec="minutes")})
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(5_000_000)


def dedupe(items):
    seen, out = set(), []
    for it in sorted(items, key=lambda x: x["date"], reverse=True):
        key = (it["link"].split("?")[0].rstrip("/"), re.sub(r"\W+", "", it["title"].lower()))
        if key[0] in seen or key[1] in seen:
            continue
        seen.update(key)
        out.append(it)
    return out[:MAX_ITEMS]


def main(out_path, previous_path=None):
    items, ok, errors = [], [], []
    for source, url in FEEDS:
        try:
            got = parse_feed(source, fetch(url))
            items += got
            ok.append(source)
        except Exception as e:  # un flux en panne n'empêche pas les autres
            errors.append(f"{source}: {type(e).__name__}")
    if not items and previous_path:
        print("Aucun flux disponible, ancien fichier conservé.", errors)
        try:
            with open(previous_path, encoding="utf-8") as f:
                prev = f.read()
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(prev)
        except OSError:
            pass
        return 0
    data = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "sources": [{"name": s, "url": u} for s, u in FEEDS if s in ok],
        "items": dedupe(items),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"{len(data['items'])} éléments, sources : {', '.join(ok) or 'aucune'}", errors or "")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
