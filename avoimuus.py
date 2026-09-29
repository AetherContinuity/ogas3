"""OGAS3 — Avoimuusrekisteri: vaikuttamistoiminta lainsäädäntöhankkeisiin.

MIKSI
-----
Lausunnot ovat julkisen kuulemisen kanava. Avoimuusrekisterin
toimintailmoitukset ovat toinen: suorat yhteydenotot valmistelijoihin,
ministereihin ja kansanedustajiin. Ilmoitusvelvollisuus on lakisääteinen
(avoimuusrekisterilaki 430/2023), ja VTV julkaisee ilmoitukset avoimena
datana (CC BY 4.0).

Liitos ketjuihin on suora: ilmoituksen aihe voi viitata hankkeeseen
tunnuksella (`contactTopicProject.projectId`, esim. "STM200:00/2025"),
joka on sama tunnus kuin Hankeikkunassa. Kaudella 1–6/2026 näin teki
635 aihetta 4 819:stä. Loput ovat vapaata tekstiä ("other"), joita ei
tässä tulkita hankkeiksi.

AIKALEIMAT — TÄSMÄLLINEN PÄIVÄ EI OLE TIEDOSSA
---------------------------------------------
Ilmoitus kertoo kauden (puoli vuotta), ei yhteydenoton päivää.

    occurred_at   YLÄRAJA: kauden loppu, tai ilmoituspäivä jos se on
                  aiempi. Yhteydenotto tapahtui viimeistään silloin.
    known_at      ilmoituspäivä (activityNotificationDate)

parameters.occurred_at_precision = "ilmoituskausi" ja kauden rajat
kulkevat mukana. Näkyvyysviive on siksi ALARAJA — todellinen viive voi
olla puoli vuotta pidempi. Tätä ei korjata arvaamalla päivää.

MITÄ EI TALLETETA
-----------------
Kohteiden henkilönimiä. Rekisteri julkaisee ne, mutta ketjun kannalta
riittää organisaatio ja osasto; sama periaate kuin äänestyksissä, joista
talletetaan ryhmäjakauma eikä kansanedustajakohtaisia rivejä.

KÄYTTÖEHDOT
-----------
VTV:n rajapinta on tarkoitettu kevyeen käyttöön. Yksi kausihaku kuussa
(ilmoitukset + kohteet), proxy välimuistittaa 30 vrk. 403 ja 429
tarkoittavat volyymirajaa: haku lopetetaan eikä uusita.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Callable

from fetchers import RawEvent

AVOIMUUS_PROXY = "https://aci-avoimuus-proxy.ruotsalainen-marko.workers.dev/"
UPSTREAM = "https://public.api.avoimuusrekisteri.fi/"

Getter = Callable[[dict], dict]


class AvoimuusError(RuntimeError):
    pass


def _get(params: dict) -> dict:
    url = AVOIMUUS_PROXY + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "OGAS3/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise AvoimuusError(f"avoimuusrekisteri {e.code}: volyymiraja — lopetetaan, ei uusita") from e
        raise AvoimuusError(f"avoimuusrekisteri HTTP {e.code}") from e
    if isinstance(d, dict) and d.get("error"):
        if any(c in str(d["error"]) for c in ("403", "429")):
            raise AvoimuusError(f"avoimuusrekisteri: volyymiraja — {d['error']}")
        raise AvoimuusError(f"avoimuusrekisteri: {d['error']}")
    return d


def current_term(terms: list[dict], now: datetime) -> dict | None:
    """Uusin kausi jonka ilmoitusaika on alkanut. Ilmoitukset kertyvät
    ilmoitusaikana ja sen jälkeen (myöhästyneet, muokatut), joten sama
    kausi kaapataan uudelleen joka kuukausi kunnes seuraava avautuu."""
    ok = [t for t in terms if t.get("status") != "draft"
          and t.get("signUpStartDate")
          and datetime.fromisoformat(t["signUpStartDate"].replace("Z", "+00:00")) <= now]
    return max(ok, key=lambda t: t["signUpStartDate"]) if ok else None


def _d(s: str | None) -> str | None:
    return s[:10] if s else None


def topic_events(notifications: list[dict], targets: list[dict], term: dict,
                 retrieved_at: str) -> tuple[list[RawEvent], dict]:
    orgs = {}
    for t in targets:
        fi = t.get("fi") or {}
        org = (fi.get("organization") or "").strip()
        dep = (fi.get("department") or "").strip()
        orgs[t["id"]] = org + (f" / {dep}" if dep and dep != "-" else "")

    start, end = _d(term.get("reportingStartDate")), _d(term.get("reportingEndDate"))
    out: list[RawEvent] = []
    n_topics = n_other = n_unresolved = 0
    for n in notifications:
        for tp in n.get("topics") or []:
            n_topics += 1
            proj = tp.get("contactTopicProject") or {}
            if tp.get("contactTopicType") != "project" or not proj.get("projectId"):
                n_other += 1
                continue
            nd = _d(n.get("activityNotificationDate"))
            occ_day = min(d for d in (end, nd) if d) if (end or nd) else None
            tids = [c.get("contactedTargetId") for c in tp.get("contactedTargets") or []]
            names = sorted({orgs[i] for i in tids if i in orgs})
            n_unresolved += sum(1 for i in tids if i not in orgs)
            methods = sorted({m for c in tp.get("contactedTargets") or [] for m in c.get("contactMethods") or []})
            anomaly = None if nd else "ilmoituspäivä puuttuu — known_at ei johdettavissa"
            src = f"{UPSTREAM}open-data-activity-notification/term/{term.get('id')}"
            out.append(RawEvent(
                event_id=f"AV:{tp.get('id')}",
                occurred_at=f"{occ_day}T00:00:00+03:00" if occ_day else None,
                known_at=f"{nd}T00:00:00+03:00" if nd else None,
                retrieved_at=retrieved_at,
                source="Avoimuusrekisteri",
                source_url=src,
                subtype=tp.get("activityType"),
                parameters={
                    "tunnus": proj["projectId"],
                    "hanke_nimi": proj.get("fi"),
                    "ilmoittaja": n.get("companyName"),
                    "ilmoittaja_ytunnus": n.get("companyId"),
                    "toimiala": n.get("mainIndustry"),
                    "toiminnan_maara": n.get("activityAmount"),
                    "asiakas": tp.get("customerCompanyName") or None,
                    "kohteet": names,
                    "kohteita": len(tids),
                    "yhteydenottotavat": methods,
                    "diaarinumero": n.get("diaryNumber"),
                    "kausi": {"id": term.get("id"), "alku": start, "loppu": end},
                    "occurred_at_precision": "ilmoituskausi",
                    "occurred_at_source": "min(kauden loppu, ilmoituspäivä) — yläraja",
                    "myohassa": n.get("isOverdue"),
                    "muokattu": n.get("isEdited"),
                    "data_class": "authoritative (lakisääteinen ilmoitusvelvollisuus)",
                },
                evidence=[{
                    "quote": f"{n.get('companyName')} → {proj['projectId']} {proj.get('fi') or ''}"[:300],
                    "location": f"ilmoitus {n.get('diaryNumber')}, aihe {tp.get('id')}",
                    "source_url": src, "retrieved_at": retrieved_at,
                }],
                anomaly=anomaly,
            ))
    log = {"source": "Avoimuusrekisteri", "kausi": term.get("id"),
           "window": [start, end], "ilmoituksia": len(notifications),
           "aiheita": n_topics, "hankeaiheita": len(out), "muita_aiheita": n_other,
           "kohteita_ratkaisematta": n_unresolved,
           "hankkeita": len({e.parameters["tunnus"] for e in out})}
    return out, log


def fetch_current(now: datetime | None = None, get: Getter = _get) -> tuple[list[RawEvent], dict]:
    now = now or datetime.now(timezone.utc)
    terms = get({"r": "terms_all", "limit": 50, "offset": 0}).get("data") or []
    term = current_term(terms, now)
    if not term:
        return [], {"source": "Avoimuusrekisteri", "status": "ei avointa tai päättynyttä kautta"}
    acts = get({"term_route": "activities_term", "termId": term["id"]})
    tgts = get({"term_route": "targets_term", "termId": term["id"]})
    retrieved = acts.get("fetched") or now.replace(microsecond=0).isoformat()
    retrieved = retrieved.replace("Z", "+00:00")
    evs, log = topic_events(acts.get("data") or [], tgts.get("data") or [], term, retrieved)
    if acts.get("n") is not None and acts["n"] != len(acts.get("data") or []):
        log["varoitus"] = f"proxy ilmoitti n={acts['n']}, dataa {len(acts.get('data') or [])}"
    return evs, log
