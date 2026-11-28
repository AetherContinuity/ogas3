"""Q-002 H1 -diagnostiikka: Eurostat-vastausten RAKENNE ilman arvoja.
Tulostaa dimensiot, kategoriakoodit ja ei-tyhjien arvojen määrän. Ei yhtään lukuarvoa."""
import json, urllib.parse, urllib.request
ES = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
def get(t, **p):
    pairs = [(k, x) for k, v in p.items() for x in (v if isinstance(v, list) else [v])]
    url = ES + t + "?" + urllib.parse.urlencode(pairs)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "OGAS3/0.1 q002-diag"}), timeout=120) as r:
            d = json.load(r)
    except Exception as e:
        print(t, p.get("unit"), p.get("na_item"), "VIRHE", str(e)[:200]); return
    val = d.get("value")
    n = len(val) if isinstance(val, (list, dict)) else None
    print(t, p.get("unit"), p.get("na_item"), "id=", d.get("id"), "size=", d.get("size"), "arvoja=", n, "value-tyyppi=", type(val).__name__)
    for k in d.get("id", []):
        ix = d["dimension"][k]["category"]["index"]
        print("   ", k, type(ix).__name__, list(ix)[:30])
    if "error" in d: print("   error:", d["error"])
M = ["FI", "SE", "DK", "NO"]; Y = [str(y) for y in range(2008, 2026)]
get("nama_10_gdp", geo=M, na_item=["B1GQ", "P51C"], unit="CP_MNAC", time=Y)
for u in ("CLV20_MNAC", "CLV15_MNAC"):
    get("nama_10_gdp", geo=M, na_item="B1GQ", unit=u, time=Y)
get("nama_10_pe", geo=M, na_item="POP_NC", unit="THS_PER", time=Y)
get("nama_10_gdp", geo=M, na_item="P51C", unit="CP_MNAC", time=Y)
