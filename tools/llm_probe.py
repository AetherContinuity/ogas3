"""OGAS3 — LLM-luokittelijan esitarkistus (ei luokittele mitään).

MIKSI
-----
classification.py hyväksyy llm-luokituksen CLEAN-tilaan vain, jos
luokittelijan knowledge_cutoff tunnetaan. Moonshot ei julkaise Kimi
K3.1 Pro:n cutoffia, joten horisonttina käytetään julkaisupäivää
ylärajana (2026-10-23). Yläraja pätee vain, jos rajapinnan takana oleva
malli ei vaihdu. Tämä skripti selvittää, voiko sen todentaa:

  1. GET /models          — onko päivättyjä snapshot-tunnisteita?
  2. yksi minimikutsu      — mitä vastauksen `model` ja
                             `system_fingerprint` kertovat, ja miten
                             päättelytokenit näkyvät `usage`-kentässä.

Kustannus: yksi lyhyt kutsu, reasoning_effort=low. Alle 0,01 $.

Avain luetaan ympäristömuuttujasta MOONSHOT_API_KEY. Sitä ei tulosteta,
ei kirjoiteta tiedostoon eikä lähetetä minnekään muualle.

Käyttö:
    MOONSHOT_API_KEY=... python3 tools/llm_probe.py [--model kimi-k3.1-pro] [--out probe.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE_URL = os.environ.get("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
UA = "OGAS3/0.1 llm_probe"

# Vastauksen otsakkeista talteen vain nämä. Ei koko otsakejoukkoa:
# siinä voi olla tilikohtaisia tunnisteita.
KEEP_HEADERS = ("date", "x-request-id", "openai-model", "x-model", "x-model-version")


def _req(method: str, path: str, key: str, body: dict | None = None) -> tuple[int, dict, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": UA,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            hdrs = {k.lower(): v for k, v in r.headers.items() if k.lower() in KEEP_HEADERS}
            return r.status, hdrs, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw[:2000]}
        return e.code, {}, payload


def probe(key: str, model: str) -> dict:
    out: dict = {
        "probed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base_url": BASE_URL,
        "requested_model": model,
    }

    # 1. Mallilista
    st, _, models = _req("GET", "/models", key)
    out["models_status"] = st
    ids = sorted(m.get("id", "") for m in models.get("data", [])) if st == 200 else []
    out["models_all"] = ids
    out["models_kimi"] = [i for i in ids if "k3" in i.lower()]
    # Päivätty tunniste = 8 numeron jakso, esim. -20261023
    out["dated_ids"] = [i for i in out["models_kimi"]
                        if any(p.isdigit() and len(p) == 8 for p in i.replace("_", "-").split("-"))]
    if st != 200:
        out["models_error"] = models

    # 2. Minimikutsu
    body = {
        "model": model,
        "reasoning_effort": "low",
        "max_completion_tokens": 2048,
        "messages": [{"role": "user", "content": "Vastaa yhdellä sanalla: ok"}],
    }
    st, hdrs, resp = _req("POST", "/chat/completions", key, body)
    out["chat_status"] = st
    out["chat_headers"] = hdrs
    if st == 200:
        out["response_model"] = resp.get("model")
        out["system_fingerprint"] = resp.get("system_fingerprint")
        out["response_created"] = resp.get("created")
        out["usage"] = resp.get("usage")
        msg = (resp.get("choices") or [{}])[0].get("message", {})
        out["content"] = msg.get("content")
        # Päättelyteksti voi tulla omassa kentässään; talteen vain pituus.
        rc = msg.get("reasoning_content")
        out["reasoning_content_chars"] = len(rc) if isinstance(rc, str) else None
        out["response_keys"] = sorted(resp.keys())
    else:
        out["chat_error"] = resp

    # 3. Johtopäätös ylärajasäännön kannalta
    verdict = []
    if out["dated_ids"]:
        verdict.append(f"Päivättyjä tunnisteita on: {out['dated_ids']}. Kiinnitä luokittelija niistä yhteen.")
    else:
        verdict.append("Ei päivättyjä tunnisteita. Ylärajasääntö vaatii vastauksen `model`/"
                       "`system_fingerprint`-kentän tallentamisen jokaiseen tietueeseen ja "
                       "ajon keskeytyksen, jos arvo muuttuu.")
    if out.get("response_model") and out["response_model"] != model:
        verdict.append(f"Alias ratkesi eri nimeen: {model} -> {out['response_model']}.")
    if st == 200 and not out.get("system_fingerprint"):
        verdict.append("system_fingerprint puuttuu: mallin vaihtumista ei voi havaita sen kautta.")
    out["verdict"] = verdict
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", default="kimi-k3.1-pro")
    ap.add_argument("--out", default=None, help="kirjoita tulos JSON-tiedostoon")
    a = ap.parse_args()

    key = os.environ.get("MOONSHOT_API_KEY", "").strip()
    if not key:
        print("MOONSHOT_API_KEY puuttuu.", file=sys.stderr)
        return 2

    res = probe(key, a.model)
    txt = json.dumps(res, ensure_ascii=False, indent=2)
    if key in txt:                      # ei pitäisi koskaan tapahtua
        print("VIRHE: avain päätyi tulosteeseen, ei kirjoiteta.", file=sys.stderr)
        return 3
    print(txt)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(txt + "\n")
    return 0 if res.get("chat_status") == 200 else 1


if __name__ == "__main__":
    sys.exit(main())
