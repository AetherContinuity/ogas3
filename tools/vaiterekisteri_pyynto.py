"""Väiterekisterin vaihe 2: Kimin täyttöpyynnön tekstiosan purku HTML-papereista.

Purkaa paperin <body>-osan tekstiksi niin, että jokainen rivi on normalisoituna
(vaiterekisteri.normalisoi) alimerkkijono koko tiedoston normalisoidusta tekstistä:
tagit korvataan välilyönnillä kuten normalisoi() tekee, lohkotagit rivinvaihdolla.
Siten rivin sisältä otettu sanatarkka lainaus läpäisee tarkista --korpus -ehdon.
Otsikkorivit merkitään '## [kohta: ...]'. Kohta-tunnus: paperin oma §-merkki,
muuten otsikon oma numero, muuten otsikon teksti.

Käyttö: python3 tools/vaiterekisteri_pyynto.py KORPUS PAPERI.html [...]  > teksti
Vain vakiokirjasto.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from vaiterekisteri import normalisoi  # noqa: E402

LOHKO = r"(?:p|div|h[1-6]|li|ul|ol|tr|table|thead|tbody|section|blockquote|br|dt|dd|dl|pre|figure|figcaption|caption|hr)"


def pura(raw: str) -> list[str]:
    t = re.sub(r"<(style|script)\b.*?</\1>", " ", raw, flags=re.S | re.I)
    m = re.search(r"<body\b[^>]*>(.*)</body>", t, flags=re.S | re.I)
    t = m.group(1) if m else t
    t = re.sub(r"<nav\b.*?</nav>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    # merkit otsikoille ja §-merkeille ennen tagien poistoa
    t = re.sub(r'<span class="section-marker">(.*?)</span>', lambda m: f"\n\x01MARK{m.group(1)}\x02\n", t, flags=re.S)
    t = re.sub(r"<(h[23])\b[^>]*>(.*?)</\1>", lambda m: f"\n\x01{m.group(1).upper()}{m.group(2)}\x02\n", t, flags=re.S | re.I)
    t = re.sub(rf"</?{LOHKO}\b[^>]*>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    rivit, marker, h2 = [], None, None
    for r in t.split("\n"):
        r = re.sub(r"\s+", " ", r.replace(" ", " ")).strip()
        if not r:
            continue
        mm = re.fullmatch(r"\x01(MARK|H2|H3)(.*)\x02", r)
        if not mm:
            rivit.append(r)
            continue
        laji, teksti = mm.group(1), mm.group(2).strip()
        if laji == "MARK":
            marker = teksti if teksti.startswith("§") else None
            if not marker:
                rivit.append(teksti)
            continue
        num = re.match(r"^(\d+(?:\.\d+)*[a-z]?)\.?\s", teksti)
        if laji == "H2":
            h2 = marker or (f"§ {num.group(1)}" if num else f"§ {teksti}")
            kohta = h2
            marker = None
        else:
            osa = num.group(1) if num else teksti
            kohta = f"{h2} / {osa}" if h2 else f"§ {osa}"
        rivit.append(f"## [kohta: {kohta}] {teksti}")
    return rivit


def main() -> int:
    korpus = Path(sys.argv[1])
    for rel in sys.argv[2:]:
        raw = (korpus / rel).read_text(encoding="utf-8")
        koko = normalisoi(raw)
        rivit = pura(raw)
        for r in rivit:
            if not r.startswith("## ") and normalisoi(r) not in koko:
                raise SystemExit(f"{rel}: rivi ei ole normalisoidun tiedoston alimerkkijono: {r[:80]}")
        print(f"===== TIEDOSTO: {rel} =====")
        print("## [kohta: alku] (otsikkoa edeltävä teksti)")
        print("\n".join(rivit))
        print(f"===== LOPPU: {rel} =====\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
