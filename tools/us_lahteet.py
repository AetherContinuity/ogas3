"""Ennakkokirjaus I (aethercontinuity.github.io SEURANTA.md): lähtötaso.
Vain maatason vuosisummat (kokoamisrajaus, kohta 5). Vain vakiokirjasto + pdftotext.
- C-1 (DoD Construction Programs): vain rivit, joissa maan nimeä seuraa pelkkiä lukuja
  (maayhteenvedot). Muut maan mainitsevat rivit lasketaan, ei tulosteta.
- USAspending: DoD-velvoitteet suorituspaikan maan mukaan, FY-summat.
"""
import json, re, subprocess, sys, urllib.request, datetime

MAAT = {"Finland": "FIN", "Norway": "NOR", "Sweden": "SWE", "Denmark": "DNK"}
UA = {"User-Agent": "Mozilla/5.0 (ACI ogas3; public budget data)", "Accept": "*/*"}
out = {"haettu": datetime.datetime.now(datetime.UTC).isoformat(), "c1": {}, "usaspending": {}, "virheet": []}

def get(url, data=None):
    h = dict(UA)
    if data is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=120) as r:
        return r.read()

num = r"[\s\$\-\d,\.\(\)]+"
for fy in (2024, 2025, 2026, 2027):
    url = f"https://comptroller.war.gov/Portals/45/Documents/defbudget/FY{fy}/FY{fy}_c1.pdf"
    try:
        open("/tmp/c1.pdf", "wb").write(get(url))
        txt = subprocess.run(["pdftotext", "-layout", "/tmp/c1.pdf", "-"], capture_output=True, text=True).stdout
        rec = {"url": url, "maat": {}}
        for maa in MAAT:
            yht, muut = [], 0
            for i, l in enumerate(txt.splitlines()):
                s = l.strip()
                if not re.search(rf"\b{maa}\b", s):
                    continue
                if re.fullmatch(rf"{maa}{num}", s):
                    yht.append(s)
                else:
                    muut += 1
            rec["maat"][maa] = {"yhteenvetorivit": yht, "muut_maininnat_lkm": muut}
        out["c1"][str(fy)] = rec
    except Exception as e:
        out["virheet"].append(f"C-1 FY{fy}: {e!r}")

API = "https://api.usaspending.gov/api/v2/"
try:
    ag = json.loads(get(API + "references/toptier_agencies/"))["results"]
    dod = next(a["agency_name"] for a in ag if a.get("toptier_code") == "097")
    out["usaspending"]["agency"] = dod
    for maa, iso in MAAT.items():
        body = {"group": "fiscal_year",
                "filters": {"time_period": [{"start_date": "2018-10-01", "end_date": "2026-09-30"}],
                            "agencies": [{"type": "awarding", "tier": "toptier", "name": dod}],
                            "place_of_performance_locations": [{"country": iso}]}}
        r = json.loads(get(API + "search/spending_over_time/", body))
        out["usaspending"][maa] = {str(x["time_period"]["fiscal_year"]): x.get("aggregated_amount") for x in r["results"]}
    # Poikkeama 1 (SEURANTA.md, I): PSC-osittelu maatasolla; vain kolme summaa tallennetaan.
    LASNA = set("YZXSM")
    out["usaspending_psc"] = {"maaritelma": "I3a = PSC alkaa Y,Z,X,S,M; I3b = numeerinen; I3c = muut kirjaimet",
                              "keskenerainen": ["2026"]}
    for maa, iso in MAAT.items():
        out["usaspending_psc"][maa] = {}
        for fy in range(2019, 2027):
            summa = {"I3a": 0.0, "I3b": 0.0, "I3c": 0.0}
            page = 1
            while True:
                body = {"filters": {"time_period": [{"start_date": f"{fy-1}-10-01", "end_date": f"{fy}-09-30"}],
                                    "agencies": [{"type": "awarding", "tier": "toptier", "name": dod}],
                                    "place_of_performance_locations": [{"country": iso}]},
                        "limit": 100, "page": page}
                r = json.loads(get(API + "search/spending_by_category/psc/", body))
                for x in r["results"]:
                    c = (x.get("code") or "?")[:1]
                    k = "I3b" if c.isdigit() else ("I3a" if c in LASNA else "I3c")
                    summa[k] += x.get("amount") or 0.0
                if not r.get("page_metadata", {}).get("hasNext"):
                    break
                page += 1
            out["usaspending_psc"][maa][str(fy)] = {k: round(v, 2) for k, v in summa.items()}
except Exception as e:
    out["virheet"].append(f"USAspending: {e!r}")

import os; os.makedirs("data/us", exist_ok=True)
p = f"data/us/i_lahtotaso_{datetime.date.today().isoformat()}.json"
json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1)[:6000])
