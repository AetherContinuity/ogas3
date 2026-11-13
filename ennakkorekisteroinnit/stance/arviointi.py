"""Stance-validoinnin arviointi — kehikko.md:n "Mittarit" ja "Päätössääntö".

Kirjoitettu ja committattu ENNEN ensimmäistä mallin ajoa. Kehikon
ulkopuoliset tarkennukset (eivät muuta lukittua sääntöä, täsmentävät sen):

  T1  Virhe (API, katkennut, jäsentymätön) on oma luokkansa "virhe" ja
      lasketaan erimielisyydeksi. Pudottaminen palkitsisi epäonnistumisen.
  T2  Päätössäännön κ(ihminen) ja otehylkäys lasketaan kummastakin
      toistosta erikseen; päätös käyttää huonompaa (konservatiivinen).
  T3  κ:n 95 %:n väli: bootstrap yksiköistä, 2000 otosta, siemen 20261113.
      Väli raportoidaan; päätös tehdään pistearvolla kuten lukittu.
  T4  Otehylkäys = quote_ok == False / (yksiköt joilla stance ei ole
      ei_kantaa tai virhe). ei_kantaa ilman otetta ei ole hylkäys.
  T5  Hinta = tulosten hinta_usd-summa malli × effort -yhdistelmälle.

Ajo:  python3 ennakkorekisteroinnit/stance/arviointi.py  → arviointi.md
"""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LUOKAT = ["kannattaa", "kannattaa_muutoksin", "vastustaa", "ei_kantaa", "epaselva", "virhe"]
AVOIN = {"kimi"}            # avoimen painon mallit (kehikko: tasapelisääntö)


