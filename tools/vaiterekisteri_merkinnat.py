"""Väiterekisteri: merkintöjen mekaaninen siirto lähdetekstin perusteella.

Syy: vaiheen 2 täyttöpyyntö (katselmoinnit/vaiterekisteri-taytto-pyynto.txt, periaate 6)
käski kirjaamaan "—" sekä silloin, kun paperi merkitsee väitteen [—], että silloin, kun
merkintää ei ole. Skeema erottaa nyt nämä (`ei_merkitty`).

Sääntö (deterministinen, ei tulkintaa):
- Etsi esiintymän lainaus lähdetiedoston normalisoidusta tekstistä.
- Lue lainauksen jälkeistä tekstiä enintään IKKUNA merkkiä, mutta katkaise ensimmäiseen
  virkkeen rajaan, jota seuraa uusi virke (". " + iso kirjain tai numero) ilman välissä
  olevaa merkintää.
- Ensimmäinen merkintä [M] / [L] / [A] / [—] tällä alueella on paperin merkintä.
  Jos sellaista ei ole, merkintä on `ei_merkitty`.
- Jos lainaus itse päättyy merkintään (valinnaisesti välimerkki perässä), se on paperin merkintä.
- Jos lainausta ei löydy, rivi jätetään ennalleen ja raportoidaan.

Syöte (Kimin raakatulos) ei muutu. Tuloste on uusi tiedosto; raportti listaa jokaisen
muutetun rivin vanhan ja uuden arvon sekä lähdetekstin otteen. Suhteisiin ei kosketa.

Käyttö:
  python3 tools/vaiterekisteri_merkinnat.py SYÖTE.json --korpus POLKU --ulos TULOS.json [--raportti R.md]
Vain vakiokirjasto.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("vr", Path(__file__).with_name("vaiterekisteri.py"))
vr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vr)

IKKUNA = 200
MERKKI = re.compile(r"\[(M|L|A|—)\]")
LOPPUMERKKI = re.compile(r"\[(M|L|A|—)\]\s*[.;,]?\s*$")
VIRKERAJA = re.compile(r"[.!?]\s+(?=[A-ZÅÄÖ0-9\"(])")


def paperin_merkinta(teksti: str, lainaus: str) -> tuple[str | None, str]:
    """(merkintä tai None jos lainausta ei löydy, ote)."""
    n = vr.normalisoi(lainaus)
    i = teksti.find(n)
    if i < 0:
        return None, ""
    loppu = i + len(n)
    sisalla = LOPPUMERKKI.search(n)
    if sisalla:  # lainaus päättyy itse merkintään
        return sisalla.group(1), teksti[max(0, loppu - 60):loppu]
    alue = teksti[loppu:loppu + IKKUNA]
    m = MERKKI.search(alue)
    v = VIRKERAJA.search(alue)
    if m and (v is None or m.start() <= v.start()):
        return m.group(1), teksti[max(0, loppu - 40):loppu + m.end()]
    return "ei_merkitty", teksti[max(0, loppu - 40):loppu + 60]


def siirra(rek: dict, korpus: Path) -> tuple[dict, list[dict]]:
    uusi = copy.deepcopy(rek)
    muutokset = []
    valimuisti: dict[str, str] = {}
    for e in uusi["esiintymat"]:
        tied = e.get("tiedosto")
        if not tied:
            muutokset.append({"id": e["id"], "vanha": e["merkinta"], "uusi": None, "syy": "tiedosto puuttuu"})
            continue
        if tied not in valimuisti:
            p = vr._korpuksessa(korpus, tied)
            valimuisti[tied] = vr.normalisoi(p.read_text(encoding="utf-8")) if p and p.is_file() else ""
        merk, ote = paperin_merkinta(valimuisti[tied], e["lainaus"])
        if merk is None:
            muutokset.append({"id": e["id"], "vanha": e["merkinta"], "uusi": None, "syy": "lainausta ei löydy"})
            continue
        if merk != e["merkinta"]:
            muutokset.append({"id": e["id"], "vanha": e["merkinta"], "uusi": merk, "ote": ote})
            e["merkinta"] = merk
    uusi["merkintasiirto"] = {
        "tyokalu": "tools/vaiterekisteri_merkinnat.py",
        "saanto": "ensimmäinen [M]/[L]/[A]/[—] lainauksen jälkeen samassa virkkeessä, enintään "
                  f"{IKKUNA} merkkiä; muuten ei_merkitty",
        "muutettuja": sum(1 for m in muutokset if m.get("uusi")),
    }
    return uusi, muutokset


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("syote")
    ap.add_argument("--korpus", required=True)
    ap.add_argument("--ulos", required=True)
    ap.add_argument("--raportti")
    a = ap.parse_args(argv)
    rek = json.loads(Path(a.syote).read_text(encoding="utf-8"))
    uusi, muut = siirra(rek, Path(a.korpus))
    Path(a.ulos).write_text(json.dumps(uusi, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    rivit = [f"# Merkintäsiirto: {Path(a.syote).name} → {Path(a.ulos).name}", "",
             f"Sääntö: {uusi['merkintasiirto']['saanto']}. Suhteisiin ei kosketa.", "",
             "| id | vanha | uusi | ote lähteestä |", "|---|---|---|---|"]
    for m in muut:
        uusi_arvo = m["uusi"] or f"(ei muutettu: {m['syy']})"
        ote = (m.get("ote") or "").replace("|", "\\|")
        rivit.append(f"| {m['id']} | {m['vanha']} | {uusi_arvo} | …{ote}… |")
    teksti = "\n".join(rivit) + "\n"
    if a.raportti:
        Path(a.raportti).write_text(teksti, encoding="utf-8")
    print(teksti)
    t = vr.tarkista(uusi, Path(a.korpus))
    print(f"tarkista: KONE {len(t.kone)}, IHMINEN {len(t.ihminen)}, AVOIN {len(t.avoin)}")
    return 0 if t.ok and not any(m["uusi"] is None for m in muut) else 1


if __name__ == "__main__":
    sys.exit(main())
