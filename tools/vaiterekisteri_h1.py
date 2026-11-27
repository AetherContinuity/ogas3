"""Väiterekisteri vaihe 3: hyväksymistesti H1, ensisijainen vertailu (H1 vs Kimin raakatulos).

H1: sivuston repon SEURANTA.md, "Väiterekisteri — hyväksymistesti H1" (lukittu PR #84, 27.11.2026).
Raakatulos: katselmoinnit/vaiterekisteri-taytto-kimi.json (PR #45). Korpus: sivuston repo @ adb800b.

TÄMÄ TIEDOSTO KIRJATAAN ENNEN AJOA. Jänteet ja säännöt on johdettu H1:n kohtakuvauksista ja
lähdetekstistä; niitä ei muuteta ajon tuloksen perusteella. Rajoite: kirjoittaja (Claude, istunto
joka laati H1:n) on nähnyt osan Kimin lainauksista merkintäsiirron raportissa (PR #46) ennen
jänteiden määrittelyä. Jänteet ovat kokonaisia kappaleita tai osioita, eivät yksittäisiä lainauksia.

KOHDISTUS (deterministinen)
- Jokainen H1-kohta on jänne lähdetekstissä: paperi, alkuankkuri (mukana), loppuankkuri (pois).
- Kimin esiintymä kuuluu kohtaan, jos paperi täsmää ja lainauksen alkukohta normalisoidussa
  tekstissä on jänteen sisällä. Kohtaan voi kuulua 0..n esiintymää.
- U4 (WP-019, SM-009, CN-007) ja kriteeri 6 (poissuljetut paperit) ovat täytön rajauksen
  ulkopuolella: tulos "ei testattavissa".

KRITEERIT (H1:n numerointi)
 1  D1 → F3 depends_on: jokin D1:n esiintymä nojaa (suoraan) johonkin F3:n same_claim-ryhmän jäseneen.
 2  S1 samassa same_claim-ryhmässä kuin F3; S2 samassa ryhmässä kuin U2.
 3  Jokaiselle U1–U3: jokin esiintymä on F3:n ylävirrassa eikä mikään sen esiintymä F3:n alavirrassa.
 4  Q1, Q2a, Q2b: qualifies-suhde F3:n ryhmään (rajaukset-kysely).
 5  X1, X2, I1, I2: ei yhtään esiintymää F3:n ryhmässä, alavirrassa tai ylävirrassa.
    Lisäksi raportoidaan, onko related-suhde F3:n ryhmään kirjattu (tieto, ei läpäisyehto,
    koska täyttöpyyntö salli suhteen jättämisen kirjaamatta).
 6  Ei testattavissa.
 7  tarkista --korpus: KONE 0 (lainaukset sanatarkkoja, jokaisella suhteella perustelu ja kirjaaja).
Kohta, jolle ei löydy esiintymää, raportoidaan "ei poimittu"; kriteeri ei silloin täyty.

Käyttö: python3 tools/vaiterekisteri_h1.py REK.json --korpus POLKU [--raportti R.md]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_s = importlib.util.spec_from_file_location("vr", Path(__file__).with_name("vaiterekisteri.py"))
vr = importlib.util.module_from_spec(_s)
_s.loader.exec_module(vr)

TIEDOSTOT = {
    "WP-020": "papers/wp-020-perameri-logistics-energy-ecosystem.html",
    "CN-008": "papers/cn-008-perameri-logistiikka-energiaekosysteemi.html",
    "CN-030": "papers/cn-030-variable-gauge-huckepack-network.html",
    "SM-024": "papers/sm-024-pohjoinen-solmu.html",
}
# kohta: (paperi, alkuankkuri, loppuankkuri)
JANTEET = {
    "F3":  ("WP-020", "Finding 3 — Coordination Failure", "Finding 4 — Foreign"),
    "D1":  ("WP-020", "Assign coordination responsibility", "Include freight logistics resilience"),
    "S1":  ("CN-008", "Pullonkaula on koordinaatio.", "Perämeren alueella on käynnissä"),
    "S2":  ("CN-008", "Transfennica operoi", "Sama kolmen vajeen rakenne"),
    "X1":  ("CN-008", "Suljettu kiertotalousmalli on teknisesti valmis", "Pullonkaula on koordinaatio."),
    "X2":  ("CN-008", "Volyymi on olemassa jos toimijat koordinoivat", "Laajempi analyysi"),
    "Q1":  ("SM-024", "Mitä tämä tarkoittaa korpukselle", "§ 03 Pohjoismaiset"),
    "Q2a": ("WP-020", "Scope note 2026-11-27", "Finding 1 — Technical"),
    "Q2b": ("CN-008", "Rajaushuomio 27.11.2026", "Mitä tarvitaan"),
    "I1":  ("CN-030", "Kuka omistaa kokonaisuuden", "9. Tutkimusasetelma"),
    "I2":  ("WP-020", "Finding 5 — Route-Level", "Recommendations for state actors"),
    "U1":  ("WP-020", "1.1 Energy: Laanila", "1.2 Logistics"),
    "U2":  ("WP-020", "Historical Context", "Illustrative Mechanism"),
    "U3":  ("WP-020", "§ 03 The Coordination Failure", "Four-Phase Action Model"),
}


def kohdista(rek: dict, korpus: Path) -> dict[str, list[str]]:
    tekstit = {p: vr.normalisoi((korpus / f).read_text(encoding="utf-8")) for p, f in TIEDOSTOT.items()}
    rajat = {}
    for k, (p, a, b) in JANTEET.items():
        t = tekstit[p]
        i = t.find(a)
        j = t.find(b, i + len(a)) if i >= 0 else -1
        if i < 0 or j < 0 or t.count(a) != 1:
            raise SystemExit(f"jänne {k}: ankkuri puuttuu tai ei yksiselitteinen")
        rajat[k] = (p, i, j)
    out = {k: [] for k in JANTEET}
    for e in rek["esiintymat"]:
        p = e["paperi"]
        if p not in tekstit:
            continue
        pos = tekstit[p].find(vr.normalisoi(e["lainaus"]))
        for k, (kp, i, j) in rajat.items():
            if kp == p and i <= pos < j:
                out[k].append(e["id"])
    return out


def arvioi(rek: dict, korpus: Path) -> tuple[list[tuple[str, str, str]], dict]:
    m = kohdista(rek, korpus)
    F3 = m["F3"]
    ryhma = set()
    for f in F3:
        ryhma |= set(vr._ryhma(rek, f))
    ala, yla = set(), set()
    for f in F3:
        ala |= {x for x, _ in vr.alavirta(rek, f)}
        yla |= {x for x, _ in vr.ylavirta(rek, f)}
    dep = [s for s in vr._aktiiviset(rek, "depends_on")]
    tulos = []

    def ei_poimittu(*kk):
        puuttuu = [k for k in kk if not m[k]]
        return f"ei poimittu: {', '.join(puuttuu)}" if puuttuu else ""

    if not F3:
        tulos.append(("0", "HYLÄTTY", "F3:a ei poimittu; vertailua ei voi tehdä"))
        return tulos, m
    # 1
    ok1 = any(s["lahde"] in m["D1"] and s["kohde"] in ryhma for s in dep)
    tulos.append(("1", "LÄPI" if ok1 else "EI", ei_poimittu("D1") or ("depends_on D1 → F3-ryhmä" + (" löytyi" if ok1 else " puuttuu"))))
    # 2
    ok_s1 = any(x in ryhma for x in m["S1"])
    u2r = set().union(*(set(vr._ryhma(rek, u)) for u in m["U2"])) if m["U2"] else set()
    ok_s2 = any(x in u2r and x not in m["U2"] for x in m["S2"])
    tulos.append(("2", "LÄPI" if ok_s1 and ok_s2 else "EI",
                  ei_poimittu("S1", "S2", "U2") or f"S1 F3:n ryhmässä: {ok_s1}; S2 U2:n ryhmässä: {ok_s2}"))
    # 3
    osat = []
    ok3 = True
    for u in ("U1", "U2", "U3"):
        if not m[u]:
            osat.append(f"{u} ei poimittu"); ok3 = False; continue
        ylos = any(x in yla for x in m[u]); alas = any(x in ala for x in m[u])
        osat.append(f"{u}: ylävirrassa {ylos}, alavirrassa {alas}")
        ok3 = ok3 and ylos and not alas
    tulos.append(("3", "LÄPI" if ok3 else "EI", "; ".join(osat) + "; U4 ei testattavissa"))
    # 4
    raj = set()
    for f in F3:
        raj |= {x for x, _ in vr.rajaukset(rek, f)}
    osat, ok4 = [], True
    for q in ("Q1", "Q2a", "Q2b"):
        if not m[q]:
            osat.append(f"{q} ei poimittu"); ok4 = False; continue
        hit = any(x in raj for x in m[q]); osat.append(f"{q}: {hit}"); ok4 = ok4 and hit
    tulos.append(("4", "LÄPI" if ok4 else "EI", "; ".join(osat)))
    # 5
    osat, ok5 = [], True
    rel = [s for s in vr._aktiiviset(rek, "related")]
    for x in ("X1", "X2", "I1", "I2"):
        if not m[x]:
            osat.append(f"{x} ei poimittu (ei väärää riippuvuutta)"); continue
        vaara = [e for e in m[x] if e in ryhma or e in ala or e in yla]
        r = any((s["lahde"] in m[x] and s["kohde"] in ryhma) or (s["kohde"] in m[x] and s["lahde"] in ryhma) for s in rel)
        osat.append(f"{x}: väärä yhteys {vaara or 'ei'}; related kirjattu {r}")
        ok5 = ok5 and not vaara
    tulos.append(("5", "LÄPI" if ok5 else "EI", "; ".join(osat)))
    tulos.append(("6", "EI TESTATTAVISSA", "poissuljetut paperit eivät olleet täytön aineistossa"))
    t = vr.tarkista(rek, korpus)
    tulos.append(("7", "LÄPI" if t.ok else "EI", f"KONE {len(t.kone)}"))
    return tulos, m


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rekisteri"); ap.add_argument("--korpus", required=True); ap.add_argument("--raportti")
    a = ap.parse_args(argv)
    rek = json.loads(Path(a.rekisteri).read_text(encoding="utf-8"))
    tulos, m = arvioi(rek, Path(a.korpus))
    lainaus = {e["id"]: e["lainaus"] for e in rek["esiintymat"]}
    r = [f"# H1, ensisijainen vertailu: {Path(a.rekisteri).name}", "",
         "Sääntö ja jänteet: `tools/vaiterekisteri_h1.py` (kirjattu ennen ajoa).", "",
         "## Kriteerit", "", "| # | tulos | peruste |", "|---|---|---|"]
    r += [f"| {k} | {t} | {p} |" for k, t, p in tulos]
    r += ["", "## Kohdistus", "", "| H1-kohta | Kimin esiintymät | lainaus (alku) |", "|---|---|---|"]
    for k, ids in m.items():
        if not ids:
            r.append(f"| {k} | — | |")
        for i in ids:
            r.append(f"| {k} | {i} | {lainaus[i][:90].replace('|', '/')}… |")
    teksti = "\n".join(r) + "\n"
    if a.raportti:
        Path(a.raportti).write_text(teksti, encoding="utf-8")
    print(teksti)
    return 0


if __name__ == "__main__":
    sys.exit(main())
