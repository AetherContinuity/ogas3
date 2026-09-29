"""OGAS3 — päätösketjun loppupää: täysistuntoäänestykset ja säädökset.

MIKSI
-----
Kuukausikaappaus näki tähän asti ketjun alun (Hankeikkuna: valmistelu,
lausunnot) ja keskivaiheen (Eduskunta: käsittelyvaiheet). Loppupää
puuttui: äänestettiinkö, ja tuliko laiksi. Ilman sitä L-tapahtumien
uptakea ei voi edes periaatteessa mitata, ja IR-ehdokkaita ei ole.

Kaksi lähdettä, molemmat data_class = authoritative:

  Eduskunta äänestykset   ?votes=<HE n/vvvv vp>
      occurred_at = aanestysalkuaika
      known_at    = sama. Täysistunto on julkinen tapahtuma.

  Finlex säädökset         ?fx=akn/fi/act/statute/<vvvv>/<n>/fin@
      occurred_at = dateIssued     (vahvistuspäivä)
      known_at    = datePublished  (säädöskokoelmassa)
      Esityöt-osio (preliminaryWork) antaa HE-numeron, valiokunnan
      mietinnön ja eduskunnan vastauksen (EV). HE-numero on liitosavain
      Hankeikkunan heTiedot.heNumerot-kenttään ja äänestyksiin.

MITÄ TÄMÄ EI TEE
----------------
Ei luokittele. Säädös ei ole automaattisesti IR: useimmat muutoslait
ovat peruttavissa seuraavalla muutoksella. Äänestys ei ole
automaattisesti lausunnon uptake: se mittaa esityksen menestystä, ei
yksittäisen lausunnon. Molemmat ovat SYÖTE luokitukselle, eivät
luokitus. type jää None-arvoksi kuten muissakin kaappauksissa.

KOLME TILAA JOTKA EIVÄT OLE SAMA ASIA
-------------------------------------
Äänestysreitti palauttaa 404 sekä olemattomalle HE:lle että esitykselle,
joka hyväksyttiin ilman äänestystä tai jota ei ole vielä käsitelty.
404 ei siis ole "ei äänestetty" eikä "hylätty". Ketjun lopputulos
päätellään lähteiden YHDISTELMÄSTÄ, ja kun se ei ratkea, se on
`määrittämätön` — ei nolla, ei hylätty.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Callable, Iterable

from fetchers import POLICY_PROXY, RawEvent, _now_iso

AKN = "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}"
FINLEX = "{http://data.finlex.fi/schema/finlex}"

SPACING_S = 1.0          # proxyn käyttöehtojen mukainen tauko kutsujen välillä
HE_RE = re.compile(r"\bHE\s+(\d+)\s*/\s*(\d{4})\b")
EV_RE = re.compile(r"\bEV\s+(\d+)\s*/\s*(\d{4})\b")
MIETINTO_RE = re.compile(r"\b([A-ZÄÖ][A-Za-zÄÖäö]*VM)\s+(\d+)\s*/\s*(\d{4})\b")


class ChainError(RuntimeError):
    pass


def he_key(s: str) -> str | None:
    """Normalisoi 'HE 51/2026', 'HE 51/2026 vp' ja välilyöntivaihtelut -> 'HE 51/2026'."""
    m = HE_RE.search(s or "")
    return f"HE {int(m.group(1))}/{m.group(2)}" if m else None


# ── Haku ─────────────────────────────────────────────────────────────
Getter = Callable[[str], tuple[int, bytes]]


def _http_get(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "OGAS3/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _proxy(params: dict) -> str:
    return f"{POLICY_PROXY}/?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


# ── Finlex ───────────────────────────────────────────────────────────
@dataclass(frozen=True)
class StatuteMeta:
    year: int
    number: int
    title: str
    date_issued: str | None
    date_published: str | None
    type_statute: str | None
    category_statute: str | None
    author: str | None       # EI käytetä: Finlex merkitsee eduskunnan myös asetuksille
    he: tuple[str, ...]
    mietinnot: tuple[str, ...]
    ev: tuple[str, ...]
    eli: str | None


def parse_statute(xml: bytes | str) -> StatuteMeta:
    root = ET.fromstring(xml)
    work = root.find(f".//{AKN}FRBRWork")
    if work is None:
        raise ChainError("FRBRWork puuttuu — ei Akoma Ntoso -säädös")
    dates = {d.get("name"): d.get("date") for d in work.findall(f"{AKN}FRBRdate")}
    uri = (work.find(f"{AKN}FRBRuri").get("value") if work.find(f"{AKN}FRBRuri") is not None else "")
    m = re.search(r"/statute/(\d{4})/(\d+)", uri)
    if not m:
        raise ChainError(f"säädöstunnus ei jäsenny: {uri!r}")
    author = work.find(f"{AKN}FRBRauthor")
    eli = next((a.get("value") for a in work.findall(f"{AKN}FRBRalias") if a.get("name") == "eli"), None)
    title_el = root.find(f".//{AKN}docTitle")
    title = "".join(title_el.itertext()).strip() if title_el is not None else ""

    def _ref(tag: str) -> str | None:
        el = root.find(f".//{FINLEX}{tag}")
        return (el.get("refersTo") or "").lstrip("#") or None if el is not None else None

    # Esityöt. Vain preliminaryWork-osiosta: muualla tekstissä HE-viittaus
    # voi olla viittaus TOISEN lain esitöihin.
    he, mie, ev = [], [], []
    for hc in root.iter(f"{AKN}hcontainer"):
        if hc.get("name") != "preliminaryWork":
            continue
        text = " ".join(" ".join(p.itertext()) for p in hc.iter(f"{AKN}p"))
        he += [f"HE {int(a)}/{b}" for a, b in HE_RE.findall(text)]
        ev += [f"EV {int(a)}/{b}" for a, b in EV_RE.findall(text)]
        mie += [f"{a} {int(b)}/{c}" for a, b, c in MIETINTO_RE.findall(text)]
    uniq = lambda xs: tuple(dict.fromkeys(xs))
    return StatuteMeta(
        year=int(m.group(1)), number=int(m.group(2)), title=title,
        date_issued=dates.get("dateIssued"), date_published=dates.get("datePublished"),
        type_statute=_ref("typeStatute"), category_statute=_ref("categoryStatute"),
        author=(author.get("href") or "").lstrip("#") or None if author is not None else None,
        he=uniq(he), mietinnot=uniq(mie), ev=uniq(ev), eli=eli,
    )


def statute_event(meta: StatuteMeta, source_url: str, retrieved_at: str) -> RawEvent:
    occ = f"{meta.date_issued}T00:00:00+03:00" if meta.date_issued else None
    kno = f"{meta.date_published}T00:00:00+03:00" if meta.date_published else None
    anomaly = None
    if not occ or not kno:
        anomaly = "dateIssued tai datePublished puuttuu"
    elif kno < occ:
        anomaly = f"datePublished {meta.date_published} ennen dateIssued {meta.date_issued}"
    return RawEvent(
        event_id=f"FX:{meta.year}/{meta.number}",
        occurred_at=occ, known_at=kno, retrieved_at=retrieved_at,
        source="Finlex", source_url=source_url,
        subtype=meta.type_statute,
        parameters={
            "saados": f"{meta.number}/{meta.year}",
            "nimeke": meta.title,
            "category": meta.category_statute,
            "heNumerot": list(meta.he),
            "mietinnot": list(meta.mietinnot),
            "ev": list(meta.ev),
            "eli": meta.eli,
            "data_class": "authoritative",
        },
        evidence=[{"quote": f"{meta.number}/{meta.year} {meta.title}"[:300],
                   "location": "preface/docTitle",
                   "source_url": source_url, "retrieved_at": retrieved_at}],
        anomaly=anomaly,
    )


def fetch_statute(year: int, number: int, get: Getter = _http_get) -> tuple[StatuteMeta | None, str, str]:
    """Palauttaa (meta | None, url, retrieved_at). None = säädöstä ei ole (404).

    Muut virheet nostetaan: 404 on havainto numeroinnin päättymisestä,
    500 tai rikkinäinen XML ei ole.
    """
    url = _proxy({"fx": f"akn/fi/act/statute/{year}/{number}/fin@"})
    status, body = get(url)
    ts = _now_iso()
    time.sleep(SPACING_S) if get is _http_get else None
    if status == 200 and body.lstrip().startswith(b"<"):
        return parse_statute(body), url, ts
    text = body.decode("utf-8", "replace")
    if status == 404 or '": 404' in text or " 404 " in text:
        return None, url, ts
    if status == 429 or "429" in text[:200]:
        raise ChainError(f"Finlex 429 säädöksessä {number}/{year} — lopetetaan, ei uusita")
    raise ChainError(f"Finlex {number}/{year}: HTTP {status} {text[:200]}")


def statutes_published_between(start: date, end: date, get: Getter = _http_get,
                               max_calls: int = 400) -> tuple[list[RawEvent], dict]:
    """Säädökset joiden datePublished on välillä [start, end).

    Numerointi on vuosikohtaisesti juokseva ja julkaisujärjestys lähes
    sama kuin numerojärjestys, mutta EI täsmälleen. Siksi:
      1. binäärihaku ensimmäiseen numeroon jonka datePublished >= start
      2. taaksepäin 20 numeron marginaali
      3. eteenpäin kunnes 15 peräkkäistä on joko yli rajan tai puuttuu
    Rajatapaukset kirjataan lokiin. max_calls katkaisee — ja katkaisu
    kirjataan, sitä ei niellä.
    """
    if start.year != end.year and not (end.year == start.year + 1 and end.month == 1 and end.day == 1):
        raise ChainError("ikkunan on oltava saman vuoden sisällä")
    year = start.year
    cache: dict[int, tuple[StatuteMeta | None, str, str]] = {}
    calls = 0

    def meta(n: int):
        nonlocal calls
        if n not in cache:
            if calls >= max_calls:
                raise ChainError(f"max_calls {max_calls} täyttyi numerossa {n}")
            calls += 1
            cache[n] = fetch_statute(year, n, get)
        return cache[n]

    def pub(n: int) -> date | None:
        m = meta(n)[0]
        return date.fromisoformat(m.date_published) if m and m.date_published else None

    # Yläraja: eksponentiaalinen haku ensimmäiseen puuttuvaan.
    hi = 64
    while pub(hi) is not None:
        hi *= 2
        if hi > 20000:
            raise ChainError("numerointi ei pääty — jäsennys rikki?")
    lo = 1
    # Binäärihaku: ensimmäinen n jolle pub(n) >= start tai puuttuu.
    a, b = lo, hi
    while a < b:
        mid = (a + b) // 2
        p = pub(mid)
        if p is None or p >= start:
            b = mid
        else:
            a = mid + 1
    first = a

    out: list[RawEvent] = []
    for n in range(max(1, first - 20), first):
        m, url, ts = meta(n)
        if m and m.date_published and start <= date.fromisoformat(m.date_published) < end:
            out.append(statute_event(m, url, ts))
    n, streak, missing, last_in = first, 0, 0, None
    while streak < 15:
        m, url, ts = meta(n)
        if m is None:
            missing += 1
            streak += 1
        else:
            p = date.fromisoformat(m.date_published) if m.date_published else None
            if p is not None and start <= p < end:
                out.append(statute_event(m, url, ts))
                streak, last_in = 0, n
            elif p is not None and p >= end:
                streak += 1
            else:
                streak = 0          # vanha numero myöhässä ikkunan jälkeen — jatketaan
        n += 1
    log = {"source": "Finlex", "window": [start.isoformat(), end.isoformat()],
           "first_number": first, "last_number_in_window": last_in,
           "calls": calls, "missing_numbers_seen": missing, "n": len(out)}
    return sorted(out, key=lambda e: int(e.event_id.split("/")[1])), log


# ── Äänestykset ──────────────────────────────────────────────────────
def _jakauma(rows: Any) -> list[dict]:
    """Ryhmäjakauma tiiviinä. Kansanedustajakohtaiset rivit jätetään pois:
    ne ovat henkilötietoa eikä kuukausisarja tarvitse niitä."""
    return [{"nimi": ((g.get("nimi") or {}).get("fi")),
             **{k: g.get(k) for k in ("jaa", "ei", "tyhjia", "poissa")}}
            for g in (rows or [])]


def vote_events(resp: dict, he: str, source_url: str, retrieved_at: str) -> list[RawEvent]:
    out = []
    for v in resp.get("data") or []:
        t = v.get("aanestysalkuaika")
        tulos = v.get("aanestystulos") or {}
        otsikko = ((v.get("aanestysotsikko") or {}).get("fi") or "").strip()
        out.append(RawEvent(
            event_id=f"VOTE:{v.get('id')}",
            occurred_at=t, known_at=t, retrieved_at=retrieved_at,
            source="Eduskunta äänestys", source_url=source_url,
            subtype=v.get("_vote_kind"),
            parameters={
                "eduskuntatunnus": he,
                "istunto": v.get("istunnonTunniste"),
                "aanestysnumero": v.get("aanestysnumero"),
                "otsikko": otsikko,
                "jaa": tulos.get("jaa"), "ei": tulos.get("ei"),
                "tyhjia": tulos.get("tyhjia"), "poissa": tulos.get("poissa"),
                "mitatoity": v.get("aanestysmitatoity"),
                "uptake_usable": v.get("_uptake_usable"),
                "party_line": v.get("_party_line"),
                "uptake_note": v.get("_uptake_note"),
                "eduskuntaryhmat": _jakauma(v.get("eduskuntaryhmaJakaumat")),
                "hallitus_oppositio": _jakauma(v.get("hallitusoppositioJakaumat")),
                "data_class": "authoritative",
            },
            evidence=[{"quote": f"{otsikko} — jaa {tulos.get('jaa')}, ei {tulos.get('ei')}"[:300],
                       "location": f"täysistunto {v.get('istunnonTunniste')}, äänestys {v.get('aanestysnumero')}",
                       "source_url": source_url, "retrieved_at": retrieved_at}],
        ))
    return out


def fetch_votes(he: str, get: Getter = _http_get) -> tuple[list[RawEvent], dict]:
    """Äänestykset yhdelle HE:lle. 404 -> tyhjä lista ja status 'ei tietuetta'.

    'ei tietuetta' EI tarkoita ettei äänestetty: hyväksyminen ilman
    äänestystä ja keskeneräinen käsittely näyttävät samalta.
    """
    key = he_key(he)
    if not key:
        raise ChainError(f"ei HE-tunnus: {he!r}")
    url = _proxy({"votes": f"{key} vp"})
    status, body = get(url)
    ts = _now_iso()
    time.sleep(SPACING_S) if get is _http_get else None
    try:
        d = json.loads(body)
    except ValueError as exc:
        raise ChainError(f"äänestykset {key}: ei JSON (HTTP {status})") from exc
    err = d.get("error") if isinstance(d, dict) else None
    if err:
        if "404" in err:
            return [], {"source": "Eduskunta äänestys", "tunnus": key, "status": "ei tietuetta", "n": 0}
        if "429" in err:
            raise ChainError(f"äänestykset {key}: 429 — lopetetaan")
        raise ChainError(f"äänestykset {key}: {err}")
    evs = vote_events(d, key, url, ts)
    return evs, {"source": "Eduskunta äänestys", "tunnus": key, "status": d.get("status"),
                 "uptake_measurable": d.get("uptake_measurable"), "n": len(evs)}


# ── Ketjut ───────────────────────────────────────────────────────────
# Eduskunnan käsittelyvaiheet, jotka tarkoittavat että eduskunta on
# päättänyt asian: eduskunnan vastaus on annettu. Vastaus voi olla myös
# hylkäävä, joten tämä EI ole "hyväksytty" — se on "eduskunta päättänyt".
EV_VAIHEET = ("Eduskunnan vastaus ja kirjelmä",
              "Eduskunnan vastauksen tai kirjelmän toimittaminen")


def chains(raw_events: Iterable[dict]) -> dict[str, dict]:
    """HE-numero -> mitä ketjusta on havaittu. Ei tulkintaa, vain liitos.

    outcome, vahvimmasta heikoimpaan:
      säädös vahvistettu   Finlex-säädös viittaa HE:hen
      eduskunta päättänyt  eduskunnan vastaus annettu (ei kerro hyväksyttiinkö)
      äänestetty           äänestystietue, ei vastausta eikä säädöstä
      eduskunnassa         käsittelyvaiheita, ei vielä vastausta
      määrittämätön        Eduskunnasta ei havaintoa — EI hylätty, EI nolla

    KORJATTU 2026-09-29: aiemmin vain kolme tilaa, ja Finlex-ikkuna on yksi
    kuukausi. Vuosia sitten vahvistettu laki jäi siksi pysyvästi tilaan
    'määrittämätön', vaikka Eduskunnan aikajanalla oli vastaus. Lopputulos
    riippui kaappausikkunasta eikä todellisuudesta. Syyskuun kaappauksessa
    23/40 haetusta HE:stä oli jo eduskunnan vastaus.
    """
    out: dict[str, dict] = {}
    raw_events = list(raw_events)

    def slot(k: str) -> dict:
        return out.setdefault(k, {"hankkeet": [], "eduskunta_vaiheet": 0,
                                  "eduskunta_vastaus": None,
                                  "aanestykset": [], "saadokset": [],
                                  "vaikuttaminen": [], "vaikuttajat": []})

    # Hankkeen tunnus -> HE. Avoimuusrekisteri viittaa hankkeeseen, ei
    # HE:hen, joten liitos kulkee Hankeikkunan heNumerot-kentän kautta.
    tunnus_he: dict[str, set] = {}
    for d in raw_events:
        if d.get("source") == "Hankeikkuna":
            p = d.get("parameters") or {}
            for h in p.get("heNumerot") or []:
                k = he_key(h) if isinstance(h, str) else None
                if k and p.get("tunnus"):
                    tunnus_he.setdefault(p["tunnus"], set()).add(k)

    for d in raw_events:
        p = d.get("parameters") or {}
        src = d.get("source")
        if src == "Hankeikkuna":
            for h in p.get("heNumerot") or []:
                k = he_key(h)
                if k and p.get("tunnus") not in slot(k)["hankkeet"]:
                    slot(k)["hankkeet"].append(p.get("tunnus"))
        elif src == "Eduskunta":
            k = he_key(p.get("eduskuntatunnus", ""))
            if k:
                c = slot(k)
                c["eduskunta_vaiheet"] += 1
                if p.get("vaihe") in EV_VAIHEET and d.get("occurred_at"):
                    pvm = d["occurred_at"][:10]
                    if c["eduskunta_vastaus"] is None or pvm < c["eduskunta_vastaus"]:
                        c["eduskunta_vastaus"] = pvm
        elif src == "Eduskunta äänestys":
            k = he_key(p.get("eduskuntatunnus", ""))
            if k:
                slot(k)["aanestykset"].append(d["event_id"])
        elif src == "Finlex":
            for h in p.get("heNumerot") or []:
                k = he_key(h)
                if k:
                    slot(k)["saadokset"].append(p.get("saados"))
        elif src == "Avoimuusrekisteri":
            # Vaikuttaminen EI muuta lopputulosta: se on ketjun sisältöä,
            # ei sen vaihe. Hanke ilman HE:tä jää ketjujen ulkopuolelle
            # (ks. unlinked_lobbying).
            for k in tunnus_he.get(p.get("tunnus"), ()):
                c = slot(k)
                c["vaikuttaminen"].append(d["event_id"])
                if p.get("ilmoittaja") and p["ilmoittaja"] not in c["vaikuttajat"]:
                    c["vaikuttajat"].append(p["ilmoittaja"])
    for c in out.values():
        c["vaikuttajat"].sort()
        c["outcome"] = ("säädös vahvistettu" if c["saadokset"]
                        else "eduskunta päättänyt" if c["eduskunta_vastaus"]
                        else "äänestetty" if c["aanestykset"]
                        else "eduskunnassa" if c["eduskunta_vaiheet"]
                        else "määrittämätön")
    return dict(sorted(out.items()))

# ── HE -> Hankeikkunan hanke ────────────────────────────────────────
def resolve_hanke(he: str, search: Callable[[dict], list] | None = None) -> tuple[list, dict]:
    """Hankeikkunan hankkeet joiden heTiedot.heNumerot sisältää tämän HE:n.

    Hankeikkunan hakuskeemassa (KohdeV2SearchFormData) ei ole HE-kenttää.
    `teksti` löytää HE-numeron, mutta se RANKKAA eikä suodata: haku
    "HE 24/2026" palautti 4 hanketta, joista yksi oli oikea. Tulos
    suodatetaan siksi tarkalla vertailulla heNumerot-kenttään — ilman
    sitä liitos olisi väärä yhtä uskottavan näköisenä kuin oikea.

    Palauttaa (RawEvent-lista, loki). Tyhjä lista = ei hanketta, jonka
    heNumerot sisältäisi HE:n. Se ei tarkoita ettei hanketta ole:
    vanhoissa hankkeissa numero on ilman HE-etuliitettä ('117/2007').
    """
    from fetchers import fetch_hankeikkuna
    key = he_key(he)
    if not key:
        raise ChainError(f"ei HE-tunnus: {he!r}")
    search = search or (lambda extra: fetch_hankeikkuna(valmisteluvaihe=None, size=20, extra=extra))
    evs = search({"teksti": key})
    hits = [e for e in evs
            if key in {he_key(h) for h in (e.parameters.get("heNumerot") or []) if isinstance(h, str)}]
    for e in hits:
        e.parameters["query_valmisteluvaihe"] = "HE-haku (teksti + tarkka heNumerot)"
    return hits, {"source": "Hankeikkuna HE-haku", "tunnus": key,
                  "candidates": len(evs), "n": len(hits)}


def unlinked_lobbying(raw_events: Iterable[dict]) -> dict[str, dict]:
    """Avoimuusrekisterin hankkeet, joita ei voitu liittää HE-ketjuun:
    hanke ei ollut kaappauksessa tai sillä ei ole HE-numeroa (esim.
    asetushanke, strategia). Näytetään erikseen, ei pudoteta."""
    evs = list(raw_events)
    linked = {(d.get("parameters") or {}).get("tunnus") for d in evs
              if d.get("source") == "Hankeikkuna" and (d.get("parameters") or {}).get("heNumerot")}
    out: dict[str, dict] = {}
    for d in evs:
        if d.get("source") != "Avoimuusrekisteri":
            continue
        p = d.get("parameters") or {}
        t = p.get("tunnus")
        if not t or t in linked:
            continue
        c = out.setdefault(t, {"hanke_nimi": p.get("hanke_nimi"), "ilmoituksia": 0, "vaikuttajat": set()})
        c["ilmoituksia"] += 1
        if p.get("ilmoittaja"):
            c["vaikuttajat"].add(p["ilmoittaja"])
    return {t: {**c, "vaikuttajat": sorted(c["vaikuttajat"])} for t, c in sorted(out.items())}
