"""Nord Pool REMIT UMM API -kokeilu: vastaako /messages ilman avainta?

Ei tallenna mitään repoon. Tulostaa kunkin kutsun tilan, vastauksen
rakenteen ja yhden esimerkkiviestin kentät. Ajo: python3 tools/umm_testi.py
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://ummapi.nordpoolgroup.com/messages"
FI = "10YFI-1--------U"
KOKEET = [
    {},
    {"limit": 5},
    {"limit": 5, "areas": FI},
    {"limit": 5, "messageTypes": "TransmissionUnavailability"},
]


def kutsu(params: dict) -> dict:
    url = BASE + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": "OGAS3/0.1 umm-testi",
                                               "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return {"url": url, "status": r.status,
                    "content_type": r.headers.get("Content-Type"), "raw": raw}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "virhe": e.read().decode(errors="replace")[:400]}
    except Exception as e:  # noqa: BLE001
        return {"url": url, "status": None, "virhe": str(e)[:400]}


def main() -> int:
    ok = False
    for p in KOKEET:
        r = kutsu(p)
        print(f"\n== {r['url']}\n   status {r['status']} · {r.get('content_type')}")
        if "virhe" in r:
            print("   virhe:", r["virhe"])
            continue
        try:
            d = json.loads(r["raw"])
        except ValueError:
            print("   ei JSON:", r["raw"][:300])
            continue
        ok = True
        if isinstance(d, dict):
            print("   avaimet:", list(d)[:15])
            items = d.get("items") or d.get("messages") or d.get("data") or []
            print("   total:", d.get("total"), "· rivejä:", len(items))
        else:
            items = d
            print("   lista, rivejä:", len(items))
        if items:
            m = items[0]
            # Vain kenttien nimet: viestien sisältöä ei tulosteta julkiseen
            # Actions-lokiin (Nord Poolin ehdot, CLAUDE.md).
            print("   esimerkin kentät:", sorted(m)[:40])
    print("\nTULOS:", "API vastaa ilman avainta" if ok else "ei vastausta ilman avainta")
    return 0


if __name__ == "__main__":
    sys.exit(main())
