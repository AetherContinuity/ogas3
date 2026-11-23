"""Lukuinventaario: ACI-korpuksen talousluvut ja niiden alkuperä.

Poimii HTML-dokumenteista kannattavuus- ja kustannusluvut (IRR, takaisinmaksu,
€/t, €/MWh, €/kW, M€/v, CAPEX) ja luokittelee kunkin luvun ympäristön
perusteella. Deterministinen: regex, ei LLM:ää.

Luokat (ensimmäinen osuma voittaa):
  MP      viittaa "Master Package" -analyysiin (TN-001-dashboardin esiaste)
  A       [A]-oletusmerkintä tai "assumption"/"oletus" ±250 merkin sisällä
  LÄHDE   ulkoinen lähde ±250 merkin sisällä (URL, nimetty julkaisija, "Source:")
  SISÄINEN  viittaa vain toiseen ACI-dokumenttiin (SP-/SM-/TN-/WP-/DA-/CN-)
  EI      ei mitään edellisistä

Luokitus kertoo, onko luvun vieressä merkintä alkuperästä — ei sitä, onko
luku oikein. Se on katselmoinnin lähtölista, ei tulos.

Ajo:
  python3 tools/lukuinventaario.py <aethercontinuity.github.io-polku> > tulos.md
"""

from __future__ import annotations

import html
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

LUKU = re.compile(
    r"(IRR[^.;]{0,40}?\d+(?:[.,]\d+)?\s*(?:–|-|to)?\s*\d*(?:[.,]\d+)?\s*%"
    r"|\d+(?:[.,]\d+)?\s*(?:–|-)\s*\d+(?:[.,]\d+)?\s*(?:yr|years|vuotta|v)\b[^.;]{0,20}payback"
    r"|payback[^.;]{0,40}?\d+(?:[.,]\d+)?(?:\s*(?:–|-)\s*\d+(?:[.,]\d+)?)?\s*(?:yr|years|vuotta|y)\b"
    r"|takaisinmaksu[^.;]{0,40}?\d+(?:[.,]\d+)?(?:\s*(?:–|-)\s*\d+(?:[.,]\d+)?)?\s*v"
    r"|€\s?\d[\d,. ]*(?:–\d[\d,. ]*)?\s?(?:M|Bn|bn|mrd)?\s?/\s?(?:t|MWh|kW|MW|y|year|v|a)\b"
    r"|\d[\d,. ]*(?:–\d[\d,. ]*)?\s?(?:M€|€|EUR)\s?/\s?(?:t|MWh|kW|MW|y|year|v|a|vuosi)\b"
    r"|CAPEX[^.;]{0,30}?(?:€\s?)?\d[\d,.]*\s?(?:–\s?\d[\d,.]*)?\s?(?:M€|M|Bn|bn|mrd)"
    r"|EBITDA[^.;]{0,30}?(?:€\s?)?\d[\d,.]*\s?(?:–\s?\d[\d,.]*)?\s?(?:M€|M))",
    re.I)

MP = re.compile(r"master\s+package", re.I)
OLETUS = re.compile(r"\[A\]|\bassum(?:ption|ed)\b|\boletus\b|\boletettu\b", re.I)
LAHDE = re.compile(
    r"https?://|\bsource:|\blähde:|\b(?:IEA|IRENA|ACER|Eurostat|Fingrid|ENTSO-?E|"
    r"Tilastokeskus|Statistics Finland|Systemiq|Argus|Platts|S&P|BNEF|Lazard|"
    r"Energiavirasto|Huoltovarmuuskeskus|Business Finland|TEM\b|VTT|LUT|AFRY|"
    r"Hydrogen Observatory|European Commission|EIB|Gasgrid|Nord Pool|Methanex)", re.I)
SISAINEN = re.compile(r"\b(?:SP|SM|TN|WP|DA|CN|DT|DRD)-\d{2,3}", re.I)


def teksti(p: Path) -> str:
    t = p.read_text(encoding="utf-8", errors="ignore")
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>", " ", t, flags=re.S | re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)


def luokka(ymp: str) -> str:
    if MP.search(ymp):
        return "MP"
    if OLETUS.search(ymp):
        return "A"
    if LAHDE.search(ymp):
        return "LÄHDE"
    if SISAINEN.search(ymp):
        return "SISÄINEN"
    return "EI"


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    juuri = Path(sys.argv[1])
    tiedostot = sorted([*juuri.glob("papers/*.html"), *juuri.glob("supplements/*.html")])
    rivit, perdoc = [], defaultdict(Counter)
    for f in tiedostot:
        t = teksti(f)
        for m in LUKU.finditer(t):
            a, b = m.span()
            ymp = t[max(0, a - 250): b + 250]
            k = luokka(ymp)
            doc = f.name.replace(".html", "")
            perdoc[doc][k] += 1
            rivit.append((doc, k, m.group(0).strip()[:70], t[max(0, a - 90): b + 60].strip()))
    tot = Counter(k for _, k, _, _ in rivit)
    print("# Lukuinventaario — ACI-korpuksen talousluvut\n")
    print(f"Dokumentteja {len(tiedostot)}, lukuja {len(rivit)}. Luokat: "
          + ", ".join(f"{k} {v}" for k, v in tot.most_common()) + "\n")
    print("Luokitus kertoo alkuperämerkinnän olemassaolon, ei luvun oikeellisuutta.\n")
    print("## Dokumentit, joissa on IRR- tai takaisinmaksulukuja\n")
    print("| Dokumentti | MP | A | LÄHDE | SISÄINEN | EI |\n|---|---|---|---|---|---|")
    kannatt = {d for d, _, l, _ in rivit if re.search(r"IRR|payback|takaisinmaksu", l, re.I)}
    for d in sorted(kannatt, key=lambda d: -sum(perdoc[d].values())):
        c = perdoc[d]
        print(f"| {d} | {c['MP']} | {c['A']} | {c['LÄHDE']} | {c['SISÄINEN']} | {c['EI']} |")
    print("\n## Kaikki luvut\n")
    print("| Dokumentti | Luokka | Luku | Konteksti |\n|---|---|---|---|")
    for d, k, l, ctx in rivit:
        ctx = ctx.replace("|", "/")
        print(f"| {d} | {k} | {l.replace('|', '/')} | {ctx} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
