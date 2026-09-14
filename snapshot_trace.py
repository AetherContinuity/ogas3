"""OGAS3 — Decision Trace: automaattinen snapshot.

traces.py LUKEE ja VALIDOI. Tämä KIRJOITTAA.

Molemmat TEM040-snapshotit koottiin käsin. Se oli noin viisikymmentä
riviä kerrallaan, ja `_supersedes`-ketju oli kirjoittajan muistin
varassa. Tämä poistaa sen.

PERIAATE: AUTOMAATTI EI TULKITSE
--------------------------------
Käsin kirjoitetuissa snapshoteissa `note`-kentät olivat proosaa:

    "Kaksi lähdettä, eri viive — Lausuntopalvelu näytti lausunnon
     heti, Hankeikkuna ei vielä."

Se on TIIVISTYS havainnosta. Havainto itse on:

    LAUSUNTO-asiakirjoja 0, etappi LAUSUNTOMENETTELY käynnissä
    13 vrk, lausuntoja muusta lähteestä >= 1

Jälkimmäinen on laskettavissa. Edellinen ei.

Siksi tämä moduuli kirjoittaa VAIN LASKETTUJA kenttiä. Jokainen
`_derived`-merkitty arvo on funktio hakutuloksesta. Proosaa ei
generoida — jos ihminen haluaa lisätä tulkinnan, hän lisää sen
erilliseen `_commentary`-kenttään joka EI vaikuta tiivisteeseen.

MIKSI NÄIN
----------
Automaatti joka kirjoittaa tulkintaa on huonompi kuin ei mitään:
se tuottaa uskottavaa tekstiä jota kukaan ei ole tarkistanut, ja
seuraava lukija ei erota sitä mitatusta. Sama vikaluokka kuin
`l_best = 0.0` -alkuarvo tai tyhjä 404 luettuna havainnoksi.

MITÄ TÄMÄ EI TEE
----------------
- Ei päätä mikä on merkittävää. Kaikki uusi kirjataan.
- Ei luokittele tapahtumatyyppiä (D/O/S/L/IR). Se on Extractorin työ.
- Ei täytä `expected`-listaa. Se on ihmisen päätös siitä mitä
  odotetaan; automaatti vain KANTAA sen edellisestä snapshotista
  ja poistaa ne jotka ovat toteutuneet.
- Ei koskaan muuta edellistä snapshotia.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROXY = "https://aci-policy-proxy.ruotsalainen-marko.workers.dev"
SCHEMA = "aci/decision-trace/v0.1"


# ── haku ────────────────────────────────────────────────────────────

def fetch_hankeikkuna(tunnus: str, tries: int = 3) -> dict:
    """Hakee kohteen. 429 uusitaan, muut virheet nostetaan heti."""
    body = json.dumps({"tunnus": [tunnus], "size": 1}).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(
                f"{PROXY}/?hi=kohteet/haku", data=body,
                headers={"Content-Type": "application/json",
                         "User-Agent": "aci-ogas3/1.0"})
            d = json.loads(urllib.request.urlopen(req, timeout=90).read())
            if "error" in d:
                raise RuntimeError(d["error"])
            res = (d.get("data") or {}).get("result") or []
            if not res:
                raise RuntimeError(f"{tunnus}: ei osumia")
            return res[0]
        except Exception as e:
            # 429 on ohimenevä; muut eivät parane odottamalla.
            if "429" in str(e) and i < tries - 1:
                time.sleep(6 * (i + 1))
                continue
            raise


# ── solmujen muodostus — VAIN LASKETTUA ─────────────────────────────

def _iso(d: str | None) -> str | None:
    """Päivä -> ISO aikaleima Suomen ajassa. None säilyy None:na.

    EI keksi päivää jos sitä ei ole. Puuttuva occurred_at tarkoittaa
    ettei solmua voi kirjata havaintona.
    """
    if not d:
        return None
    return f"{d[:10]}T00:00:00+03:00"


def nodes_from_kohde(kohde: dict, retrieved_at: str) -> list[dict]:
    """Hanke asetettu -solmu.

    HUOM: `asettamisPaiva` puuttuu useimmista hankkeista. Silloin
    käytetään `aloitusPaiva`, ja `occurred_at_source` kertoo kumpi se
    on. Ne ovat ERI KENTTIÄ eri semantiikalla, eikä sitä saa piilottaa.
    """
    pv = kohde.get("asettamisPaiva") or kohde.get("aloitusPaiva")
    if not pv:
        return []
    return [{
        "node_id": "hanke-asetettu",
        "kind": "observed",
        "occurred_at": _iso(pv),
        "occurred_at_source": ("asettamisPaiva" if kohde.get("asettamisPaiva")
                               else "aloitusPaiva"),
        "known_at": _iso((kohde.get("julkaisuaika") or "")[:10]) or None,
        "retrieved_at": retrieved_at,
        "source": "Hankeikkuna kohteet/haku",
        "evidence": [{
            "quote": (kohde.get("nimi") or {}).get("fi") or kohde.get("tunnus"),
            "location": f"kohde {kohde.get('tunnus')}",
            "source_url": "https://api.hankeikkuna.fi/api/v2/kohteet/haku",
            "retrieved_at": retrieved_at,
        }],
        "_derived": {"asettamisPaiva_puuttuu": kohde.get("asettamisPaiva") is None},
    }]


def nodes_from_etapit(etapit: list, retrieved_at: str, today: str) -> list[dict]:
    out = []
    for e in etapit or []:
        if not e.get("alku"):
            continue
        vaihe = e.get("valmisteluvaihe") or "ETAPPI"
        nid = f"etappi-{vaihe.lower()}-{e['alku'][:10]}"
        kesto = None
        if e.get("alku"):
            try:
                a = datetime.fromisoformat(e["alku"][:10])
                kesto = (datetime.fromisoformat(today) - a).days
            except Exception:
                pass
        out.append({
            "node_id": nid,
            "kind": "observed",
            "occurred_at": _iso(e["alku"]),
            "known_at": _iso(e["alku"]),
            "retrieved_at": retrieved_at,
            "source": "Hankeikkuna etapit",
            "evidence": [{
                "quote": f"{vaihe} {e.get('alku','')[:10]} – {e.get('loppu','')[:10]}",
                "location": "etapit",
                "source_url": "https://api.hankeikkuna.fi/api/v2/kohteet/haku",
                "retrieved_at": retrieved_at,
            }],
            "_derived": {
                "vaihe": e.get("vaihe"),
                "loppu": (e.get("loppu") or "")[:10] or None,
                "kesto_vrk": kesto,
            },
        })
    return out


def nodes_from_asiakirjat(asiakirjat: list, retrieved_at: str) -> list[dict]:
    out = []
    for x in asiakirjat or []:
        if not x.get("laatimispaiva") or not x.get("uuid"):
            continue
        nimi = (x.get("nimi") or {}).get("fi")
        if not nimi:            # nimetön duplikaatti — ohitetaan
            continue
        out.append({
            "node_id": f"asiakirja-{x['uuid'][:8]}",
            "kind": "observed",
            "occurred_at": _iso(x["laatimispaiva"]),
            "known_at": _iso((x.get("luotu") or "")[:10]) or None,
            "retrieved_at": retrieved_at,
            "source": "Hankeikkuna asiakirjat",
            "doc_type": x.get("tyyppi"),
            "evidence": [{
                "quote": nimi,
                "location": f"asiakirjat · uuid {x['uuid']}",
                "source_url": x.get("url") or "",
                "retrieved_at": retrieved_at,
            }],
            "_derived": {"laatija": (x.get("laatija") or {}).get("fi")},
        })
    return out


def derive_state(kohde: dict, etapit: list, asiakirjat: list,
                 today: str) -> dict:
    """Laskettu tila. EI proosaa.

    Jokainen kenttä on funktio hakutuloksesta. Se mikä käsin
    kirjoitetussa snapshotissa oli lause ("kaksi lähdettä, eri viive")
    on tässä kolme lukua joista lukija tekee saman päätelmän itse.
    """
    tyypit: dict[str, int] = {}
    for x in asiakirjat or []:
        t = x.get("tyyppi") or "?"
        tyypit[t] = tyypit.get(t, 0) + 1

    lausunto_kierros = None
    for e in etapit or []:
        if (e.get("valmisteluvaihe") or "").upper() == "LAUSUNTOMENETTELY":
            lausunto_kierros = e
            break

    auki_vrk = None
    jaljella_vrk = None
    if lausunto_kierros:
        try:
            t0 = datetime.fromisoformat(today)
            if lausunto_kierros.get("alku"):
                auki_vrk = (t0 - datetime.fromisoformat(
                    lausunto_kierros["alku"][:10])).days
            if lausunto_kierros.get("loppu"):
                jaljella_vrk = (datetime.fromisoformat(
                    lausunto_kierros["loppu"][:10]) - t0).days
        except Exception:
            pass

    return {
        "tila": kohde.get("tila"),
        "asiakirjat_yhteensa": len(asiakirjat or []),
        "asiakirjat_tyypeittain": tyypit,
        "lausuntoja_hankeikkunassa": tyypit.get("LAUSUNTO", 0),
        "lausuntokierros_auki_vrk": auki_vrk,
        "lausuntokierros_jaljella_vrk": jaljella_vrk,
        "_lausuntoja_note": (
            "Luku on Hankeikkunan asiakirjoista. TEM: Lausuntopalvelussa "
            "annetut nakyvat automaattisesti, kirjaamoon toimitettuja EI "
            "julkaista. Havaittu maara on siis ALARAJA, ei kokonaismaara."),
        "uptake": None,
        "_uptake_note": (
            "MAARITTAMATON, ei nolla. Mitattavissa vasta taysistunnon "
            "aanestyksesta, ja aanestystyyppi on luokiteltava erikseen."),
    }


# ── snapshot ────────────────────────────────────────────────────────

def make_snapshot(tunnus: str, outdir: str | Path,
                  today: str | None = None,
                  prev_path: str | Path | None = None,
                  subject_extra: dict | None = None) -> tuple[Path, dict]:
    """Hakee, vertaa edelliseen ja kirjoittaa uuden lukitun snapshotin.

    EDELLISTA EI MUUTETA KOSKAAN. Uusi tiedosto, `_supersedes` viittaa
    edelliseen tiivisteineen.
    """
    today = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    retrieved_at = datetime.now(timezone.utc).replace(
        microsecond=0).isoformat()
    outdir = Path(outdir)

    r = fetch_hankeikkuna(tunnus)
    kohde = r.get("kohde") or {}
    etapit = r.get("etapit") or []
    asiakirjat = r.get("asiakirjat") or []

    nodes = (nodes_from_kohde(kohde, retrieved_at)
             + nodes_from_etapit(etapit, retrieved_at, today)
             + nodes_from_asiakirjat(asiakirjat, retrieved_at))

    prev = None
    if prev_path and Path(prev_path).exists():
        prev = json.loads(Path(prev_path).read_text(encoding="utf-8"))

    # uudet solmut = ne joita edellisessä ei ollut
    prev_ids = {n["node_id"] for n in (prev or {}).get("observed", [])}
    uudet = [n["node_id"] for n in nodes if n["node_id"] not in prev_ids]
    # kadonneet: jos lähde poistaa jotain, se on OMA havaintonsa
    kadonneet = sorted(prev_ids - {n["node_id"] for n in nodes})

    # expected kannetaan edellisestä; toteutuneet poistetaan
    expected = list((prev or {}).get("expected", []))
    if expected:
        toteutunut_ids = {n["node_id"] for n in nodes}
        expected = [e for e in expected
                    if e.get("_fulfilled_by") not in toteutunut_ids]

    snap: dict[str, Any] = {
        "_schema": SCHEMA,
        "_locked_at": today,
        "_revision": 1,
        "_generator": "snapshot.py (automaattinen) — EI tulkintaa, vain "
                      "laskettuja kenttia. Proosa kuuluu _commentary-kenttaan "
                      "jonka ihminen lisaa ja joka EI vaikuta tiivisteeseen.",
        "_lock_note": "LUKITTU. Ei muuteta jalkikateen; uudet havainnot "
                      "seuraavaan snapshotiin.",
        "subject": {
            "tunnus": kohde.get("tunnus"),
            "asianumero": (kohde.get("asianumerot") or [None])[0],
            "nimi": (kohde.get("nimi") or {}).get("fi"),
            **(subject_extra or {}),
        },
        "_state": derive_state(kohde, etapit, asiakirjat, today),
        "_diff": {
            "edellinen": (str(Path(prev_path).name) if prev_path and prev
                          else None),
            "uusia_solmuja": len(uudet),
            "uudet": uudet,
            "kadonneita": len(kadonneet),
            "kadonneet": kadonneet,
            "_kadonneet_note": (
                "Solmu joka oli edellisessa muttei tassa. EI poisteta "
                "hiljaa — lahde on muuttunut, ja se on oma havaintonsa.\n"
                "HUOM KAKSI VAARAA HALYTYSTA:\n"
                "(1) KASIN kirjatut solmut joita Hankeikkuna ei tunne "
                "(esim. oma lausunto ennen kuin se nakyy asiakirjoissa) "
                "nakyvat AINA kadonneina. Ne eivat ole kadonneet — "
                "automaatti ei vain nae niita.\n"
                "(2) NIMEAMISERO: kasin kirjatut kayttivat vapaita "
                "node_id-arvoja (esim. 'lausuntokierros-alkoi'), automaatti "
                "kayttaa kaavaa 'etappi-<vaihe>-<pvm>'. Sama tapahtuma, eri "
                "tunniste. Ensimmainen automaattiajo kasin kirjoitetun "
                "snapshotin paalle raportoi siksi kadonneita joita ei ole.\n"
                "Kumpikin nakyy VAIN ensimmaisella ajolla; sen jalkeen "
                "tunnisteet ovat yhtenaiset."),
        },
        "observed": nodes,
        "_expected_note": "Eivat ole tapahtumia. Ei aikaleimoja. "
                          "Automaatti EI lisaa naita — se vain kantaa ne "
                          "edellisesta ja poistaa toteutuneet.",
        "expected": expected,
    }
    if prev:
        snap["_supersedes"] = {
            "file": Path(prev_path).name,
            "content_hash": prev.get("_content_hash"),
            "locked_at": prev.get("_locked_at"),
        }

    blob = json.dumps({k: v for k, v in snap.items()
                       if k not in ("_content_hash", "_commentary")},
                      ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))
    snap["_content_hash"] = hashlib.sha256(blob.encode()).hexdigest()[:12]

    outdir.mkdir(parents=True, exist_ok=True)
    p = outdir / f"{tunnus.replace(':', '').replace('/', '-')}-trace-{today}.json"
    p.write_text(json.dumps(snap, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    return p, snap
