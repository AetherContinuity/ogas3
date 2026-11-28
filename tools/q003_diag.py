"""Q-003 -diagnostiikka 2: muuttujat ja koodit ilman arvoja."""
import json, urllib.parse, urllib.request
UA = {"User-Agent": "OGAS3/0.1 q003-diag"}
def j(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return json.load(r)
d = j("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/apri_ap_anouta?geo=FI&time=2015")
lab = d["dimension"]["prod_ani"]["category"]["label"]
print("apri_ap_anouta milk:", [(k, v) for k, v in lab.items() if "milk" in v.lower()])
d = j("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/apri_ap_anouta?prod_ani=12111000&time=2015")
print("apri geo:", list(d["dimension"]["geo"]["category"]["index"])[:40])
B = "https://statdb.luke.fi/PxWeb/api/v1/fi/LUKE/"
for t in ["maa/tuohin/v/0600_tuohin.px", "maa/maitot/v/0600_maitot.px", "maa/maitot/v/1100_maitot.px", "maa/kotlkm/0300_kotlkm.px"]:
    try:
        m = j(B + urllib.parse.quote(t))
    except Exception as e:
        print(t, "VIRHE", str(e)[:100]); continue
    print("==", t, m.get("title"))
    for v in m["variables"]:
        vals = list(zip(v["values"], v["valueTexts"]))
        print("   ", v["code"], len(vals), vals[:25] if len(vals) < 60 else (vals[:5], "...", vals[-3:]))