def kappa(a: list[str], b: list[str]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(a) | set(b)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def raaka(a, b) -> float:
    return sum(x == y for x, y in zip(a, b)) / len(a)


def bootstrap(a, b, n=2000, seed=20261113) -> tuple[float, float]:
    rnd = random.Random(seed)
    idx = range(len(a))
    vals = []
    for _ in range(n):
        s = [rnd.choice(idx) for _ in idx]
        k = kappa([a[i] for i in s], [b[i] for i in s])
        if k is not None:
            vals.append(k)
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def lue_ajo(p: Path, ids: list[str]) -> tuple[list[str], list[dict]]:
    recs = {r["id"]: r for r in json.loads(p.read_text(encoding="utf-8"))}
    out = []
    for i in ids:
        r = recs.get(i)
        out.append("virhe" if not r or r.get("virhe") or not r.get("stance") else r["stance"])
    return out, list(recs.values())


def ensimmainen_objekti(raaka: str) -> str | None:
    """Poikkeama 2: ensimmäinen kokonainen JSON-objekti, kuten stance.py:n
    jasenna()-docstring lupaa. Vain herkkyysanalyysiin."""
    i = (raaka or "").find("{")
    if i < 0:
        return None
    try:
        d, _ = json.JSONDecoder().raw_decode(raaka[i:])
    except ValueError:
        return None
    s = d.get("stance") if isinstance(d, dict) else None
    return s if s in LUOKAT[:-1] else None


def lue_ajo_herkkyys(p: Path, ids: list[str]) -> list[str]:
    recs = {r["id"]: r for r in json.loads(p.read_text(encoding="utf-8"))}
    out = []
    for i in ids:
        r = recs.get(i) or {}
        if r.get("stance") and not r.get("virhe"):
            out.append(r["stance"])
        elif (r.get("virhe") or "").startswith("jäsennys"):
            out.append(ensimmainen_objekti(r.get("raaka")) or "virhe")
        else:
            out.append("virhe")
    return out


def otehylkays(recs: list[dict]) -> float:
    arvioit = [r for r in recs if r.get("stance") and r["stance"] != "ei_kantaa" and not r.get("virhe")]
    if not arvioit:
        return 1.0
    return sum(r.get("quote_ok") is False for r in arvioit) / len(arvioit)


def matriisi(ih: list[str], ml: list[str]) -> str:
    rivit = ["| ihminen \\ malli | " + " | ".join(k[:12] for k in LUOKAT) + " |",
             "|---|" + "---|" * len(LUOKAT)]
    for r in LUOKAT[:-1]:
        rivit.append(f"| {r} | " + " | ".join(
            str(sum(1 for x, y in zip(ih, ml) if x == r and y == c)) for c in LUOKAT) + " |")
    return "\n".join(rivit)


def main() -> int:
    ihm = json.loads((HERE / "ihminen.json").read_text(encoding="utf-8"))["koodit"]
    ids = [k["id"] for k in ihm]
    ih = [k["stance"] for k in ihm]
    tdir = HERE / "tulokset"
    ajot: dict[tuple[str, str], dict[int, tuple[list[str], list[dict]]]] = {}
    for p in sorted(tdir.glob("*.json")):
        malli, effort, toisto = p.stem.rsplit("_", 2)
        ajot.setdefault((malli, effort), {})[int(toisto)] = lue_ajo(p, ids)

    md = ["# Stance — validoinnin tulokset", "",
          f"Yksiköitä {len(ids)}. Ihmisen jakauma: " +
          ", ".join(f"{k} {v}" for k, v in Counter(ih).most_common()), ""]
    yhteenveto = []
    for (malli, effort), toistot in sorted(ajot.items()):
        md.append(f"## {malli} · {effort}")
        ks, hyl, vak = [], [], None
        for t, (st, recs) in sorted(toistot.items()):
            k = kappa(ih, st)
            lo, hi = bootstrap(ih, st)
            h = otehylkays(recs)
            ks.append(k)
            hyl.append(h)
            md += [f"- toisto {t}: κ {k:.3f} (95 % {lo:.2f}–{hi:.2f}) · raaka {raaka(ih, st):.0%} · "
                   f"otehylkäys {h:.0%} · virheitä {st.count('virhe')} · "
                   f"hinta {sum(r.get('hinta_usd') or 0 for r in recs):.2f} $"]
        if len(toistot) >= 2:
            vak = kappa(toistot[1][0], toistot[2][0])
            md.append(f"- κ toistojen välillä: {vak:.3f}")
        md += ["", matriisi(ih, toistot[min(toistot)][0]), ""]
        kmin, hmax = min(ks), max(hyl)
        # hylkäysehdot ensin: otehylkäys > 5 % hylkää κ:sta riippumatta
        if kmin < 0.40 or hmax > 0.05:
            tulos = "HYLÄTÄÄN"
        elif kmin >= 0.60 and vak is not None and vak >= 0.80:
            tulos = "KÄYTTÖÖN"
        elif kmin < 0.60:
            tulos = "VAIN KAHDEN MALLIN YHTÄPITÄVISSÄ"
        else:
            tulos = "EI KÄYTTÖÖN (toistovakaus alle 0,80)"
        hinta = sum(r.get("hinta_usd") or 0 for _, (_, recs) in toistot.items() for r in recs)
        yhteenveto.append((malli, effort, kmin, hmax, vak, tulos, hinta))

    md += ["## Mallien välinen yhtäpitävyys (toisto 1)", ""]
    avaimet = sorted(ajot)
    for i, a in enumerate(avaimet):
        for b in avaimet[i + 1:]:
            if a[0] != b[0] and 1 in ajot[a] and 1 in ajot[b]:
                md.append(f"- {a[0]}:{a[1]} vs {b[0]}:{b[1]}: κ {kappa(ajot[a][1][0], ajot[b][1][0]):.3f}")
    md += ["", "## Päätössääntö (kehikko + T2)", "",
           "| malli | effort | κ(ihminen) min | otehylkäys max | κ(toistot) | tulos | hinta |",
           "|---|---|---|---|---|---|---|"]
    for m, e, k, h, v, t, hi in yhteenveto:
        md.append(f"| {m} | {e} | {k:.3f} | {h:.0%} | {'–' if v is None else f'{v:.3f}'} | {t} | {hi:.2f} $ |")

    md += ["", "## Herkkyys: jäsennin ottaa ensimmäisen JSON-objektin (poikkeama 2)", "",
           "Ensisijainen tulos ja päätössääntö yllä ovat lukitun jäsentimen mukaiset. "
           "Tässä jäsennysvirheet luetaan uudelleen ensimmäisestä kokonaisesta "
           "JSON-objektista; muut virheet pysyvät virheinä.", ""]
    for p in sorted(tdir.glob("*.json")):
        st = lue_ajo_herkkyys(p, ids)
        md.append(f"- {p.stem}: κ {kappa(ih, st):.3f} · raaka {raaka(ih, st):.0%} · "
                  f"virheitä {st.count('virhe')}")

    hyv = [y for y in yhteenveto if y[5] == "KÄYTTÖÖN"]
    md += ["", "### Valinta", ""]
    if not hyv:
        md.append("Yksikään malli × effort ei läpäissyt käyttöönottorajaa.")
    else:
        # sama malli: halvempi effort; mallien välillä avoin paino, ellei ero > 0,10
        paras = {}
        for y in hyv:
            if y[0] not in paras or y[6] < paras[y[0]][6]:
                paras[y[0]] = y
        valinta = max(paras.values(), key=lambda y: y[2])
        avoimet = [y for y in paras.values() if y[0] in AVOIN]
        if avoimet and valinta[0] not in AVOIN and valinta[2] - avoimet[0][2] <= 0.10:
            valinta = avoimet[0]
        md.append(f"**{valinta[0]} · {valinta[1]}** (κ {valinta[2]:.3f}).")
    (HERE / "arviointi.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
