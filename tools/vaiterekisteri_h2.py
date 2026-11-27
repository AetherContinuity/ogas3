"""Väiterekisteri vaihe 3: hyväksymistesti H2 (CN-030 luku 10, "Miksi tätä ei ole laskettu").

H2: sivuston repon SEURANTA.md, "Väiterekisteri — hyväksymistesti H2" (PR #85) ja "H2 — lisäys 1"
(PR #86), 27.11.2026. Korpus: sivuston repo @ adb800b.

TÄMÄ TIEDOSTO KIRJATAAN ENNEN AJOA. Kirjoittaja (Claude, istunto joka laati H1:n ja H2:n) ei ole
avannut täytön v2 raakatulosta; se on nähnyt sen yhteenvetotilastot (lisäys 1) ja täytön 1
raakatuloksen. Jänteitä ja sääntöjä ei muuteta ajon tuloksen perusteella.

KOHDISTUS (sama kuin vaiterekisteri_h1.py)
- Jokainen H2-kohta on jänne: paperi, alkuankkuri (mukana), loppuankkuri (pois).
- Esiintymä kuuluu kohtaan, jos lainauksen alkukohta normalisoidussa tekstissä on jänteen sisällä.
  Lainaus, joka alkaa yhdestä kohdasta ja jatkuu seuraavaan, kuuluu vain alkukohtaansa; tällaiset
  raportoidaan tietona ("ylittää jänteen").

SUHTEEN TULKINTA
- "suora suhde X–Y": aktiivinen (ei hylatty) suhde, jonka toinen pää on X:n ja toinen Y:n
  same_claim-ryhmässä. T:n ryhmä = T:n esiintymien same_claim-ryhmien yhdiste.
- "T depends_on X": lahde T:n ryhmässä, kohde X:n ryhmässä.

KRITEERIT (H2:n numerointi; kattavuus 1–5, tarkkuus 6–8, alkuperä 9)
 1  T depends_on U1 suoraan, ja ainakin yksi tällainen suhde on perustaltaan eksplisiittinen.
 2  T depends_on U2 ja T depends_on U3 suoraan. Pelkkä välillinen ylävirta raportoidaan, ei täytä.
    Mikään U2:n tai U3:n esiintymä ei ole T:n alavirrassa.
 3  Kriteerien 1–2 suorista suhteista: U1:n suhde ei ole rekonstruoitu; U2:n ja U3:n suhteet
    eivät ole eksplisiittisiä. Puuttuva perusta ei täytä. U1:n rekonstruoidun suhteen perustelu
    tulostetaan, jotta epävarmuussäännön osuus voidaan erottaa (lisäys 1).
 4  O1 on I1:n same_claim-ryhmässä.
 5  Q1 qualifies T (lahde Q1, kohde T:n ryhmässä). P1 (P1a tai P1b) depends_on U2 suoraan, eikä
    yksikään P1:n esiintymä ole T:n ryhmässä, T:n alavirrassa tai suorassa suhteessa T:hen.
 6  Rajatapaukset, suorat suhteet T:hen. Luokka hyväksytty / väärä luokitus / puuttuu (lisäys 1).
      R1, I1: hyväksytty related tai rekonstruoitu depends_on (kumpaan suuntaan tahansa);
              puuttuu = ei suoraa suhdetta (ei täytä).
      U4:     hyväksytty T depends_on U4 rekonstruoitu, related, tai ei suhdetta.
      S1:     hyväksytty related, T depends_on S1 rekonstruoitu, tai ei suhdetta; S1 same_claim
              U4 raportoidaan tietona. Väärä: S1 T:n same_claim-ryhmässä.
    Kaikissa: eksplisiittinen tai perustaton depends_on, qualifies tai same_claim T:n kanssa = väärä.
 7  N1 (WP-020 F3, sama jänne kuin H1): ei suoraa depends_on-suhdetta T:hen eikä samaa
    same_claim-ryhmää. N2–N5 eivät olleet täytön aineistossa: ei testattavissa.
 8  Ei testattavissa (poissuljetut paperit eivät olleet täytön aineistossa).
 9  tarkista --korpus: KONE 0.
Kohta, jolle ei löydy esiintymää, raportoidaan "ei poimittu"; kriteeri ei silloin täyty
(paitsi rajatapauksissa, joissa puuttuminen on hyväksytty luokka).

Käyttö: python3 tools/vaiterekisteri_h2.py REK.json --korpus POLKU [--raportti R.md]
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
JANTEET = {
    "T":   ("CN-030", "Poolausarvo ja kapasiteettiketjun pienin lenkki", "Tämä ei ole hankesuositus."),
    "U1":  ("CN-030", "Miksi tätä ei ole laskettu", "Poolausarvo ja kapasiteettiketjun pienin lenkki"),
    "Q1":  ("CN-030", "Tämä ei ole hankesuositus.", "Tarkistamatta"),
    "U2":  ("CN-030", "4.2 Poolausarvo", "5. Kotimaan"),
    "U3":  ("CN-030", "Kapasiteettiketjun lenkki", "8.3 Kolme porrasta"),
    "U4":  ("CN-030", "Väylävirasto vastaa kysymykseen, siirtyisikö", "4.2 Poolausarvo"),
    "S1":  ("CN-030", "Poolattu, monikäyttöinen kalusto on laskematta", "Valtion linja on rinnakkaisraide"),
    "P1a": ("CN-030", "Säädettävä teli ei valitse suuntaa", "Kysyntää samalle leveysparille on myös Baltiassa"),
    "P1b": ("CN-030", "Nootin oma lisä on poolausarvo", "Ratapölkkykoe."),
    "R1":  ("CN-030", "9. Tutkimusasetelma", "Telispeksi ja preemio vähintään kahdelta"),
    "I1":  ("CN-030", "Kuka omistaa kokonaisuuden", "9. Tutkimusasetelma"),
    "O1":  ("SM-024", "CN-030 : länsikäytävän läpäisykyvylle", "Valmiuden vähimmäissisältö erottaa"),
    "N1":  ("WP-020", "Finding 3 — Coordination Failure", "Finding 4 — Foreign"),
}


def kohdista(rek: dict, korpus: Path):
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
    yli = []
    for e in rek["esiintymat"]:
        p = e["paperi"]
        if p not in tekstit:
            continue
        lz = vr.normalisoi(e["lainaus"])
        pos = tekstit[p].find(lz)
        for k, (kp, i, j) in rajat.items():
            if kp == p and i <= pos < j:
                out[k].append(e["id"])
                if pos + len(lz) > j:
                    yli.append(f"{e['id']} ({k})")
    return out, yli


def arvioi(rek: dict, korpus: Path):
    m, yli = kohdista(rek, korpus)

    def ryhma(k):
        g = set()
        for x in m[k]:
            g |= set(vr._ryhma(rek, x))
        return g

    G = {k: ryhma(k) for k in JANTEET}
    TG = G["T"]
    akt = [s for s in rek["suhteet"] if s.get("tila", "ehdotettu") != "hylatty"]
    ala, yla = set(), set()
    for t in m["T"]:
        ala |= {x for x, _ in vr.alavirta(rek, t)}
        yla |= {x for x, _ in vr.ylavirta(rek, t)}

    def t_dep(k):
        return [s for s in akt if s["laji"] == "depends_on" and s["lahde"] in TG and s["kohde"] in G[k]]

    def suorat(k):
        return [s for s in akt if s["laji"] != "same_claim" and (
            (s["lahde"] in G[k] and s["kohde"] in TG) or (s["kohde"] in G[k] and s["lahde"] in TG))]

    def kuvaa(ss):
        return ", ".join(f"{s['id']} {s['laji']} {s['lahde']}→{s['kohde']} [{s.get('perusta') or 'ei perustaa'}]" for s in ss) or "ei"

    tulos, info = [], []
    if not m["T"]:
        return [("0", "HYLÄTTY", "T:tä ei poimittu; vertailua ei voi tehdä")], m, yli, info

    # 1
    d1 = t_dep("U1")
    ok1 = bool(m["U1"]) and any(s.get("perusta") == "eksplisiittinen" for s in d1)
    tulos.append(("1", "LÄPI" if ok1 else "EI", "ei poimittu: U1" if not m["U1"] else f"T depends_on U1: {kuvaa(d1)}"))
    # 2
    osat, ok2 = [], True
    for u in ("U2", "U3"):
        if not m[u]:
            osat.append(f"{u} ei poimittu"); ok2 = False; continue
        d = t_dep(u)
        valill = any(x in yla for x in m[u])
        alas = any(x in ala for x in m[u])
        osat.append(f"{u}: suora {kuvaa(d)}; ylävirrassa {valill}; alavirrassa {alas}")
        ok2 = ok2 and bool(d) and not alas
    tulos.append(("2", "LÄPI" if ok2 else "EI", "; ".join(osat)))
    # 3
    osat, ok3 = [], True
    if d1:
        for s in d1:
            if s.get("perusta") != "eksplisiittinen":
                ok3 = False
            if s.get("perusta") == "rekonstruoitu":
                info.append(f"U1 rekonstruoitu {s['id']}, perustelu: {s.get('perustelu', '')}")
        osat.append(f"U1: {[s.get('perusta') for s in d1]}")
    else:
        ok3 = False; osat.append("U1: ei suoraa suhdetta")
    for u in ("U2", "U3"):
        d = t_dep(u)
        if not d:
            ok3 = False; osat.append(f"{u}: ei suoraa suhdetta"); continue
        ps = [s.get("perusta") for s in d]
        osat.append(f"{u}: {ps}")
        if any(p != "rekonstruoitu" for p in ps):
            ok3 = False
    tulos.append(("3", "LÄPI" if ok3 else "EI", "; ".join(osat)))
    # 4
    ok4 = bool(m["O1"]) and bool(m["I1"]) and any(x in G["I1"] for x in m["O1"])
    tulos.append(("4", "LÄPI" if ok4 else "EI",
                  "ei poimittu: " + ", ".join(k for k in ("O1", "I1") if not m[k]) if not (m["O1"] and m["I1"]) else f"O1 I1:n ryhmässä: {ok4}"))
    # 5
    q = [s for s in akt if s["laji"] == "qualifies" and s["lahde"] in G["Q1"] and s["kohde"] in TG]
    p1 = m["P1a"] + m["P1b"]
    p1g = G["P1a"] | G["P1b"]
    p1_u2 = [s for s in akt if s["laji"] == "depends_on" and s["lahde"] in p1g and s["kohde"] in G["U2"]]
    p1_vaara = [x for x in p1 if x in TG or x in ala] + [s["id"] for s in akt if s["laji"] != "same_claim" and (
        (s["lahde"] in p1g and s["kohde"] in TG) or (s["kohde"] in p1g and s["lahde"] in TG))]
    ok5 = bool(q) and bool(p1_u2) and not p1_vaara
    tulos.append(("5", "LÄPI" if ok5 else "EI",
                  f"Q1 {'ei poimittu' if not m['Q1'] else 'qualifies T: ' + kuvaa(q)}; "
                  f"P1 {'ei poimittu' if not p1 else 'depends_on U2: ' + kuvaa(p1_u2) + '; väärä yhteys T:hen: ' + (', '.join(p1_vaara) or 'ei')}"))
    # 6
    osat, ok6 = [], True
    for k in ("R1", "I1", "U4", "S1"):
        if not m[k]:
            luokka = "puuttuu" if k in ("R1", "I1") else "hyväksytty (ei poimittu)"
        else:
            ss = suorat(k)
            sama = any(x in TG for x in m[k])
            vaarat = [s for s in ss if s["laji"] == "qualifies" or (
                s["laji"] == "depends_on" and s.get("perusta") != "rekonstruoitu")]
            if k == "U4":
                vaarat += [s for s in ss if s["laji"] == "depends_on" and s["lahde"] in G["U4"]]
            if k == "S1":
                vaarat += [s for s in ss if s["laji"] == "depends_on" and s["lahde"] in G["S1"]]
            if sama or vaarat:
                luokka = "väärä luokitus" + (" (same_claim T)" if sama else "")
            elif ss:
                luokka = "hyväksytty"
            else:
                luokka = "puuttuu" if k in ("R1", "I1") else "hyväksytty (ei suhdetta)"
            luokka += f": {kuvaa(ss)}"
            if k == "S1":
                luokka += f"; S1 U4:n ryhmässä {any(x in G['U4'] for x in m['S1'])}"
            alas_yla = [x for x in m[k] if x in ala or x in yla]
            if alas_yla:
                luokka += f"; välillisesti T:n ylä- tai alavirrassa {alas_yla}"
        osat.append(f"{k}: {luokka}")
        ok6 = ok6 and luokka.startswith("hyväksytty")
    tulos.append(("6", "LÄPI" if ok6 else "EI", "; ".join(osat)))
    # 7
    if not m["N1"]:
        tulos.append(("7", "LÄPI", "N1 ei poimittu; N2–N5 ei testattavissa"))
    else:
        dn = [s for s in akt if s["laji"] == "depends_on" and (
            (s["lahde"] in G["N1"] and s["kohde"] in TG) or (s["kohde"] in G["N1"] and s["lahde"] in TG))]
        sama = any(x in TG for x in m["N1"])
        muut = [s for s in suorat("N1") if s not in dn]
        valill = [x for x in m["N1"] if x in ala or x in yla]
        ok7 = not dn and not sama
        tulos.append(("7", "LÄPI" if ok7 else "EI",
                      f"N1 depends_on: {kuvaa(dn)}; same_claim T: {sama}; muut suorat: {kuvaa(muut)}; "
                      f"välillisesti {valill or 'ei'}; N2–N5 ei testattavissa"))
    tulos.append(("8", "EI TESTATTAVISSA", "poissuljetut paperit eivät olleet täytön aineistossa"))
    t = vr.tarkista(rek, korpus)
    tulos.append(("9", "LÄPI" if t.ok else "EI", f"KONE {len(t.kone)}"))
    return tulos, m, yli, info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rekisteri"); ap.add_argument("--korpus", required=True); ap.add_argument("--raportti")
    a = ap.parse_args(argv)
    rek = json.loads(Path(a.rekisteri).read_text(encoding="utf-8"))
    tulos, m, yli, info = arvioi(rek, Path(a.korpus))
    lainaus = {e["id"]: e["lainaus"] for e in rek["esiintymat"]}
    r = [f"# H2: {Path(a.rekisteri).name}", "",
         "Sääntö ja jänteet: `tools/vaiterekisteri_h2.py` (kirjattu ennen ajoa).", "",
         "## Kriteerit", "", "| # | tulos | peruste |", "|---|---|---|"]
    r += [f"| {k} | {t} | {p.replace('|', '/')} |" for k, t, p in tulos]
    if info or yli:
        r += ["", "## Tieto", ""]
        r += [f"- {x}" for x in info]
        if yli:
            r.append(f"- Lainaus ylittää jänteen: {', '.join(yli)}")
    r += ["", "## Kohdistus", "", "| H2-kohta | esiintymät | lainaus (alku) |", "|---|---|---|"]
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
