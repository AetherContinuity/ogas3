"""OGAS3 — YVA-menettely: ympäristövaikutusten arvioinnin vaiheet.

MIKSI
-----
YVA on ainoa julkinen lähde, jossa suuri uusi kuorma (datakeskus,
teollisuuslaitos, voimalaitos) näkyy ennen investointipäätöstä ja
ennen liittymäsopimusta. Fingridin liittymisjono ei ole julkinen;
YVA-menettely on. Siksi se on D-tapahtumien (uusi kuorma) paras lähde.

Se on ERI KANAVA kuin säädösvalmistelu: YVA-lausunnot menevät
yhteysviranomaiselle, eivät Lausuntopalveluun tai Hankeikkunaan. YVA-
hankkeilla ei ole HE-numeroa, joten ne eivät liity päätösketjuihin.

TAPAHTUMAT
----------
Jokainen hankesivun aikataulurivi, jonka vaihe tunnistetaan:

    ohjelma_nahtavilla     arviointiohjelma nähtävillä   = menettelyn alku
    ohjelma_lausunto       yhteysviranomaisen lausunto ohjelmasta
    selostus_nahtavilla    arviointiselostus nähtävillä
    perusteltu_paatelma    yhteysviranomaisen perusteltu päätelmä = loppu

    occurred_at = known_at = rivin päivä. Nähtävilläolo ja päätös
    kuulutetaan julkisesti, joten tieto on julkinen samana päivänä —
    sama perustelu kuin täysistunnossa. Tarkkuus on päivä.

Tyyppiä ei aseteta. Kaikki YVA-hankkeet eivät ole uutta sähkökuormaa
(turvetuotanto, kiviaines); `aihealue` kulkee mukana luokitusta varten.

KUORMA
------
Hankesivuja on ~790. Jokainen kaappaus hakee vain sivut, jotka voivat
muuttua: uudet, keskeneräiset ja yli 180 vrk sitten tarkistetut.
Tila säilytetään tiedostossa snapshots/yva-rekisteri.json. Ensimmäinen
ajo hakee kaikki kerran. max_pages rajaa ajon; loput siirtyvät
seuraavaan kuukauteen ja se kirjataan, ei niellä.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from fetchers import RawEvent

YVA_PROXY = "https://aci-yva-proxy.ruotsalainen-marko.workers.dev/"
REGISTRY = Path(__file__).resolve().parent / "snapshots" / "yva-rekisteri.json"
VAIHEET = ("ohjelma_nahtavilla", "ohjelma_lausunto", "selostus_nahtavilla", "perusteltu_paatelma")
REFRESH_DAYS = 180
SPACING_S = 1.0

Getter = Callable[[dict], dict]


class YvaError(RuntimeError):
    pass


def _get(params: dict) -> dict:
    url = YVA_PROXY + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "OGAS3/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise YvaError(f"yva-proxy HTTP {e.code}") from e
    if isinstance(d, dict) and d.get("error"):
        raise YvaError(f"yva-proxy: {d['error']}")
    time.sleep(SPACING_S)
    return d


def _closed(tila: str | None) -> bool:
    return bool(tila) and tila.lower().startswith("päättynyt")


def needs_fetch(slug: str, reg: dict, now: datetime) -> bool:
    r = reg.get(slug)
    if not r or not r.get("checked_at"):
        return True
    if not _closed(r.get("tila")):
        return True
    return now - datetime.fromisoformat(r["checked_at"]) > timedelta(days=REFRESH_DAYS)


def project_events(page: dict, slug: str, name: str, stats: dict | None = None) -> list[RawEvent]:
    """Tunnistetut, jo tapahtuneet vaiheet. Tulevaksi kuulutettu vaihe
    (päivä hakuhetken jälkeen) EI ole tapahtuma — se on odotus, sama
    periaate kuin tracen expected-solmuissa. Se lasketaan lokiin."""
    out = []
    retrieved = (page.get("fetched") or "").replace("Z", "+00:00")
    stats = stats if stats is not None else {}
    for a in page.get("aikataulu") or []:
        v = a.get("vaihe")
        if not a.get("alku"):
            continue
        if v not in VAIHEET:
            stats.setdefault("tunnistamattomat", []).append(a.get("text", "")[:120])
            continue
        if retrieved and a["alku"] > retrieved[:10]:
            stats["tulevia"] = stats.get("tulevia", 0) + 1
            continue
        ts = f"{a['alku']}T00:00:00+03:00"
        out.append(RawEvent(
            event_id=f"YVA:{slug}:{v}:{a['alku']}",
            occurred_at=ts, known_at=ts, retrieved_at=retrieved,
            source="YVA", source_url=page.get("url") or "",
            subtype=v,
            parameters={
                "slug": slug, "hanke": name, "tila": page.get("tila"),
                "aihealue": page.get("aihealue"), "alueet": page.get("alueet"),
                "asianumero": page.get("asianumero"), "julkaisija": page.get("julkaisija"),
                "vaihe": v, "loppu": a.get("loppu"), "asiakirjoja": page.get("n_documents"),
                "data_class": "authoritative (lakisääteinen YVA-menettely)",
            },
            evidence=[{"quote": a.get("text", "")[:300], "location": "YVA-menettelyn aikataulu",
                       "source_url": page.get("url") or "", "retrieved_at": retrieved}],
        ))
    return out


def capture(now: datetime | None = None, get: Getter = _get, registry: Path = REGISTRY,
            max_pages: int = 900) -> tuple[list[RawEvent], dict, dict]:
    """Palauttaa (tapahtumat, loki, päivitetty rekisteri). Rekisteriä ei
    kirjoiteta tässä — kutsuja päättää (kuivaharjoitus ei kirjoita)."""
    now = now or datetime.now(timezone.utc)
    reg = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {}
    idx = get({"index": "all"})
    projects = idx.get("data") or []
    # Järjestys: ensin koskaan tarkistamattomat (uudet hankkeet), sitten
    # keskeneräiset, lopuksi vanhentuneet päättyneet. Lykkäys osuu näin
    # vähiten muuttuviin.
    def prio(p):
        r = reg.get(p["slug"]) or {}
        return 0 if not r.get("checked_at") else 1 if not _closed(r.get("tila")) else 2
    todo = sorted((p for p in projects if needs_fetch(p["slug"], reg, now)), key=prio)
    deferred = todo[max_pages:]
    events: list[RawEvent] = []
    errors = []
    stats: dict = {}
    for p in todo[:max_pages]:
        try:
            page = get({"project": p["slug"]})
        except YvaError as exc:
            errors.append({"slug": p["slug"], "error": str(exc)[:200]})
            continue
        events.extend(project_events(page, p["slug"], p["name"], stats))
        reg[p["slug"]] = {"name": p["name"], "tila": page.get("tila"),
                          "aihealue": page.get("aihealue"),
                          "paivitetty": page.get("paivitetty") or page.get("julkaistu"),
                          "vaiheita": len([a for a in page.get("aikataulu") or [] if a.get("vaihe")]),
                          "checked_at": now.replace(microsecond=0).isoformat()}
    known = {p["slug"] for p in projects}
    for slug in reg:
        reg[slug]["hakemistossa"] = slug in known     # poistunut hanke: merkitään, ei poisteta
    log = {"source": "YVA", "hakemistossa": len(projects), "haettu": len(todo) - len(deferred),
           "lykatty_seuraavaan": len(deferred), "virheita": len(errors), "virheet": errors[:20],
           "tapahtumia": len(events),
           "tulevia_ohitettu": stats.get("tulevia", 0),
           "tunnistamattomia_riveja": len(stats.get("tunnistamattomat", [])),
           "tunnistamattomat_esimerkit": stats.get("tunnistamattomat", [])[:15],
           "vaiheettomia": sum(1 for p in todo[:max_pages] if reg.get(p["slug"], {}).get("vaiheita") == 0)}
    return events, log, reg


def write_registry(reg: dict, registry: Path = REGISTRY) -> None:
    registry.write_text(json.dumps(dict(sorted(reg.items())), ensure_ascii=False, indent=1), encoding="utf-8")
