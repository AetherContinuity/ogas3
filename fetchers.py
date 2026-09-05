"""OGAS3 — tapahtumien haku ACI-proxyista.

Metodologinen ehto: moottori ei muuta tapahtumien sisältöä. Tämä moduuli
on mekaaninen poiminta — se lukee kentät, johtaa aikaleimat ja rakentaa
todisteen. Se EI luokittele.

Nimenomaisesti EI aseteta:
    type (D/O/S)        vaatii ROE-kartoituksen, ei ole spesifioitu
    impact_weight       ei spesifioitu
    intensity           I:n deterministinen laskenta ei ole spesifioitu
    irreversibility     aggregointikaava ei ole lukittu

Nämä jäävät None-arvoiksi ja validator vaatii ne eksplisiittisinä.
`type` on pakollinen, joten haettu tapahtuma EI ole vielä validi Event —
se on `RawEvent`, joka odottaa luokitusta.

AIKALEIMASEMANTIIKKA LÄHTEITTÄIN
--------------------------------
Hankeikkuna  occurred_at = kohde.asettamisPaiva   (hallinnollinen päätös)
             known_at    = kohde.julkaisuaika     (kirjautui järjestelmään)

             VARAKENTTÄ: jos asettamisPaiva puuttuu, käytetään aloitusPaiva.
             Kattavuus 12/32 -> 32/32. Käytetty kenttä kirjataan
             parameters.occurred_at_source.

    Mitattu 4.9.2026, kaikki 32 hanketta varakentän kanssa:
    mediaani 20 vrk, keskiarvo 86,2, min -396, maksimi 662 vrk.
    asettamisPaiva-pohjaiset: mediaani 20, max 662 (n=12)
    aloitusPaiva-pohjaiset:   mediaani 24, max 308 (n=20)
    YKSI NEGATIIVINEN: TEM061:00/2024 julkaistu 31 vrk ENNEN
    asettamispäiväänsä. Syy on semanttinen, ei tekninen: asettamisPaiva
    voi olla eteenpäin päivätty päätös, julkaisuaika on kirjautumishetki.
    Näitä EI korjata hiljaisesti — ne merkitään `anomaly`-kenttään ja
    validator hylkää ne, kunnes ihminen päättää mitä tehdä.

Eduskunta    occurred_at = kasittely.tapahtumapvm
             known_at    = sama päivä. Istunto on julkinen tapahtuma.

Finlex       occurred_at = säädöksen vahvistuspäivä
             known_at    = säädöskokoelmassa julkaisupäivä
             (ei toteutettu tässä versiossa — vaatii Akoma Ntoso -jäsennyksen)
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

POLICY_PROXY = "https://aci-policy-proxy.ruotsalainen-marko.workers.dev"
UA = {"User-Agent": "OGAS3/0.1", "Content-Type": "application/json"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _post(url: str, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=UA, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "OGAS3/0.1"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def _date_iso(v: Any) -> str | None:
    """Päivämäärä tai aikaleima -> ISO 8601 aikavyöhykkeellä.

    Hankeikkuna palauttaa päivämäärät ilman vyöhykettä ja julkaisuajan
    ilman Z:aa. Suomen aika oletetaan, koska lähde on suomalainen
    hallintojärjestelmä — tämä on oletus ja se on kirjattu tähän.
    """
    if not v or not isinstance(v, str):
        return None
    s = v.strip()
    if len(s) == 10:
        s += "T00:00:00"
    if not (s.endswith("Z") or "+" in s[10:]):
        s += "+03:00"          # OLETUS: Suomen aika
    return s


@dataclass
class RawEvent:
    """Haettu tapahtuma ENNEN luokitusta. Ei vielä validi Event."""

    event_id: str
    occurred_at: str | None
    known_at: str | None
    retrieved_at: str
    source: str
    source_url: str
    subtype: str | None
    parameters: dict[str, Any]
    evidence: list[dict[str, str]]
    anomaly: str | None = None
    type: None = None
    # Tyyppivihje: LAUSUNTO-asiakirjoista tiedetään että ne ovat L-tapahtumia
    # ilman tulkintaa (Hankeikkunan oma tyyppikenttä). Muille tyyppi jää
    # Nulliksi ja odottaa Extractoria.
    type_hint: str | None = None
    llm_classification: dict = field(default_factory=lambda: {
        "intensity": None, "targeting": None, "policy_proximity": None, "uptake": None})
    irreversibility: None = None
    impact_weight: None = None

    def to_dict(self) -> dict:
        d = {
            "event_id": self.event_id,
            "occurred_at": self.occurred_at,
            "known_at": self.known_at,
            "retrieved_at": self.retrieved_at,
            "source": self.source,
            "source_url": self.source_url,
            "type": self.type_hint,
            "subtype": self.subtype,
            "parameters": self.parameters,
            "llm_classification": self.llm_classification,
            "irreversibility": None,
            "impact_weight": None,
            "evidence": self.evidence,
        }
        if self.anomaly:
            d["_anomaly"] = self.anomaly
        return d


def fetch_hankeikkuna(valmisteluvaihe: str = "EDUSKUNTAKASITTELY",
                      tyyppi: str = "LAINSAADANTO",
                      size: int = 500) -> list[RawEvent]:
    url = f"{POLICY_PROXY}/?hi=kohteet/haku"
    body = {"tyyppi": [tyyppi], "valmisteluvaihe": [valmisteluvaihe], "size": size}
    j = _post(url, body)
    rows = j.get("data", {}).get("result", [])
    ret = _now_iso()
    out: list[RawEvent] = []
    for row in rows:
        k = row.get("kohde") or {}
        tunnus = k.get("tunnus") or k.get("uuid")
        # occurred_at: asettamisPaiva ensisijaisesti, aloitusPaiva varalla.
        # Mitattu 4.9.2026: asettamisPaiva täytetty 12/32, aloitusPaiva 32/32,
        # julkaisuaika 32/32. Ilman varakenttää 20 hanketta 32:sta putoaisi
        # pois, ja sarja mittaisi kirjaamisen huolellisuutta eikä tapahtumia.
        # KENTÄT EIVÄT OLE SAMA ASIA — asettaminen on muodollinen päätös,
        # aloitus on työn alkaminen. Käytetty kenttä kirjataan
        # parameters.occurred_at_source, jotta se voidaan suodattaa jälkikäteen.
        occ = _date_iso(k.get("asettamisPaiva"))
        occ_src = "asettamisPaiva"
        if not occ:
            occ = _date_iso(k.get("aloitusPaiva"))
            occ_src = "aloitusPaiva" if occ else None
        kn = _date_iso(k.get("julkaisuaika"))
        anomaly = None
        if occ and kn:
            if datetime.fromisoformat(kn) < datetime.fromisoformat(occ):
                lag = (datetime.fromisoformat(kn) - datetime.fromisoformat(occ)).days
                anomaly = (f"known_at {abs(lag)} vrk ENNEN occurred_at "
                           f"(lähde {occ_src}) — päivämäärä on todennäköisesti "
                           "eteenpäin päivätty hallinnollinen merkintä. "
                           "Ei korjattu automaattisesti.")
        else:
            anomaly = "aikaleimaa ei voi johtaa: julkaisuaika tai molemmat alkupäivät puuttuvat"
        nimi = (k.get("nimi") or {}).get("fi") or ""
        out.append(RawEvent(
            event_id=f"HI:{tunnus}",
            occurred_at=occ, known_at=kn, retrieved_at=ret,
            source="Hankeikkuna",
            source_url="https://api.hankeikkuna.fi/api/v2/kohteet/haku",
            subtype=k.get("valmisteluvaihe"),
            parameters={"tunnus": tunnus, "tila": k.get("tila"),
                        "asianumerot": k.get("asianumerot"),
                        "valmisteluvaihe": k.get("valmisteluvaihe"),
                        "occurred_at_source": occ_src,
                        "heNumerot": ((row.get("lainsaadanto") or {})
                                      .get("heTiedot") or {}).get("heNumerot"),
                        "skNumerot": ((row.get("lainsaadanto") or {})
                                      .get("heTiedot") or {}).get("skNumerot"),
                        "lainsaadantoTehtavaluokka": (row.get("lainsaadanto") or {}).get("tehtavaluokka"),
                        "asiasanat": [a.get("uri") if isinstance(a, dict) else a
                                      for a in (row.get("asiasanat") or [])][:12]},
            evidence=[{
                "quote": (nimi or "(nimeke puuttuu)")[:400],
                "location": f"kohteet/haku · tunnus {tunnus}",
                "source_url": "https://api.hankeikkuna.fi/api/v2/kohteet/haku",
                "retrieved_at": ret,
            }],
            anomaly=anomaly,
        ))
    return out


def fetch_eduskunta(tunnus: str) -> list[RawEvent]:
    """Yhden valtiopäiväasian käsittelyvaiheet tapahtumina.

    Istunto on julkinen tapahtuma: occurred_at == known_at. Tämä on
    ainoa lähde, jossa yhtäsuuruus on perusteltu eikä oletus.
    """
    import urllib.parse
    url = f"{POLICY_PROXY}/?asia={urllib.parse.quote(tunnus)}"
    j = _get(url)
    if "error" in j:
        raise RuntimeError(f"Eduskunta: {j['error']}")
    ret = _now_iso()
    out: list[RawEvent] = []
    for i, k in enumerate(j.get("aikajana") or []):
        ts = _date_iso(k.get("pvm"))
        out.append(RawEvent(
            event_id=f"EDK:{tunnus}:{i:02d}",
            occurred_at=ts, known_at=ts, retrieved_at=ret,
            source="Eduskunta",
            source_url="https://api.eduskunta.fi/api/v1/search",
            subtype=k.get("vaihe"),
            parameters={"eduskuntatunnus": tunnus, "vaihe": k.get("vaihe"),
                        "tila": j.get("tila")},
            evidence=[{
                "quote": f"{k.get('vaihe')} — {j.get('nimeke','')[:200]}",
                "location": f"valtiopaivaasia {tunnus}, aikajana[{i}]",
                "source_url": "https://api.eduskunta.fi/api/v1/search",
                "retrieved_at": ret,
            }],
            anomaly=None if ts else "tapahtumapvm puuttuu",
        ))
    return out


def summarize(events: list[RawEvent]) -> dict:
    lags = []
    for e in events:
        if e.occurred_at and e.known_at:
            lags.append((datetime.fromisoformat(e.known_at)
                         - datetime.fromisoformat(e.occurred_at)).days)
    anomalies = [e for e in events if e.anomaly]
    s = sorted(lags)
    return {
        "n": len(events),
        "with_both_timestamps": len(lags),
        "anomalies": len(anomalies),
        "lag_median": s[len(s) // 2] if s else None,
        "lag_mean": round(sum(s) / len(s), 1) if s else None,
        "lag_max": max(s) if s else None,
        "lag_negative": sum(1 for x in s if x < 0),
    }

# ── L-TAPAHTUMAT: lausunnot Hankeikkunan asiakirjoista ────────────────
#
# LÖYTÖ 5.9.2026: erillistä Lausuntopalvelu-proxya ei tarvita. Lausunnot
# päätyvät hankkeen julkisille hankesivuille (valtioneuvosto.fi/hankkeet),
# ja Hankeikkunan `asiakirjat`-kentässä ne ovat rakenteisena.
#
# Yhdessä hankkeessa (STM050:00/2025) 93 asiakirjaa, joista:
#   LAUSUNTO 80 · LAUSUNTOPYYNTO 8 · YHTEENVETO 4 · MUISTIO 1
#
# ROE:n rakenteellinen päätös — L-tapahtuma on lausunto, EI lausuntopyyntö —
# on siis valvottavissa `tyyppi`-kentästä koneellisesti, ilman tulkintaa.
#
# Kenttäkartoitus:
#   laatija.fi        -> actor (ja actor_role-kartoituksen pohja)
#   laatimispaiva     -> occurred_at   (lausunnon päiväys)
#   luotu             -> known_at      (kirjautui Hankeikkunaan)
#   url               -> evidence.source_url, ja Extractorin syöte
#   uuid              -> event_id
#
# Mitattu 80 lausunnosta 5.9.2026: laatija, laatimispaiva ja luotu ovat
# täytettyjä 80/80. URL puuttuu 2:lta — ne ovat `nakyvyys: VIITETIEDOT`,
# eli asiakirjasta on julkaistu vain viitetiedot eikä tiedostoa.
# Viive laatimisesta kirjautumiseen: mediaani 0 vrk, max 97, ei negatiivisia.

STATEMENT_TYPE = "LAUSUNTO"          # L-tapahtuma
REQUEST_TYPE = "LAUSUNTOPYYNTO"      # hallinnon toimi, EI L-tapahtuma


def statements_from_kohde(row: dict, ret: str) -> list[RawEvent]:
    """Poimii yhden hankkeen lausunnot L-tapahtumina.

    Ei luokittele: type asetetaan "L", mutta intensity/targeting/
    policy_proximity/uptake jäävät Nulliksi. Ne ovat Extractorin työtä
    ja vaativat PDF:n sisällön, ei metatietoja.
    """
    k = row.get("kohde") or {}
    tunnus = k.get("tunnus") or k.get("uuid")
    out: list[RawEvent] = []
    for a in (row.get("asiakirjat") or []):
        if a.get("tyyppi") != STATEMENT_TYPE:
            continue
        occ = _date_iso(a.get("laatimispaiva"))
        kn = _date_iso(a.get("luotu"))
        laatija = (a.get("laatija") or {}).get("fi")
        nimi = (a.get("nimi") or {}).get("fi") or ""
        url = a.get("url")

        anomaly = None
        if not occ or not kn:
            anomaly = "laatimispaiva tai luotu puuttuu — aikaleimaa ei voi johtaa"
        elif datetime.fromisoformat(kn) < datetime.fromisoformat(occ):
            lag = (datetime.fromisoformat(kn) - datetime.fromisoformat(occ)).days
            anomaly = (f"known_at {abs(lag)} vrk ENNEN occurred_at — "
                       "ei korjattu automaattisesti")
        if not url:
            # nakyvyys: VIITETIEDOT — vain viitetiedot julkaistu, ei tiedostoa.
            # Tapahtuma on olemassa mutta Extractor ei voi luokitella sitä.
            anomaly = ((anomaly + " · ") if anomaly else "") + \
                      f"asiakirjan URL puuttuu (nakyvyys={a.get('nakyvyys')}) — " \
                      "sisältöä ei voi lukea, luokitus jää tekemättä"

        out.append(RawEvent(
            event_id=f"HI-LAUS:{a.get('uuid')}",
            occurred_at=occ, known_at=kn, retrieved_at=ret,
            source="Hankeikkuna/asiakirjat",
            source_url="https://api.hankeikkuna.fi/api/v2/kohteet/haku",
            subtype=STATEMENT_TYPE,
            parameters={"hanke": tunnus, "actor": laatija,
                        "nakyvyys": a.get("nakyvyys"),
                        "asiakirja_url": url,
                        "asiasanat": [x.get("uri") if isinstance(x, dict) else x
                                      for x in (row.get("asiasanat") or [])][:12]},
            evidence=[{
                "quote": (nimi or "(nimeke puuttuu)")[:400],
                "location": f"asiakirjat · hanke {tunnus} · uuid {a.get('uuid')}",
                "source_url": url or "https://api.hankeikkuna.fi/api/v2/kohteet/haku",
                "retrieved_at": ret,
            }],
            anomaly=anomaly,
        ))
        out[-1].type_hint = "L"      # ks. RawEvent.to_dict
    return out


def fetch_statements(tunnukset: list[str],
                     errors: list[dict] | None = None) -> list[RawEvent]:
    """Hakee lausunnot annetuille hanketunnuksille, PERÄKKÄIN.

    Hankeikkunan haku palauttaa asiakirjat vain kun kysely kohdistuu
    yksittäiseen hankkeeseen — listahaussa kenttä on tyhjä eikä se anna
    virhettä. Siksi tämä on N kutsua eikä yksi.

    VIRHEENKÄSITTELY (korjattu 2026-09-05):
    Aiempi versio nielaisi poikkeuksen `except Exception: continue`.
    Jos proxy oli alhaalla tai host estetty, funktio palautti tyhjän
    listan ILMAN virhettä — ja tulos näytti siltä että lausuntoja ei
    ole. Se on sama vikaluokka kuin muut tässä järjestelmässä todetut
    hiljaiset viat, ja se oli ainoa hakija joka teki niin:
    fetch_hankeikkuna ja fetch_eduskunta päästävät poikkeuksen läpi.

    Kaksi tilaa, kutsujan valittavana:
      errors is None   poikkeus nousee läpi kuten muissa hakijoissa
      errors annettu   virhe kirjataan listaan ja haku jatkuu muihin
                       tunnuksiin — kutsuja (esim. snapshot.py) raportoi

    Kummassakaan tapauksessa virhe ei katoa.
    """
    url = f"{POLICY_PROXY}/?hi=kohteet/haku"
    ret = _now_iso()
    out: list[RawEvent] = []
    for t in tunnukset:
        try:
            j = _post(url, {"tunnus": [t], "size": 1})
        except Exception as exc:
            if errors is None:
                raise
            errors.append({"source": "Hankeikkuna/asiakirjat", "tunnus": t,
                           "error": str(exc)})
            continue
        rows = j.get("data", {}).get("result", [])
        if not rows:
            # Hanke ei löytynyt. EI virhe, mutta ei myöskään nolla
            # lausuntoa — nämä ovat eri asioita ja pysyvät erillään.
            if errors is not None:
                errors.append({"source": "Hankeikkuna/asiakirjat", "tunnus": t,
                               "error": "hanketta ei löytynyt (0 osumaa)"})
            continue
        out.extend(statements_from_kohde(rows[0], ret))
    return out
