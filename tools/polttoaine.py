"""Polttoainekoe: synapsimoottorin kokeilu viikoittaisilla polttoainehinnoilla (julkinen data).

Lähteet (haetaan GitHub Actionsista; työtilan verkko ei salli):
  EU Weekly Oil Bulletin, hintahistoria 2005– (verollinen, EUR/1000 l)
  FRED DCOILBRENTEU (Brent, USD/bbl, päivittäinen; EIA) ja DEXUSEU (USD per EUR)
Vaiheet:
  kartoita  tulostaa xlsx:n välilehdet ja otsikkorivit (rakenteen selvitys ennen jäsentimen lukitsemista)
  poimi     Suomen Euro-super 95 ja diesel (verollinen ja veroton) → data/polttoaine/wob-fi.json
Vain vakiokirjasto (xlsx = zip + XML).
"""
from __future__ import annotations

import io
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

WOB = "https://energy.ec.europa.eu/document/download/906e60ca-8b6a-44e7-8589-652854d2fd3f_en?filename=Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
UA = {"User-Agent": "Mozilla/5.0 (ACI-ogas3-polttoaine)"}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def lataa(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def xlsx_rivit(b: bytes, max_rivit: int | None = None):
    z = zipfile.ZipFile(io.BytesIO(b))
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    nimet = [s.get("name") for s in wb.find("m:sheets", NS)]
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    kohteet = {r.get("Id"): r.get("Target") for r in rels}
    for s in wb.find("m:sheets", NS):
        rid = s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        polku = "xl/" + kohteet[rid].lstrip("/").replace("xl/", "")
        rivit = []
        for i, row in enumerate(ET.fromstring(z.read(polku)).iter("{%s}row" % NS["m"])):
            if max_rivit is not None and i >= max_rivit:
                break
            solut = {}
            for c in row.findall("m:c", NS):
                ref = re.match(r"([A-Z]+)", c.get("r")).group(1)
                v = c.find("m:v", NS)
                x = None if v is None else v.text
                if c.get("t") == "s" and x is not None:
                    x = ss[int(x)]
                solut[ref] = x
            rivit.append(solut)
        yield s.get("name"), rivit


def main(argv=None) -> int:
    cmd = (argv or sys.argv[1:] or ["kartoita"])[0]
    if cmd == "kartoita":
        b = lataa(WOB)
        print("WOB koko", len(b))
        for nimi, rivit in xlsx_rivit(b, max_rivit=8):
            print("=== välilehti:", nimi)
            for r in rivit:
                print("  ", dict(list(r.items())[:14]))
        for sid in ("DCOILBRENTEU", "DEXUSEU"):
            t = lataa(FRED.format(sid)).decode()
            rr = t.splitlines()
            print("===", sid, len(rr), "riviä:", rr[:3], rr[-2:])
        return 0
    if cmd == "poimi":
        import json
        from datetime import date, timedelta
        b = lataa(WOB)
        out = {"lahde": "EU Weekly Oil Bulletin, Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx (European Commission, DG ENER)",
               "sha256": __import__("hashlib").sha256(b).hexdigest(), "maa": "FI", "yksikko": "EUR/1000 l", "sarjat": {}}
        for nimi, rivit in xlsx_rivit(b):
            if nimi not in ("Prices wo taxes", "Prices with taxes"):
                continue
            otsikot = rivit[0]
            sarakkeet = {k: v for k, v in otsikot.items() if v and v.startswith("FI_price_") and v.endswith(("euro95", "diesel"))}
            print(nimi, "sarakkeet", sarakkeet)
            for col, otsikko in sarakkeet.items():
                srj = {}
                for r in rivit[3:]:
                    try:
                        d = (date(1899, 12, 30) + timedelta(days=int(float(r.get("A"))))).isoformat()
                        srj[d] = round(float(r[col]), 2)
                    except (TypeError, ValueError, KeyError):
                        continue
                out["sarjat"][otsikko] = dict(sorted(srj.items()))
        print({k: (len(v), min(v), max(v)) for k, v in out["sarjat"].items()})
        Path("data/polttoaine").mkdir(parents=True, exist_ok=True)
        Path("data/polttoaine/wob-fi.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        return 0
    if cmd == "poimi-kaikki":
        import json
        from datetime import date, timedelta
        b = lataa(WOB)
        out = {"lahde": "EU Weekly Oil Bulletin, Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx (European Commission, DG ENER)",
               "sha256": __import__("hashlib").sha256(b).hexdigest(), "valilehti": "Prices wo taxes", "yksikko": "1000 l", "sarjat": {}}
        for nimi, rivit in xlsx_rivit(b):
            if nimi != "Prices wo taxes":
                continue
            ots = rivit[0]
            cols = {k: v for k, v in ots.items() if v and re.fullmatch(r"[A-Z]{2}_price_wo_tax_(euro95|diesel)", v)}
            for col, o in cols.items():
                srj = {}
                for r in rivit[3:]:
                    try:
                        d = (date(1899, 12, 30) + timedelta(days=int(float(r.get("A"))))).isoformat()
                        srj[d] = round(float(r[col]), 2)
                    except (TypeError, ValueError, KeyError):
                        continue
                if srj:
                    out["sarjat"][o] = dict(sorted(srj.items()))
        print(len(out["sarjat"]), "sarjaa")
        Path("data/polttoaine").mkdir(parents=True, exist_ok=True)
        Path("data/polttoaine/wob-kaikki.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        return 0
    raise SystemExit(f"tuntematon {cmd}")


if __name__ == "__main__":
    sys.exit(main())
