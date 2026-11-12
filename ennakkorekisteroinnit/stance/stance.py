"""Stance-validoinnin mallien ajo — kehikko.md:n "Ajot"-osion toteutus.

Ajaa jokaisen yksikön (`yksikot.json`) annetuilla malli × effort ×
toisto -yhdistelmillä ja kirjoittaa tietueet `tulokset/`-hakemistoon
skeemalla `aci/stance/v0.1`. Ei lue `ihminen.json`:ia.

KUSTANNUSRAJAT
  tulostekatto / kutsu   low 8 000, muut 16 000 tokenia (päättely + vastaus)
  budjetti / koko ajo     --budjetti (oletus 15 $). Ylitys keskeyttää ajon;
                          jo kirjoitetut tulokset jäävät.
  hinnat                  2 $ / 10 $ per Mtok kummallekin mallille (12.11.2026)

MALLIN VAIHTUMINEN
  Vastauksen `model` tallennetaan jokaiseen tietueeseen. Jos arvo muuttuu
  saman mallin ajojen välillä, ajo keskeytyy (kehikko: Tietohorisontti).

VIRHEET
  API-virhe, katkennut vastaus (tulostekatto) tai jäsentymätön JSON
  kirjataan tietueeseen `virhe`-kenttään, stance = null. Ei arvata.

Ajo:
  MOONSHOT_API_KEY=... OGAS3ANTH_API_KEY=... \\
    python3 ennakkorekisteroinnit/stance/stance.py \\
      --ajot kimi:low,kimi:max,sonnet:low,sonnet:high --toistot 2
  --kuiva  rakentaa kutsut mutta ei lähetä (tarkistus)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA = "aci/stance/v0.1"

MALLIT = {
    "kimi": {
        "id": "kimi-k3.1-pro",
        "version": "kimi-k3.1-pro/cutoff=release-upper-bound",
        "knowledge_cutoff": "2026-10-23T23:59:59+00:00",
        "efforts": {"low", "high", "max"},
        "avain": "MOONSHOT_API_KEY",
        "hinta": (2.0, 10.0),
    },
    "sonnet": {
        "id": "claude-sonnet-5-5",
        "version": "claude-sonnet-5-5/cutoff=published-training-data",
        "knowledge_cutoff": "2026-06-30T23:59:59+00:00",
        "efforts": {"low", "medium", "high", "max"},
        "avain": "OGAS3ANTH_API_KEY",
        "hinta": (2.0, 10.0),
    },
}
LUOKAT = ("kannattaa", "kannattaa_muutoksin", "vastustaa", "ei_kantaa", "epaselva")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def lue_prompt() -> tuple[str, str, str]:
    raw = (HERE / "prompt.md").read_bytes()
    txt = raw.decode("utf-8")
    sysm = re.search(r"<!-- SYSTEM -->\n(.*?)\n<!-- /SYSTEM -->", txt, re.S)
    usrm = re.search(r"<!-- USER -->\n(.*?)\n<!-- /USER -->", txt, re.S)
    if not sysm or not usrm:
        raise SystemExit("prompt.md: SYSTEM- tai USER-lohko puuttuu")
    return sysm.group(1), usrm.group(1), hashlib.sha256(raw).hexdigest()


def user_viesti(pohja: str, y: dict) -> str:
    kohta = y["section"] and f"§/luku {y['section']}" or (
        "koko lausunto" if y["form_type"] in ("yksi_kentta", "vapaa_asiakirja")
        else "yleinen kenttä")
    # str.replace eikä format: teksti voi sisältää aaltosulkeita
    return (pohja.replace("{hanke_nimi}", y.get("hanke_nimi") or "(ei tiedossa)")
                 .replace("{laatija}", y.get("laatija") or "(ei tiedossa)")
                 .replace("{kohta}", kohta)
                 .replace("{teksti}", y["teksti"]))


def _http(url: str, headers: dict, body: dict, yrityksia: int = 3) -> dict:
    data = json.dumps(body).encode()
    for i in range(yrityksia):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:500]
            if e.code in (429, 500, 502, 503, 529) and i < yrityksia - 1:
                time.sleep(10 * (i + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {msg}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if i < yrityksia - 1:
                time.sleep(10 * (i + 1))
                continue
            raise RuntimeError(f"verkko: {e}") from None
    raise RuntimeError("ei vastausta")


def kutsu(malli: str, effort: str, system: str, user: str, katto: int) -> dict:
    """Palauttaa {teksti, response_model, tin, tout, katkesi}."""
    m = MALLIT[malli]
    key = os.environ.get(m["avain"], "").strip()
    if not key:
        raise SystemExit(f"{m['avain']} puuttuu")
    if malli == "kimi":
        j = _http("https://api.moonshot.ai/v1/chat/completions",
                  {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                   "User-Agent": "OGAS3/0.1 stance"},
                  {"model": m["id"], "reasoning_effort": effort,
                   "max_completion_tokens": katto,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}]})
        ch = (j.get("choices") or [{}])[0]
        u = j.get("usage") or {}
        return {"teksti": (ch.get("message") or {}).get("content") or "",
                "response_model": j.get("model"),
                "tin": u.get("prompt_tokens", 0), "tout": u.get("completion_tokens", 0),
                "katkesi": ch.get("finish_reason") == "length"}
    j = _http("https://api.anthropic.com/v1/messages",
              {"x-api-key": key, "anthropic-version": "2023-06-01",
               "content-type": "application/json", "User-Agent": "OGAS3/0.1 stance"},
              {"model": m["id"], "max_tokens": katto, "system": system,
               "thinking": {"type": "adaptive"}, "output_config": {"effort": effort},
               "messages": [{"role": "user", "content": user}]})
    u = j.get("usage") or {}
    txt = "".join(b.get("text", "") for b in j.get("content") or [] if b.get("type") == "text")
    return {"teksti": txt, "response_model": j.get("model"),
            "tin": u.get("input_tokens", 0), "tout": u.get("output_tokens", 0),
            "katkesi": j.get("stop_reason") == "max_tokens"}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def jasenna(teksti: str) -> dict:
    """Ottaa ensimmäisen JSON-objektin vastauksesta. Ei korjaa sisältöä."""
    t = teksti.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        raise ValueError("ei JSON-objektia")
    d = json.loads(m.group(0))
    s = d.get("stance")
    if s not in LUOKAT:
        raise ValueError(f"tuntematon luokka: {s!r}")
    q = d.get("quote")
    if q is not None and not isinstance(q, str):
        raise ValueError("quote ei ole merkkijono")
    return {"stance": s, "quote": q or ""}


def ote_ok(quote: str, teksti: str, stance: str) -> bool | None:
    if not quote:
        return None if stance == "ei_kantaa" else False
    return len(quote) <= 300 and _norm(quote) in _norm(teksti)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ajot", default="kimi:low,kimi:max,sonnet:low,sonnet:high")
    ap.add_argument("--toistot", type=int, default=2)
    ap.add_argument("--budjetti", type=float, default=15.0)
    ap.add_argument("--kuiva", action="store_true")
    a = ap.parse_args()

    system, user_pohja, phash = lue_prompt()
    yk = json.loads((HERE / "yksikot.json").read_text(encoding="utf-8"))["yksikot"]
    ajot = []
    for s in a.ajot.split(","):
        malli, effort = s.strip().split(":")
        if malli not in MALLIT or effort not in MALLIT[malli]["efforts"]:
            raise SystemExit(f"tuntematon ajo {s}")
        ajot.append((malli, effort))

    out_dir = HERE / "tulokset"
    out_dir.mkdir(exist_ok=True)
    kulut = 0.0
    nahty_malli: dict[str, str] = {}
    print(f"prompt_hash {phash[:16]} · yksiköitä {len(yk)} · ajoja {len(ajot) * a.toistot}")

    for toisto in range(1, a.toistot + 1):
        for malli, effort in ajot:
            m = MALLIT[malli]
            katto = 8000 if effort == "low" else 16000
            tiedosto = out_dir / f"{malli}_{effort}_{toisto}.json"
            if tiedosto.exists():
                vanha = json.loads(tiedosto.read_text(encoding="utf-8"))
                # Korvataan VAIN jos yksikään malli ei nähnyt yhtään yksikköä:
                # jokainen tietue on virhe eikä yhdestäkään ole usage-tietoa
                # (pyyntö hylättiin ennen mallia, esim. HTTP 400). Muuten
                # olemassa oleva tulos säilyy aina.
                if vanha and all(r.get("virhe") and not r.get("usage") for r in vanha):
                    print(f"{tiedosto.name}: kaikki {len(vanha)} tietuetta hylättyjä pyyntöjä "
                          f"ilman mallin vastausta — ajetaan uudelleen. Ensimmäinen virhe: "
                          f"{vanha[0]['virhe'][:300]}")
                else:
                    print(f"{tiedosto.name} on jo olemassa — ohitetaan")
                    continue
            tietueet = []
            for y in yk:
                user = user_viesti(user_pohja, y)
                if a.kuiva:
                    continue
                rec = {"_schema": SCHEMA, "id": y["id"], "uuid": y["uuid"],
                       "indeksi": y["indeksi"], "section": y["section"],
                       "teksti_sha256": y["teksti_sha256"],
                       "classified_at": _now(),
                       "classifier": {"kind": "llm", "id": m["id"], "version": m["version"],
                                      "knowledge_cutoff": m["knowledge_cutoff"],
                                      "prompt_hash": phash},
                       "effort": effort, "toisto": toisto,
                       "stance": None, "quote": None, "quote_ok": None, "virhe": None}
                try:
                    r = kutsu(malli, effort, system, user, katto)
                except Exception as exc:          # noqa: BLE001 — kirjataan
                    rec["virhe"] = str(exc)[:500]
                    tietueet.append(rec)
                    print(f"  {y['id'][-8:]} VIRHE {rec['virhe'][:300]}")
                    continue
                hin, hout = m["hinta"]
                hinta = r["tin"] * hin / 1e6 + r["tout"] * hout / 1e6
                kulut += hinta
                rec.update({"response_model": r["response_model"],
                            "usage": {"in": r["tin"], "out": r["tout"]},
                            "hinta_usd": round(hinta, 5)})
                rm = r["response_model"]
                if rm and nahty_malli.setdefault(malli, rm) != rm:
                    tietueet.append(rec)
                    tiedosto.write_text(json.dumps(tietueet, ensure_ascii=False, indent=1) + "\n",
                                        encoding="utf-8")
                    print(f"KESKEYTYS: {malli} vastasi mallilla {rm}, aiemmin {nahty_malli[malli]}")
                    return 3
                if r["katkesi"]:
                    rec["virhe"] = "tulostekatto ylittyi — vastaus katkesi"
                else:
                    try:
                        p = jasenna(r["teksti"])
                        rec["stance"], rec["quote"] = p["stance"], p["quote"]
                        rec["quote_ok"] = ote_ok(p["quote"], y["teksti"], p["stance"])
                    except Exception as exc:      # noqa: BLE001
                        rec["virhe"] = f"jäsennys: {exc}"
                        rec["raaka"] = r["teksti"][:1000]
                tietueet.append(rec)
                print(f"  {malli}:{effort}#{toisto} {y['id'][-8:]} {rec['stance'] or rec['virhe'][:40]}"
                      f" · {r['tout']} tok · yht {kulut:.2f} $")
                if kulut > a.budjetti:
                    tiedosto.write_text(json.dumps(tietueet, ensure_ascii=False, indent=1) + "\n",
                                        encoding="utf-8")
                    print(f"KESKEYTYS: budjetti {a.budjetti} $ ylittyi ({kulut:.2f} $)")
                    return 4
            if not a.kuiva:
                tiedosto.write_text(json.dumps(tietueet, ensure_ascii=False, indent=1) + "\n",
                                    encoding="utf-8")
                print(f"{tiedosto.name} kirjoitettu · kulut yht {kulut:.2f} $")

    if a.kuiva:
        pit = [len(system) + len(user_viesti(user_pohja, y)) for y in yk]
        print(f"kuiva ajo OK · merkkejä / kutsu: max {max(pit)}, yht {sum(pit)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
