"""Stance-validoinnin otos — kehikko.md:n "Otos"-osion toteutus.

Ajetaan kerran. Tulos `otos.json` ja `teksti/<uuid>.txt` committataan
ennen käsikoodausta. Tätä tiedostoa ei muuteta otoksen jälkeen.

PERUSJOUKKO
-----------
Hankeikkuna LAINSAADANTO-hankkeet, jotka osuvat johonkin TERMIT-listan
`teksti`-hakuun. Lista on kiinteä. Pois jätetty tarkoituksella:
  "sähkö"        osuu sanaan "sähköinen" (sähköinen asiointi ym.)
  "polttoaine"   osuu liikenteen ja verotuksen hankkeisiin
Hankkeen lausunnot = asiakirjat, tyyppi LAUSUNTO, url olemassa.

"Lausuntoaika päättyi ennen 1.10.2026":
  hankkeen LAUSUNTOKIERROS-etappien suurin `loppu` < 2026-10-01.
  Jos etappia tai loppupäivää ei ole: lausunnon `laatimispaiva`
  (tai `luotu`) < 2026-10-01. Kirjataan tietueeseen (`aika_peruste`).

POISSULJETUT ENNEN JÄRJESTYSTÄ
  TEM040:00/2026, TEM043:00/2026 (tuotantoaineisto)
  rekisteröijän oma lausunto (laatija alkaa "Marko Ruotsalainen")

VALINTA
  sha256(asiakirjan uuid) nousevaan järjestykseen. Kuljetaan järjestyksessä:
  PDF haetaan, teksti `pdftotext -layout`, `extractor.parse_form`.
  Ohitetaan (syy kirjataan): is_empty, form_type tunnistamaton,
  parse_confidence low kysymys-/pykälälomakkeella (poikkeama_1),
  haku- tai tekstivirhe (myös muut kuin PDF-tiedostot). 20 ensimmäistä
  hyväksyttyä = otos. Ohitetut kirjataan `ohitetut`-listaan.

Ajo:  python3 ennakkorekisteroinnit/stance/otos.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from extractor import parse_form  # noqa: E402

PROXY = "https://aci-policy-proxy.ruotsalainen-marko.workers.dev"
TERMIT = [
    "sähkömarkkina", "sähköverkko", "sähkönsiirto", "sähköntuotanto",
    "siirtoverkko", "energia", "energiatehokkuus", "uusiutuva",
    "tuulivoima", "vety", "ydinenergia", "maakaasu", "kaukolämmi",
]
RAJA = "2026-10-01"
POIS_HANKKEET = {"TEM040:00/2026", "TEM043:00/2026"}
POIS_LAATIJA = ("marko ruotsalainen",)
N = 20


def _post(body: dict) -> dict:
    req = urllib.request.Request(
        f"{PROXY}/?hi=kohteet/haku", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "OGAS3/0.1 stance-otos"},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.loads(r.read().decode())
    if "error" in j:
        raise RuntimeError(j["error"])
    return j


def hae_hankkeet() -> tuple[dict[str, dict], dict[str, int]]:
    hankkeet: dict[str, dict] = {}
    osumat: dict[str, int] = {}
    for t in TERMIT:
        after = None
        n = 0
        while True:
            body = {"teksti": t, "tyyppi": ["LAINSAADANTO"], "size": 500}
            if after:
                body["searchAfter"] = after
            j = _post(body)
            rows = j["data"]["result"]
            for r in rows:
                hankkeet.setdefault(r["kohde"]["uuid"], r)
            n += len(rows)
            after = j["data"].get("nextSearchAfter")
            if not rows or not after or n >= j.get("totalHits", 0):
                break
        if n != j.get("totalHits"):
            raise RuntimeError(f"{t}: haettu {n}, totalHits {j.get('totalHits')} — vajaa joukko")
        osumat[t] = n
    return hankkeet, osumat


def _pvm(v) -> str | None:
    if not v:
        return None
    return str(v)[:10]


def perusjoukko(hankkeet: dict[str, dict]) -> list[dict]:
    out = []
    for r in hankkeet.values():
        k = r["kohde"]
        tunnus = k.get("tunnus")
        if tunnus in POIS_HANKKEET:
            continue
        loput = [e.get("loppu") for e in (r.get("etapit") or [])
                 if e.get("tyyppi") == "LAUSUNTOKIERROS" and e.get("loppu")]
        kierros = max(loput) if loput else None
        for a in r.get("asiakirjat") or []:
            if a.get("tyyppi") != "LAUSUNTO" or not a.get("url"):
                continue
            laatija = ((a.get("laatija") or {}).get("fi") or "").strip()
            if laatija.lower().startswith(POIS_LAATIJA):
                continue
            if kierros:
                if kierros >= RAJA:
                    continue
                peruste = f"LAUSUNTOKIERROS.loppu {kierros}"
            else:
                d = _pvm(a.get("laatimispaiva")) or _pvm(a.get("luotu"))
                if not d or d >= RAJA:
                    continue
                peruste = f"asiakirjan pvm {d} (ei kierroksen loppua)"
            out.append({
                "uuid": a["uuid"],
                "sha256": hashlib.sha256(a["uuid"].encode()).hexdigest(),
                "hanke": tunnus,
                "laatija": laatija or None,
                "nimi": (a.get("nimi") or {}).get("fi"),
                "laatimispaiva": _pvm(a.get("laatimispaiva")),
                "url": a["url"],
                "aika_peruste": peruste,
            })
    # sama asiakirja voi esiintyä usean hankkeen alla — uuid ratkaisee
    uniq = {d["uuid"]: d for d in out}
    return sorted(uniq.values(), key=lambda d: d["sha256"])


def teksti(url: str) -> str:
    q = urllib.parse.urlencode({"doc": url})
    req = urllib.request.Request(f"{PROXY}/?{q}", headers={"User-Agent": "OGAS3/0.1 stance-otos"})
    with urllib.request.urlopen(req, timeout=120) as r:
        pdf = r.read()
    if not pdf.startswith(b"%PDF"):
        raise RuntimeError(f"ei PDF ({pdf[:80]!r})")
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(pdf)
        f.flush()
        res = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", f.name, "-"],
                             capture_output=True, timeout=120)
    if res.returncode != 0:
        raise RuntimeError(f"pdftotext {res.returncode}: {res.stderr[:200]!r}")
    return res.stdout.decode("utf-8", errors="replace")


def main() -> int:
    hankkeet, osumat = hae_hankkeet()
    pj = perusjoukko(hankkeet)
    (HERE / "teksti").mkdir(exist_ok=True)
    valitut, ohitetut = [], []
    for d in pj:
        if len(valitut) >= N:
            break
        try:
            txt = teksti(d["url"])
        except Exception as exc:          # noqa: BLE001 — syy kirjataan
            ohitetut.append({"uuid": d["uuid"], "syy": f"haku: {exc}"})
            continue
        form = parse_form(txt)
        syy = None
        if not txt.strip():
            syy = "tyhjä teksti (skannattu PDF?)"
        elif form.is_empty:
            syy = "is_empty"
        elif form.form_type == "tunnistamaton":
            syy = "form_type tunnistamaton"
        elif form.parse_confidence == "low" and form.form_type in ("kysymyksittain", "pykalittain"):
            # poikkeama_1: low on ohitusperuste vain osittain jäsentyneelle
            # kysymyslomakkeelle. yksi_kentta ja vapaa_asiakirja saavat
            # extractorissa AINA low (ei kysymyksiä) — ne luokitellaan
            # kokonaisena tekstinä, kehikon yksikkötaulukon mukaan.
            syy = "parse_confidence low (kysymyslomake jäsentyi osittain)"
        if syy:
            ohitetut.append({"uuid": d["uuid"], "syy": syy})
            continue
        (HERE / "teksti" / f"{d['uuid']}.txt").write_text(txt, encoding="utf-8")
        d = dict(d)
        d["form_type"] = form.form_type
        d["yksikoita"] = len(form.answers) if form.form_type not in ("yksi_kentta", "vapaa_asiakirja") else 1
        d["teksti_sha256"] = hashlib.sha256(txt.encode("utf-8")).hexdigest()
        valitut.append(d)
        time.sleep(0.5)

    if len(valitut) < N:
        print(f"VAROITUS: vain {len(valitut)} hyväksyttyä", file=sys.stderr)

    out = {
        "_schema": "aci/stance-otos/v0.1",
        "luotu": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "termit": TERMIT,
        "osumat_per_termi": osumat,
        "hankkeita": len(hankkeet),
        "raja": RAJA,
        "pois_hankkeet": sorted(POIS_HANKKEET),
        "tekstinpoiminta": "pdftotext -layout -enc UTF-8 (poppler)",
        "perusjoukko_n": len(pj),
        "perusjoukko_uuid_sha256": hashlib.sha256(
            "\n".join(d["uuid"] for d in pj).encode()).hexdigest(),
        "perusjoukko_uuid": [d["uuid"] for d in pj],
        "valitut": valitut,
        "ohitetut": ohitetut,
    }
    (HERE / "otos.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                                    encoding="utf-8")
    print(f"hankkeita {len(hankkeet)}, perusjoukko {len(pj)}, valittu {len(valitut)}, "
          f"ohitettu {len(ohitetut)}, yksiköitä {sum(d['yksikoita'] for d in valitut)}")
    return 0 if len(valitut) == N else 1


if __name__ == "__main__":
    sys.exit(main())
