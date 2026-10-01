"""Q-001 H4 lukitulla YVA-tunnistuksella (poikkeama_1.md).

Ensisijainen H4-luku. Tunnistaa ohjelma_nahtavilla-vaiheen tapahtuman
evidence-lainauksesta lukitushetken (82b3bde, 2026-09-30) säännöillä ja
järjestyksellä — ei proxyn nykyisestä vaihe-kentästä. Herkkyysluku on
q001.py H4. q001.py:tä ei muuteta.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# aci-yva-proxy worker.js @ lukitus, VAIHEET-järjestys (ensimmäinen osuma voittaa)
LUKITTU = [
    ("perusteltu_paatelma", re.compile(r"perustel\S*\s+päätelm", re.I)),
    ("ohjelma_lausunto", re.compile(r"lausun\S*[^.]{0,60}?(yva-|arviointi)?ohjelmasta|ohjelmasta\s+on\s+annettu", re.I)),
    ("ohjelma_nahtavilla", re.compile(r"(arviointi|yva-)ohjelm\S*[^.]{0,40}?nähtävillä", re.I)),
    ("selostus_nahtavilla", re.compile(r"(arviointi|yva-)selostu\S*[^.]{0,40}?nähtävillä", re.I)),
]
RX = re.compile(r"datakeskus|palvelinkeskus|data ?cent", re.I)  # = q001.py h4


def lukittu_vaihe(text: str):
    return next((v for v, rx in LUKITTU if rx.search(text)), None)


def h4_lukittu(months=("2026-11", "2026-12", "2027-01", "2027-02", "2027-03", "2027-04")) -> dict:
    seen, vain_uusi = {}, {}
    for m in months:
        p = ROOT / "snapshots" / f"{m}.json"
        if not p.exists():
            raise SystemExit(f"snapshot {m} puuttuu — H4:ää ei voi vielä mitata")
        for e in json.loads(p.read_text(encoding="utf-8"))["events"]:
            pr = e.get("parameters") or {}
            if not (e.get("source") == "YVA" and RX.search(pr.get("hanke") or "")
                    and "2026-10-01" <= (e.get("known_at") or "")[:10] <= "2027-03-31"):
                continue
            quote = ((e.get("evidence") or [{}])[0]).get("quote") or ""
            if lukittu_vaihe(quote) == "ohjelma_nahtavilla":
                seen[pr["slug"]] = (e["known_at"][:10], pr.get("hanke"))
            elif pr.get("vaihe") == "ohjelma_nahtavilla":
                vain_uusi[pr["slug"]] = (e["known_at"][:10], pr.get("hanke"), quote[:160])
    for s in seen:
        vain_uusi.pop(s, None)
    return {"hypoteesi": "H4 (lukittu instrumentti, ensisijainen)", "uudet": sorted(seen.values()),
            "n": len(seen), "ennuste": ">= 3", "tulos": "TUETTU" if len(seen) >= 3 else "KUMOTTU",
            "vain_nykyisella_instrumentilla": sorted(vain_uusi.values())}


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        assert lukittu_vaihe("Arviointiohjelma nähtävillä 28.8.-26.9.2025") == "ohjelma_nahtavilla"
        assert lukittu_vaihe("YVA-ohjelma oli kuultavana 4.11.-5.12.2022.") is None
        assert lukittu_vaihe("Lausunto YVA-ohjelmasta on annettu, ohjelma nähtävillä") == "ohjelma_lausunto"
        print("ok")
    else:
        print(json.dumps(h4_lukittu(), ensure_ascii=False, indent=1))
