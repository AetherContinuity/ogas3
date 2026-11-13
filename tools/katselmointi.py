"""Riippumaton LLM-katselmointi: lähettää pyyntötiedoston Kimi K3.1 Pro:lle
ja tallentaa vastauksen sellaisenaan.

Katselmointi on lausunto, ei mittaus: sen tulos ei muuta lukittuja
tiedostoja eikä mittaustuloksia. Löydökset tarkistetaan koodia vasten
ennen kuin niiden perusteella kirjataan mitään.

Ajo:
  MOONSHOT_API_KEY=... python3 tools/katselmointi.py katselmoinnit/q001-pyynto.txt
Tulos: katselmoinnit/<pyynnön nimi ilman -pyynto>-vastaus-<pvm>.md
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MALLI = "kimi-k3.1-pro"
EFFORT = "max"
KATTO = 32000          # tulostekatto: enintään 0,32 $ / kutsu (10 $ / Mtok)
SYSTEM = ("Olet huolellinen ja kriittinen menetelmä- ja koodikatselmoija. "
          "Vastaa suomeksi. Viittaa rivinumeroihin. Älä arvaa: jos jokin ei "
          "käy ilmi aineistosta, sano se.")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    p = Path(sys.argv[1])
    pyynto = p.read_text(encoding="utf-8")
    key = os.environ.get("MOONSHOT_API_KEY", "").strip()
    if not key:
        raise SystemExit("MOONSHOT_API_KEY puuttuu")
    body = {"model": MALLI, "reasoning_effort": EFFORT, "max_completion_tokens": KATTO,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": pyynto}]}
    req = urllib.request.Request(
        "https://api.moonshot.ai/v1/chat/completions", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": "OGAS3/0.1 katselmointi"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=1800) as r:
            j = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode(errors='replace')[:500]}")
    ch = j["choices"][0]
    u = j.get("usage") or {}
    hinta = u.get("prompt_tokens", 0) * 2 / 1e6 + u.get("completion_tokens", 0) * 10 / 1e6
    nyt = datetime.now(timezone.utc)
    nimi = p.stem.replace("-pyynto", "")
    out = p.parent / f"{nimi}-vastaus-{nyt:%Y-%m-%d}.md"
    meta = {"pyynto": str(p), "pyynto_sha256": hashlib.sha256(pyynto.encode()).hexdigest(),
            "malli": MALLI, "response_model": j.get("model"), "effort": EFFORT,
            "aika": nyt.isoformat(timespec="seconds"), "finish_reason": ch.get("finish_reason"),
            "usage": u, "hinta_usd": round(hinta, 4)}
    out.write_text(
        "# Katselmointi (LLM) — lausunto, ei mittaus\n\n```json\n"
        + json.dumps(meta, ensure_ascii=False, indent=1) + "\n```\n\n"
        + ((ch.get("message") or {}).get("content") or "(tyhjä vastaus)") + "\n",
        encoding="utf-8")
    print(f"{out} · {u.get('completion_tokens')} tok · {hinta:.3f} $ · {ch.get('finish_reason')}")
    return 0 if ch.get("finish_reason") == "stop" else 1


if __name__ == "__main__":
    sys.exit(main())
