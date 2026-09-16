"""OGAS3 — collect.py: proxykutsu → trace-solmu.

Jokainen haku tässä istunnossa kirjoitettiin käsin. Sama 429-käsittely
toistui viidessä skriptissä, ja `evidence`-rakenne oli joka kerta
hieman erilainen. Tämä yhtenäistää molemmat.

PERIAATE
--------
Trace-solmu tarvitsee neljä asiaa:

    occurred_at   milloin tapahtui
    known_at      milloin tuli julkiseksi
    source        mistä
    evidence      mitä, mistä kohtaa, millä kutsulla

**Proxy antaa kaikki neljä**, ja `evidence.source_url` on se kutsu
jolla luku haettiin — joten havainto on toistettavissa. Kertaluontoinen
lähde (XLS, PDF) antaa vain kaksi, ja siksi se on eri `source_class`.

Se ero ratkaisee mikä tallennetaan repoon: `rp-margin` ja
`wem-mittaukset` eivät ole uudelleenhaettavissa kohtuullisella
vaivalla, `edp-2025` on yksi kutsu.

MITÄ TÄMÄ EI TEE
----------------
- Ei päätä mikä on `occurred_at`. Se on lähdekohtainen: StatFinin
  vuosihavainnon tapahtumahetki on 31.12., Fingridin varttidatan
  `startTime`. Kutsuja antaa säännön.
- Ei luokittele tapahtumatyyppiä.
- Ei kirjoita tiedostoa. Palauttaa solmut; snapshotin kokoaminen on
  `snapshot_trace.py`:n tai kutsujan työ.
- Ei tulkitse. `_measured`-kenttään menevät luvut sellaisenaan.

429-KÄSITTELY
-------------
Yhdessä paikassa, koska se oli viidessä. Fingrid on tiukin: 3 vrk
ikkuna, 1,8–2,2 s tauko, backoff 6–8 s. Ilman niitä 43 ikkunaa 61:stä
kaatui.

**Rinnakkaisuus on kielletty.** Promise.all-tyylinen yhtaikaisuus
laukaisi 429:n välittömästi myös selaimessa.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

UA = "aci-ogas3-collect/1.0 (aethercontinuity.org)"

# Proxyt. Nimet ovat vakiintuneet; polku on osa osoitetta koska
# ne eroavat — Fingrid on /api, muut juuressa.
PROXY = {
    "fingrid":  "https://aci-fingrid-proxy.ruotsalainen-marko.workers.dev/api",
    "policy":   "https://aci-policy-proxy.ruotsalainen-marko.workers.dev/",
    "pxweb":    "https://aci-pxweb-proxy.ruotsalainen-marko.workers.dev/",
    "avoimuus": "https://aci-avoimuus-proxy.ruotsalainen-marko.workers.dev/",
    "entsoe":   "https://aci-entsoe-proxy.ruotsalainen-marko.workers.dev/",
    "ecb":      "https://aci-ecb-proxy.ruotsalainen-marko.workers.dev/",
    "yva":      "https://aci-yva-proxy.ruotsalainen-marko.workers.dev/",
}

# Tauko haun jälkeen. Fingrid on tiukin; avoimuusrekisterin käyttöehdot
# vaativat 500 ms JA rajaavat volyymia erikseen.
SPACING = {"fingrid": 2.0, "avoimuus": 1.2, "entsoe": 3.0, "pxweb": 1.5}
DEFAULT_SPACING = 1.0

# Aikakatkaisu. ENTSO-E on hidas: 5–26 s tyypillisesti, ja 30 s
# katkaisi kesken. Ks. proxy-ohje luku 2.
TIMEOUT = {"entsoe": 90, "avoimuus": 90}
DEFAULT_TIMEOUT = 60


class CollectError(RuntimeError):
    pass


@dataclass
class Fetch:
    """Yhden kutsun tulos. `url` on se millä se toistetaan."""
    proxy: str
    url: str
    data: Any
    retrieved_at: str
    attempts: int = 1


def _url(proxy: str, params: dict | None = None, path: str = "") -> str:
    base = PROXY[proxy]
    if path:
        base = base.rstrip("/") + "/" + path.lstrip("/")
    if not params:
        return base
    sep = "&" if "?" in base else "?"
    return base + sep + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


def fetch(proxy: str, params: dict | None = None, *, path: str = "",
          body: dict | None = None, tries: int = 3) -> Fetch:
    """Yksi kutsu. 429 uusitaan, muut virheet nostetaan heti.

    Muut virheet EIVÄT parane odottamalla — uusiminen vain piilottaa
    ne ja kuormittaa lähdettä.
    """
    if proxy not in PROXY:
        raise CollectError(f"tuntematon proxy {proxy!r}, sallitut {list(PROXY)}")
    u = _url(proxy, params, path)
    to = TIMEOUT.get(proxy, DEFAULT_TIMEOUT)
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                u, headers={"User-Agent": UA, "Accept": "application/json"})
            if body is not None:
                req.data = json.dumps(body).encode()
                req.add_header("Content-Type", "application/json")
            raw = urllib.request.urlopen(req, timeout=to).read()
            d = json.loads(raw)
            if isinstance(d, dict) and "error" in d:
                raise CollectError(f"{proxy}: {d['error']}")
            time.sleep(SPACING.get(proxy, DEFAULT_SPACING))
            return Fetch(proxy=proxy, url=u, data=d, attempts=i + 1,
                         retrieved_at=datetime.now(timezone.utc)
                         .replace(microsecond=0).isoformat())
        except Exception as e:
            last = e
            if "429" in str(e) and i < tries - 1:
                time.sleep(6 * (i + 1))
                continue
            raise CollectError(f"{proxy} {u}: {e}") from e
    raise CollectError(str(last))


def fetch_many(calls: Iterable[tuple[str, dict]], tries: int = 3) -> list[Fetch]:
    """Useita kutsuja PERÄKKÄIN.

    Rinnakkaisuutta ei tarjota tarkoituksella. Yhtaikaiset kutsut
    laukaisivat 429:n välittömästi sekä skriptistä että selaimesta.
    """
    return [fetch(p, params, tries=tries) for p, params in calls]


# ── solmujen muodostus ──────────────────────────────────────────────

def assert_nonempty(f: Fetch, rows: Iterable, *, mika: str = "") -> None:
    """Nostaa virheen jos tulos on tyhjä.

    HAVAITTU 2026-09-16: `?ds=99999` ei anna virhettä. Fingrid palauttaa
    `{"data": [], "pagination": {"total": 0}}` — siis 200 OK ja tyhjä
    lista. Tuntematon datasetti ja aito tyhjä ikkuna näyttävät
    TÄSMÄLLEEN samalta.

    Sama koskee useimpia proxyja: tuntematon parametri tuottaa tyhjän
    tuloksen, ei virhettä.

    **Tyhjä ei ole havainto.** Jos kutsuja odottaa rivejä, hän kutsuu
    tätä — ja saa virheen sen sijaan että kirjaisi nollan.

    Sama vikaluokka kuin DS 105:n vakionolla, tyhjä 404 Eduskunnasta ja
    yksikielinen lomakejäsennin: rakenne näyttää oikealta, sisältöä ei
    ole, eikä mikään kerro eroa.
    """
    rows = list(rows)
    if rows:
        return
    raise CollectError(
        f"TYHJÄ TULOS{' — ' + mika if mika else ''}: {f.url}\n"
        "Tyhjä lista EI ole havainto. Mahdolliset syyt: tuntematon "
        "tunniste (ei anna virhettä), väärä parametrin nimi, ikkuna "
        "jolla ei ole dataa, tai sarja joka alkaa myöhemmin. "
        "Tarkista tunniste ennen kuin tulkitset tämän nollaksi.")


def to_nodes(f: Fetch, *,
             rows: Callable[[Any], Iterable[dict]],
             node_id: Callable[[dict], str],
             occurred_at: Callable[[dict], str],
             quote: Callable[[dict], str],
             location: str,
             source: str,
             known_at: Callable[[dict], str | None] | None = None,
             measured: Callable[[dict], dict] | None = None,
             **kiinteat: Any) -> list[dict]:
    """Muuntaa hakutuloksen trace-solmuiksi.

    Kaikki muunnokset ovat KUTSUJAN antamia funktioita. Moduuli ei
    tiedä missä `occurred_at` on missäkin lähteessä — StatFinin
    vuosihavainnossa se on 31.12., Fingridin varttidatassa
    `startTime`. Sääntö tulee kutsujalta, ei arvauksena.

    `evidence.source_url` on aina se kutsu jolla data haettiin, joten
    havainto on toistettavissa.
    """
    kaikki = list(rows(f.data))
    if not kaikki:
        # EI palauta tyhjää listaa hiljaa — ks. assert_nonempty.
        raise CollectError(
            f"to_nodes: rows() palautti tyhjän. {f.url}\n"
            "Tyhjä ei ole havainto. Jos tyhjä on odotettu tulos, kutsu "
            "rows() itse ja käsittele se eksplisiittisesti.")
    out = []
    for r in kaikki:
        n: dict[str, Any] = {
            "node_id": node_id(r),
            "kind": "observed",
            "occurred_at": occurred_at(r),
            "known_at": known_at(r) if known_at else None,
            "retrieved_at": f.retrieved_at,
            "source": source,
            "evidence": [{
                "quote": quote(r),
                "location": location,
                "source_url": f.url,       # TOISTETTAVA
                "retrieved_at": f.retrieved_at,
            }],
        }
        if measured:
            n["_measured"] = measured(r)
        n.update(kiinteat)
        out.append(n)
    return out


# ── valmiit reitit — vain ne jotka on TODENNETTU tässä istunnossa ───
#
# Jokainen alla oleva on ajettu ja tulos tarkistettu. Muita ei
# lisätä ennen kuin ne on ajettu — arvattu reitti on huonompi kuin
# ei reittiä, koska se näyttää valmiilta.

def statfin(table: str, query: list[dict]) -> Fetch:
    """PxWeb-taulukko. HUOM: parametri on `p`, EI `px`.

    Ja polkumuoto on `StatFin/klv/14lj.px`, EI Tilastokeskuksen
    omaa tunnusta `statfin_klv_pxt_14lj.px` — jälkimmäinen antaa 400.
    Proxyn oma virheviesti kertoo oikean muodon.
    """
    return fetch("pxweb", {"p": table},
                 body={"query": query,
                       "response": {"format": "json-stat2"}})


def statfin_tables(db: str) -> Fetch:
    """Tietokannan taulukkoluettelo. Poistaa tunnusten arvailun."""
    return fetch("pxweb", {"p": db})


def hankeikkuna(tunnus: str) -> Fetch:
    return fetch("policy", {"hi": "kohteet/haku"},
                 body={"tunnus": [tunnus], "size": 1})


def votes(asia: str) -> Fetch:
    """Äänestykset. Tunnus koodataan kokonaan — myös kauttaviiva.

    `HE 101/2024` -> `HE%20101%2F2024`. Raaka kauttaviiva antaa tyhjän
    404:n, ja välilyönti katkaisee greedy-polkuparametrin.
    """
    return fetch("policy", {"votes": asia})


def fingrid(ds: int, start: str, end: str, size: int = 400) -> Fetch:
    """Fingrid-datasetti. Ikkuna korkeintaan 3 vrk 429:n takia."""
    return fetch("fingrid", {"ds": ds, "start": start, "end": end,
                             "size": size})


def entsoe_price(bzn: str, start: str, end: str) -> Fetch:
    return fetch("entsoe", {"bzn": bzn, "periodStart": start,
                            "periodEnd": end}, path="day-ahead-price")


def entsoe_capacity(bzn: str, year: int) -> Fetch:
    return fetch("entsoe", {"bzn": bzn, "year": year},
                 path="installed-capacity")


def yva_index(section: str = "all") -> Fetch:
    """YVA-hankeluettelo. Turvakynnys on proxyssa: alle 100 hanketta
    nostaa virheen, koska HTML-jäsennin hajoaa hiljaa."""
    return fetch("yva", {"index": section})


def avoimuus_term(route: str, term_id: int) -> Fetch:
    """Kausikohtainen haku. Rajaton päätepiste ei ota parametreja
    ja antaa 500 — se on poistettu proxysta."""
    return fetch("avoimuus", {"term_route": route, "termId": term_id})
