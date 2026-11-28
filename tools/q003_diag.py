"""Q-003 -diagnostiikka: lähteiden RAKENNE ilman arvoja (taulut, dimensiot, koodit, nimikkeet)."""
import json, urllib.parse, urllib.request
UA = {"User-Agent": "OGAS3/0.1 q003-diag"}
def j(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return json.load(r)
def es_meta(t, **p):
    pairs = [(k, x) for k, v in p.items() for x in (v if isinstance(v, list) else [v])]
    try:
        d = j("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/" + t + "?" + urllib.parse.urlencode(pairs))
    except Exception as e:
        print(t, p, "VIRHE", str(e)[:150]); return
    print(t, p, "id=", d.get("id"), "size=", d.get("size"), "arvoja=", len(d.get("value") or {}))
    for k in d.get("id", []):
        c = d["dimension"][k]["category"]; lab = c.get("label", {})
        ks = list(c["index"])
        print("   ", k, [(x, lab.get(x, "")[:60]) for x in ks[:40]])
# Eurostat: maidon tuottajahinta ja maitotilat (vain rakenne; maa- ja vuosirajaus pieni)
es_meta("apri_ap_anouta", geo="FI", time="2015")
es_meta("ef_lsk_dairy", geo="FI")
es_meta("ef_kvaareg", geo="FI", time="2016")
es_meta("apro_mk_farm", geo="FI", time="2015")
es_meta("apro_mk_cola", geo="FI", time="2015")
# Luke statdb: taulut, joissa maito
def luke(polku=""):
    for base in ("https://statdb.luke.fi/PxWeb/api/v1/fi/LUKE/", "https://statdb.luke.fi/PXWeb/api/v1/fi/LUKE/"):
        try:
            return j(base + polku), base
        except Exception as e:
            err = str(e)[:120]
    print("LUKE VIRHE", polku, err); return None, None
root, base = luke()
if root:
    print("LUKE base", base, [x.get("id") for x in root])
    def kay(polku, syv):
        d, _ = luke(polku)
        if not d: return
        for x in d:
            p = polku + x["id"] + ("/" if x.get("type") == "l" else "")
            t = x.get("text", "")
            if x.get("type") == "l" and syv < 3 and any(k in (p + t).lower() for k in ["maito", "kotielain", "kotieläin", "maatilat", "maatalous", "02 maatalous", "maa"]):
                kay(p, syv + 1)
            elif x.get("type") == "t" and any(k in t.lower() for k in ["maito", "maidon", "lypsy", "tilojen lukum", "maatilojen lukum"]):
                print("  T", p, "|", t[:110])
    kay("", 0)
