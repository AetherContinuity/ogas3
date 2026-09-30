"""Q-001 — mittaukset. LUKITTU yhdessä q001.md:n kanssa.

Tätä tiedostoa EI muuteta rekisteröinnin jälkeen. Jos mittauksessa
havaitaan vika, korjaus tehdään uutena tiedostona (q001_korjaus_N.py)
ja molempien tulokset raportoidaan. Sama periaate kuin lukitussa
tracessa: vanhaa ei korvata, uusi viittaa siihen.

Ajo:  python3 ennakkorekisteroinnit/q001/q001.py H1|H2|H3|H4
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# ── Kiinteä datakeskustoimijoiden luettelo (DT) ──────────────────────
# YVA-datakeskushankkeiden kehittäjät (lahto_yva.json) ja niiden
# konsernit, sekä toimijat jotka Avoimuusrekisterin kaudella 5 ilmoittivat
# datakeskustoiminnan omaksi liiketoiminnakseen. Täsmäys nimen alkuun,
# kirjainkoosta riippumatta. Luetteloa EI täydennetä mittaushetkellä:
# luettelon ulkopuoliset yritykset raportoidaan erikseen, ei lasketa.
DT = [
    "microsoft", "google", "tuike", "hyperco", "polarnode", "data prop link",
    "jokelan vihreä maa", "mustanlahden datakeskus", "pohjan voima keminmaa",
    "finnish data center association", "verne", "verda cloud",
]


def is_dt(name: str | None) -> bool:
    n = (name or "").strip().lower()
    return any(n.startswith(s) for s in DT)


def laatija(node: dict) -> str | None:
    """Lausunnon antaja tracen solmusta. laatija-kenttä, tai nimekkeen
    alku ennen ';' ("Rajavartiolaitos; Ei lausuttavaa")."""
    v = (node.get("_derived") or {}).get("laatija")
    if v:
        return re.sub(r"\s*\(\d+\)\s*$", "", v).strip()
    q = ((node.get("evidence") or [{}])[0].get("quote") or "")
    return q.split(";")[0].strip() or None if ";" in q else None


def latest_trace(tunnus: str, min_locked: str) -> dict:
    stem = tunnus.replace(":", "").replace("/", "-")
    files = sorted((ROOT / "traces").glob(f"{stem}-trace-*.json"))
    ok = [json.loads(p.read_text(encoding="utf-8")) for p in files]
    ok = [t for t in ok if t.get("_locked_at", "") >= min_locked]
    if not ok:
        raise SystemExit(f"{tunnus}: ei tracea lukittuna {min_locked} tai myöhemmin — mittausta ei voi tehdä")
    return max(ok, key=lambda t: (t["_locked_at"], t.get("_revision", 1)))


def lausunnonantajat(trace: dict) -> list[str]:
    out = []
    for n in trace.get("observed") or []:
        if n.get("doc_type") == "LAUSUNTO":
            a = laatija(n)
            if a and a not in out:
                out.append(a)
    return out


# Mittausajankohta H1/H2: kierrokset päättyvät 2.10. ja 9.10.2026.
# Mediaaniviive lausuntomenettelyssä on 7 vrk; 30 vrk marginaali.
H12_MIN_LOCKED = "2026-11-08"


def h1() -> dict:
    t = latest_trace("TEM043:00/2026", H12_MIN_LOCKED)
    la = lausunnonantajat(t)
    dt = [a for a in la if is_dt(a)]
    return {"hypoteesi": "H1", "trace_locked_at": t["_locked_at"], "lausunnonantajia": len(la),
            "dt": dt, "n_dt": len(dt), "ennuste": ">= 3", "tulos": "TUETTU" if len(dt) >= 3 else "KUMOTTU",
            "muut_yritykset": [a for a in la if not is_dt(a) and re.search(r"\b(oy|oyj|ab|ltd)\b", a, re.I)]}


def h2() -> dict:
    from actors import actor_role, canonical
    a = latest_trace("TEM040:00/2026", H12_MIN_LOCKED)
    b = latest_trace("TEM043:00/2026", H12_MIN_LOCKED)
    ca = {canonical(x) or x for x in lausunnonantajat(a)}
    cb = {canonical(x) or x for x in lausunnonantajat(b)}
    both = sorted(ca & cb)
    roles = {x: actor_role(x)[0] for x in both}
    non_auth = [x for x in both if roles[x] not in ("viranomainen",)]
    unknown = [x for x in both if roles[x] is None]
    # Tuntematon rooli: raportoidaan molempiin suuntiin, ei arvata.
    lo = len([x for x in non_auth if roles[x] is not None])
    hi = len(non_auth)
    return {"hypoteesi": "H2", "yhteiset": both, "roolit": roles, "ei_viranomaisia_min": lo,
            "ei_viranomaisia_max": hi, "rooli_tuntematon": unknown, "ennuste": "<= 3",
            "tulos": ("TUETTU" if hi <= 3 else "KUMOTTU" if lo > 3 else "RATKAISEMATON (tuntemattomat roolit)")}


def h3(term_json: str) -> dict:
    """term_json: Avoimuusrekisterin kausi 6 (7–12/2026) proxysta
    ?term_route=activities_term&termId=6, tallennettuna repoon."""
    DX = re.compile(r"datakesk|palvelinkesk|data ?cent", re.I)
    d = json.loads(Path(term_json).read_text(encoding="utf-8"))
    if d.get("termId") not in ("6", 6):
        raise SystemExit("H3 mitataan kaudelta 6")
    proj = other = 0
    for n in d.get("data") or []:
        for t in n.get("topics") or []:
            p = t.get("contactTopicProject") or {}
            txt = f"{t.get('contactTopicOther') or ''} {p.get('fi') or ''} {t.get('title') or ''}"
            if DX.search(txt):
                if p.get("projectId"):
                    proj += 1
                else:
                    other += 1
    n = proj + other
    share = other / n if n else None
    return {"hypoteesi": "H3", "hankenumerolla": proj, "ilman": other, "osuus_ilman": share,
            "ennuste": "> 0.5", "tulos": None if share is None else ("TUETTU" if share > 0.5 else "KUMOTTU")}


def h4() -> dict:
    """Uudet datakeskus-YVA:t: vaihe ohjelma_nahtavilla, known_at
    2026-10-01 … 2027-03-31, snapshoteista 2026-11 … 2027-04."""
    RX = re.compile(r"datakeskus|palvelinkeskus|data ?cent", re.I)
    seen = {}
    for m in ("2026-11", "2026-12", "2027-01", "2027-02", "2027-03", "2027-04"):
        p = ROOT / "snapshots" / f"{m}.json"
        if not p.exists():
            raise SystemExit(f"snapshot {m} puuttuu — H4:ää ei voi vielä mitata")
        for e in json.loads(p.read_text(encoding="utf-8"))["events"]:
            pr = e.get("parameters") or {}
            if (e.get("source") == "YVA" and pr.get("vaihe") == "ohjelma_nahtavilla"
                    and RX.search(pr.get("hanke") or "")
                    and "2026-10-01" <= (e.get("known_at") or "")[:10] <= "2027-03-31"):
                seen[pr["slug"]] = (e["known_at"][:10], pr.get("hanke"))
    return {"hypoteesi": "H4", "uudet": sorted(seen.values()), "n": len(seen), "ennuste": ">= 3",
            "tulos": "TUETTU" if len(seen) >= 3 else "KUMOTTU"}


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"H1": h1, "H2": h2, "H4": h4}.get(which)
    res = h3(sys.argv[2]) if which == "H3" else fn() if fn else None
    if res is None:
        raise SystemExit("käyttö: q001.py H1|H2|H4  tai  q001.py H3 <kausi6.json>")
    print(json.dumps(res, ensure_ascii=False, indent=1))
