"""OGAS3 — vahti: nimettyjen asioiden ilmaantuminen julkisiin lähteisiin.

Kuukausikaappaus seuraa päätösketjuja, joilla on jo hanke tai HE-numero.
Vahti seuraa asioita, joilla sitä EI vielä ole: luvattua selvitystä,
odotettua päätöstä, suunnitelmaa jolle on annettu määräaika. Kysymys on
"onko tämä ilmestynyt", ei "miten tämä eteni".

MITÄ VAHTI KIRJAA
-----------------
Jokaiselle vahdille kaksi havaintolajia:

    hakusana      Hankeikkunan tekstihaku. Kirjataan osumien tunnukset.
                  Uusi tunnus = hanke, jota ei edellisessä ajossa ollut.
    hanke         Nimetyn hankkeen asiakirjat. Uusi asiakirja = uuid,
                  jota ei edellisessä ajossa ollut.

Edellinen tila on rekisterissä snapshots/vahti-rekisteri.json (sama malli
kuin yva-rekisteri.json). Kuivaharjoitus ei kirjoita rekisteriä.

MITÄ VAHTI EI OLE
-----------------
Vahti ei tuota tapahtumia (events) eikä vaikuta ketjuihin tai lukuihin
totals.events. Se on oma lohkonsa snapshotissa. Tyhjä tulos tarkoittaa
"ei ilmestynyt hakusanalla", ei "ei ole olemassa": asia voi olla
valmisteilla eri nimellä tai kokonaan Hankeikkunan ulkopuolella
(virastojen omat selvitykset, kehyspäätökset, varautumissuunnitelmat).

ANSAT
-----
- kohteet/haku palauttaa oletuksena 10 riviä; size on annettava.
- teksti-haku ei taivuta: "raideleveys" ja "raideleveyden" ovat eri haut.
- tunnus-kenttä on LISTA; merkkijono palauttaa 400.
- Haun virhe kirjataan eikä tyhjennä rekisteriä: epäonnistunut haku ei
  saa näyttää siltä, että osumat katosivat ja palasivat "uusina".
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from fetchers import POLICY_PROXY, _post

REGISTRY = Path(__file__).resolve().parent / "snapshots" / "vahti-rekisteri.json"
SCHEMA = "aci/ogas3-vahti/v0.1"
SIZE = 200

# Vahdit. Lisäys on uusi alkio; olemassa olevan id:tä ei muuteta, koska
# rekisteri ja aikasarja avaimoituvat siihen.
WATCHES: list[dict] = [
    {
        "id": "lansireitti-tavoite",
        "lisatty": "2026-10-05",
        "kuvaus": "Asetetaanko länsireitin (Haaparanta/Tornio) kuljetuskapasiteetille "
                  "määrällinen tavoite. VNp 568/2024 velvoittaa laadullisesti, ei lukuna.",
        "lahde": "CN-030 luku 7",
        "hakusanat": ["huoltovarmuuden tavoitteista", "vaihtoehtoiset kuljetusreitit",
                      "kuljetusten jatkuvuus"],
        "hankkeet": [],
    },
    {
        "id": "raideleveys-siirtyma",
        "lisatty": "2026-10-05",
        "kuvaus": "Raideleveyden kansallinen siirtymäsuunnitelma komissiolle (määräaika 6/2027) "
                  "ja sen välivaiheen toimet. LVM:n kirje 29.7.2026 on Liikenne 12 -hankkeessa.",
        "lahde": "CN-030 luku 7",
        "hakusanat": ["raideleveys", "raideleveyden", "raideleveyteen", "Rail Nordica"],
        "hankkeet": ["LVM029:00/2023"],
    },
    {
        "id": "raidekalusto-selvitys",
        "lisatty": "2026-10-05",
        "kuvaus": "Liikenne 12 -selonteon kirjaus: valtio selvittää raideliikennekaluston "
                  "kehittämisen sotilaallisiin vaatimuksiin kaksikäyttöisyys huomioiden. "
                  "Julkaistaanko selvitys.",
        "lahde": "CN-030 luku 7",
        "hakusanat": ["raideliikennekaluston", "raidekalusto", "sotilaallinen liikkuvuus",
                      "sotilaallisen liikkuvuuden"],
        "hankkeet": [],
    },
]

Poster = Callable[[str, dict], dict]


def _fi(x) -> str:
    return ((x.get("fi") if isinstance(x, dict) else x) or "") if x is not None else ""


def _rows(j: dict) -> tuple[list[dict], int | None]:
    data = j.get("data")
    rows = (data.get("result") if isinstance(data, dict) else data) or j.get("result") or []
    return rows, j.get("totalHits")


def _search(post: Poster, body: dict) -> tuple[list[dict], int | None]:
    j = post(f"{POLICY_PROXY}/?hi=kohteet/haku", {"size": SIZE, **body})
    if "error" in j:
        raise RuntimeError(str(j["error"])[:200])
    return _rows(j)


def _hit(row: dict) -> dict:
    k = row.get("kohde") or {}
    return {"tunnus": k.get("tunnus") or k.get("uuid"), "nimi": _fi(k.get("nimi"))[:200],
            "tyyppi": k.get("tyyppi"), "tila": k.get("tila"),
            "valmisteluvaihe": k.get("valmisteluvaihe")}


def _doc(a: dict) -> dict:
    return {"uuid": a.get("uuid"), "tyyppi": a.get("tyyppi"),
            "pvm": str(a.get("laatimispaiva") or a.get("luotu") or "")[:10],
            "laatija": _fi(a.get("laatija"))[:80], "nimi": _fi(a.get("nimi"))[:200]}


def capture(now: datetime | None = None, post: Poster = _post, registry: Path = REGISTRY,
            watches: list[dict] | None = None) -> tuple[dict, dict, dict]:
    """Palauttaa (lohko snapshotiin, loki, päivitetty rekisteri). Rekisteriä
    ei kirjoiteta tässä — kutsuja päättää (kuivaharjoitus ei kirjoita)."""
    now = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    watches = WATCHES if watches is None else watches
    reg = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {}
    new_reg = json.loads(json.dumps(reg))
    out, n_err, n_new = [], 0, 0

    for w in watches:
        prev = reg.get(w["id"])            # None = vahdin ensimmäinen ajo
        cur = {"hakusanat": dict((prev or {}).get("hakusanat") or {}),
               "hankkeet": dict((prev or {}).get("hankkeet") or {})}
        haut, hankkeet = [], []

        for term in w.get("hakusanat") or []:
            try:
                rows, total = _search(post, {"teksti": term})
            except Exception as exc:
                n_err += 1
                haut.append({"teksti": term, "error": str(exc)[:200]})
                continue                    # rekisterin vanha tila säilyy
            hits = [_hit(r) for r in rows]
            seen = set((prev or {}).get("hakusanat", {}).get(term) or []) if prev else None
            uudet = None if seen is None or term not in (prev or {}).get("hakusanat", {}) \
                else [h for h in hits if h["tunnus"] not in seen]
            n_new += len(uudet or [])
            haut.append({"teksti": term, "totalHits": total, "osumia": len(hits),
                         "katkaistu": bool(total and total > len(hits)),
                         "uudet": uudet, "tunnukset": sorted(h["tunnus"] for h in hits if h["tunnus"])})
            cur["hakusanat"][term] = sorted(h["tunnus"] for h in hits if h["tunnus"])

        for tunnus in w.get("hankkeet") or []:
            try:
                rows, _ = _search(post, {"tunnus": [tunnus]})
                row = next((r for r in rows if (r.get("kohde") or {}).get("tunnus") == tunnus), None)
                if row is None:
                    raise RuntimeError("hanketta ei löytynyt tunnuksella")
            except Exception as exc:
                n_err += 1
                hankkeet.append({"tunnus": tunnus, "error": str(exc)[:200]})
                continue
            docs = [_doc(a) for a in (row.get("asiakirjat") or []) if a.get("uuid")]
            known = (prev or {}).get("hankkeet", {}).get(tunnus)
            uudet = None if known is None else [d for d in docs if d["uuid"] not in set(known)]
            n_new += len(uudet or [])
            k = row.get("kohde") or {}
            hankkeet.append({"tunnus": tunnus, "tila": k.get("tila"),
                             "valmisteluvaihe": k.get("valmisteluvaihe"),
                             "asiakirjoja": len(docs), "uudet_asiakirjat": uudet})
            cur["hankkeet"][tunnus] = sorted(d["uuid"] for d in docs)

        out.append({"id": w["id"], "kuvaus": w["kuvaus"], "lahde": w.get("lahde"),
                    "lisatty": w.get("lisatty"), "ensimmainen_ajo": prev is None,
                    "haut": haut, "hankkeet": hankkeet})
        new_reg[w["id"]] = {**cur, "paivitetty": now.isoformat()}

    block = {"_schema": SCHEMA, "captured_at": now.isoformat(),
             "_note": "uudet = null tarkoittaa lähtötilaa (ei vertailukohtaa), [] ei uusia. "
                      "Tyhjä haku ei todista, ettei asiaa ole.",
             "watches": out}
    log = {"source": "Vahti", "vahteja": len(out), "uusia": n_new,
           **({"error": f"{n_err} hakua epäonnistui"} if n_err else {})}
    return block, log, new_reg


def summarize(block: dict | None) -> dict | None:
    """Tiivistelmä käyttöliittymälle: vain se, mikä muuttui tai puuttuu."""
    if not block:
        return None
    rows = []
    for w in block.get("watches") or []:
        uudet_h = [h for q in w.get("haut") or [] for h in (q.get("uudet") or [])]
        uniq = list({h["tunnus"]: h for h in uudet_h}.values())
        uudet_a = [{"hanke": h["tunnus"], **d} for h in w.get("hankkeet") or []
                   for d in (h.get("uudet_asiakirjat") or [])]
        virheet = [q.get("teksti") or q.get("tunnus")
                   for q in (w.get("haut") or []) + (w.get("hankkeet") or []) if q.get("error")]
        rows.append({"id": w["id"], "kuvaus": w["kuvaus"], "lahtotila": bool(w.get("ensimmainen_ajo")),
                     "uudet_hankkeet": sorted(uniq, key=lambda h: h["tunnus"] or ""),
                     "uudet_asiakirjat": sorted(uudet_a, key=lambda d: (d["pvm"], d["uuid"] or "")),
                     "virheet": virheet})
    return {"_note": "Vahti kertoo, mitä ilmestyi edellisen ajon jälkeen. Hiljaisuus ei ole havainto.",
            "captured_at": block.get("captured_at"), "watches": rows}


def write_registry(reg: dict, registry: Path = REGISTRY) -> None:
    registry.write_text(json.dumps(dict(sorted(reg.items())), ensure_ascii=False, indent=1),
                        encoding="utf-8")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="kirjoita rekisteri (lähtötilan kaappaus)")
    a = ap.parse_args()
    b, l, r = capture()
    print(json.dumps(summarize(b), ensure_ascii=False, indent=1))
    print(l)
    if a.write:
        write_registry(r)
        print("rekisteri kirjoitettu:", REGISTRY)
