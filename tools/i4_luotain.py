"""I4-lähteen luotain: mitkä Puolustusvoimien/puolustusministeriön tiedotelistaukset ovat koneellisesti haettavissa."""
import urllib.request, re
U = ["https://puolustusvoimat.fi/", "https://puolustusvoimat.fi/tiedotteet", "https://puolustusvoimat.fi/web/guest/tiedotteet",
     "https://puolustusvoimat.fi/ajankohtaista", "https://puolustusvoimat.fi/-/rss", "https://puolustusvoimat.fi/rss",
     "https://puolustusvoimat.fi/sitemap.xml", "https://puolustusvoimat.fi/robots.txt",
     "https://valtioneuvosto.fi/robots.txt", "https://valtioneuvosto.fi/sitemap.xml",
     "https://www.defmin.fi/", "https://www.defmin.fi/robots.txt"]
for u in U:
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (ACI ogas3)"}), timeout=30)
        b = r.read(); t = b.decode("utf-8", "replace")
        links = sorted(set(re.findall(r'href="([^"]*(?:tiedot|uutis|rss|feed|ajankoht|news|sitemap)[^"]*)"', t, re.I)))[:25]
        print(f"== {u} {r.status} {r.headers.get('content-type')} {len(b)}")
        if u.endswith(("robots.txt",)): print(t[:1500])
        elif "sitemap" in u: print(t[:1500])
        else: print("\n".join(links))
    except Exception as e:
        print(f"== {u} VIRHE {e!r}")
