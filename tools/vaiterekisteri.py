"""Väiterekisteri v0.1 — skeema, validointi ja kyselyt (vaihe 1).

Määrittely: aethercontinuity.github.io/SEURANTA.md, "Idea: korpuksen väiterekisteri"
ja hyväksymistesti H1. Tämä työkalu EI sisällä H1:tä eikä sen tulosjoukkoa; H1 on
suljettu hyväksymistesti, jota käytetään vasta sokkotäytön (vaihe 2) jälkeen.

TIETOMALLI
- Yksikkö on väitteen ESIINTYMÄ: yksi rajattu väite yhdessä paperin kohdassa.
  Sama väite eri papereissa on eri esiintymiä, jotka yhdistää `same_claim`-suhde.
  Esiintymiä ei koskaan yhdistetä yhdeksi olioksi.
- Suhteet ovat omia rivejään ja kantavat oman evidenssinsä.

  esiintymat[]: id, paperi, kohta, lainaus, merkinta (M|L|A|—),
                tiedosto (valinnainen, polku korpuksen juuresta), countertest (valinnainen)
  suhteet[]:    id, lahde, kohde, laji, perustelu, kirjaaja,
                tarkistaja (valinnainen), tila (ehdotettu|tarkistettu|hylatty)

  laji:
    depends_on  lahde nojaa kohteeseen argumentissaan (suunnattu)
    same_claim  sama väite toisessa paikassa tai toisin sanoin (suuntaamaton)
    qualifies   lahde rajaa tai tarkentaa kohdetta (suunnattu)
    related     sama aihe, riippuvuutta ei osoitettu (suuntaamaton); ei koskaan riippuvuus

  countertest: condition, evidence_required, status (not_specified|not_tested|tested), note
    `tested` = määritelty testi on suoritettu, EI että väite olisi vahvistettu.

VALIDOINTI erottaa kolme luokkaa:
  KONE      koneellisesti tarkistettavat ehdot (rakenne, viitteet, kaksoiskappaleet,
            syklit, lainauksen sanatarkkuus kun korpus annetaan). Virhe = exit 1.
  IHMINEN   semanttiset ehdot, joita kone ei voi todentaa: suhteen oikeellisuus,
            väitteen rajaus. Listataan arvioitaviksi, ei hylätä.
  AVOIN     ehdot, joita ei vielä ole tarkistettu (lainaus ilman korpusta,
            suhde ilman tarkistajaa).
  KONE-luokan läpäisy ei kerro mitään sisällön oikeellisuudesta.

Käyttö:
  python3 tools/vaiterekisteri.py tarkista REK.json [--korpus POLKU]
  python3 tools/vaiterekisteri.py alavirta REK.json ID
  python3 tools/vaiterekisteri.py ylavirta REK.json ID
  python3 tools/vaiterekisteri.py ryhmat REK.json
  python3 tools/vaiterekisteri.py rajaukset REK.json ID
  python3 tools/vaiterekisteri.py liittyvat REK.json ID
Vain vakiokirjasto.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

LAJIT = {"depends_on", "same_claim", "qualifies", "related"}
SUUNTAAMATTOMAT = {"same_claim", "related"}
MERKINNAT = {"M", "L", "A", "—"}
CT_TILAT = {"not_specified", "not_tested", "tested"}
SUHDE_TILAT = {"ehdotettu", "tarkistettu", "hylatty"}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:\-]*$")


def normalisoi(teksti: str) -> str:
    """HTML pois, entiteetit auki, välilyönnit yhdeksi, lainausmerkit yhtenäisiksi."""
    t = re.sub(r"<(style|script)\b.*?</\1>", " ", teksti, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = t.replace(" ", " ").replace("”", '"').replace("“", '"').replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


class Tulos:
    def __init__(self) -> None:
        self.kone: list[str] = []
        self.ihminen: list[str] = []
        self.avoin: list[str] = []

    @property
    def ok(self) -> bool:
        return not self.kone


def tarkista(rek: dict, korpus: Path | None = None) -> Tulos:
    r = Tulos()
    if not isinstance(rek, dict):
        r.kone.append("juuri ei ole objekti")
        return r
    es = rek.get("esiintymat")
    su = rek.get("suhteet")
    if not isinstance(es, list) or not isinstance(su, list):
        r.kone.append("puuttuu lista 'esiintymat' tai 'suhteet'")
        return r

    ids: dict[str, dict] = {}
    for i, e in enumerate(es):
        paikka = f"esiintymat[{i}]"
        if not isinstance(e, dict):
            r.kone.append(f"{paikka}: ei objekti")
            continue
        for k in ("id", "paperi", "kohta", "lainaus", "merkinta"):
            if not isinstance(e.get(k), str) or not e.get(k).strip():
                r.kone.append(f"{paikka}: kenttä '{k}' puuttuu tai on tyhjä")
        eid = e.get("id")
        if isinstance(eid, str):
            if not ID_RE.match(eid):
                r.kone.append(f"{paikka}: virheellinen id '{eid}'")
            if eid in ids:
                r.kone.append(f"{paikka}: id '{eid}' toistuu")
            ids[eid] = e
        if e.get("merkinta") not in MERKINNAT:
            r.kone.append(f"{paikka}: merkinta '{e.get('merkinta')}' ei ole {sorted(MERKINNAT)}")
        ct = e.get("countertest")
        if ct is not None:
            if not isinstance(ct, dict):
                r.kone.append(f"{paikka}: countertest ei objekti")
            else:
                st = ct.get("status")
                if st not in CT_TILAT:
                    r.kone.append(f"{paikka}: countertest.status '{st}' ei ole {sorted(CT_TILAT)}")
                if st in ("not_tested", "tested"):
                    for k in ("condition", "evidence_required"):
                        if not (ct.get(k) or "").strip():
                            r.kone.append(f"{paikka}: countertest.{k} vaaditaan, kun status = {st}")
                if st == "tested" and not (ct.get("note") or "").strip():
                    r.kone.append(f"{paikka}: countertest.note vaaditaan, kun status = tested")
                if st != "tested" and (ct.get("note") or "").strip():
                    r.kone.append(f"{paikka}: countertest.note sallitaan vain, kun status = tested")
        elif e.get("merkinta") == "A":
            r.ihminen.append(f"{eid}: [A]-väite ilman countertestiä (sallittu; harkitse not_specified)")
        # lainauksen sanatarkkuus
        lainaus = e.get("lainaus") or ""
        tied = e.get("tiedosto")
        if korpus is None or not tied:
            r.avoin.append(f"{eid}: lainausta ei tarkistettu lähdettä vasten"
                           + ("" if tied else " (tiedosto puuttuu)"))
        else:
            p = (korpus / tied)
            if not p.is_file():
                r.kone.append(f"{eid}: tiedostoa ei löydy: {tied}")
            elif normalisoi(lainaus) not in normalisoi(p.read_text(encoding="utf-8")):
                r.kone.append(f"{eid}: lainaus ei löydy sanatarkasti tiedostosta {tied}")

    nahdyt: set[tuple] = set()
    sids: set[str] = set()
    for i, s in enumerate(su):
        paikka = f"suhteet[{i}]"
        if not isinstance(s, dict):
            r.kone.append(f"{paikka}: ei objekti")
            continue
        for k in ("id", "lahde", "kohde", "laji", "perustelu", "kirjaaja"):
            if not isinstance(s.get(k), str) or not s.get(k).strip():
                r.kone.append(f"{paikka}: kenttä '{k}' puuttuu tai on tyhjä")
        sid, a, b, laji = s.get("id"), s.get("lahde"), s.get("kohde"), s.get("laji")
        if isinstance(sid, str):
            if sid in sids:
                r.kone.append(f"{paikka}: suhde-id '{sid}' toistuu")
            sids.add(sid)
        if laji not in LAJIT:
            r.kone.append(f"{paikka}: laji '{laji}' ei ole {sorted(LAJIT)}")
        for nimi, x in (("lahde", a), ("kohde", b)):
            if isinstance(x, str) and x not in ids:
                r.kone.append(f"{paikka}: {nimi} '{x}' ei ole esiintymä")
        if a == b and a is not None:
            r.kone.append(f"{paikka}: suhde itseensä ({a})")
        tila = s.get("tila", "ehdotettu")
        if tila not in SUHDE_TILAT:
            r.kone.append(f"{paikka}: tila '{tila}' ei ole {sorted(SUHDE_TILAT)}")
        if tila == "tarkistettu" and not (s.get("tarkistaja") or "").strip():
            r.kone.append(f"{paikka}: tila 'tarkistettu' vaatii tarkistajan")
        if tila == "tarkistettu" and (s.get("tarkistaja") or "").strip() == (s.get("kirjaaja") or "").strip():
            r.kone.append(f"{paikka}: tarkistaja ei voi olla sama kuin kirjaaja")
        avain = (laji, *sorted((a or "", b or ""))) if laji in SUUNTAAMATTOMAT else (laji, a, b)
        if avain in nahdyt:
            r.kone.append(f"{paikka}: sama suhde toistuu ({laji} {a}–{b})")
        nahdyt.add(avain)
        if laji in LAJIT:
            if tila == "ehdotettu":
                r.avoin.append(f"{sid}: {laji} {a} → {b} tarkistamatta")
            if laji in ("depends_on", "same_claim") and tila == "ehdotettu":
                r.ihminen.append(f"{sid}: {laji} {a} → {b}: onko suhde osoitettu argumentista eikä samankaltaisuudesta?")

    # ristiriidat saman parin välillä
    pari = defaultdict(set)
    for s in su:
        if isinstance(s, dict) and s.get("laji") in LAJIT and s.get("tila", "ehdotettu") != "hylatty":
            pari[frozenset((s.get("lahde"), s.get("kohde")))].add(s.get("laji"))
    for p, lajit in pari.items():
        if "related" in lajit and lajit & {"depends_on", "same_claim"}:
            r.kone.append(f"pari {sorted(p)}: 'related' ja {sorted(lajit & {'depends_on','same_claim'})} samaan aikaan")
        if "same_claim" in lajit and "depends_on" in lajit:
            r.kone.append(f"pari {sorted(p)}: 'same_claim' ja 'depends_on' samaan aikaan")

    # depends_on-syklit
    g = defaultdict(list)
    for s in su:
        if isinstance(s, dict) and s.get("laji") == "depends_on" and s.get("tila", "ehdotettu") != "hylatty":
            g[s.get("lahde")].append(s.get("kohde"))
    vari: dict[str, int] = {}

    def dfs(u: str, polku: list[str]) -> None:
        vari[u] = 1
        for v in g.get(u, []):
            if vari.get(v) == 1:
                kierros = polku[polku.index(v):] + [v] if v in polku else [u, v]
                r.kone.append("depends_on-sykli: " + " → ".join(kierros))
            elif vari.get(v) is None:
                dfs(v, polku + [v])
        vari[u] = 2

    for u in list(g):
        if vari.get(u) is None:
            dfs(u, [u])
    return r


# --- kyselyt -------------------------------------------------------------

def _aktiiviset(rek: dict, laji: str) -> list[dict]:
    return [s for s in rek["suhteet"] if s["laji"] == laji and s.get("tila", "ehdotettu") != "hylatty"]


def ryhmat(rek: dict) -> list[list[str]]:
    """same_claim-ryhmät (yhtenäiset komponentit). Esiintymät säilyvät erillisinä."""
    naap = defaultdict(set)
    for s in _aktiiviset(rek, "same_claim"):
        naap[s["lahde"]].add(s["kohde"])
        naap[s["kohde"]].add(s["lahde"])
    nahty, out = set(), []
    for u in sorted(naap):
        if u in nahty:
            continue
        comp, q = [], deque([u])
        nahty.add(u)
        while q:
            x = q.popleft()
            comp.append(x)
            for y in sorted(naap[x]):
                if y not in nahty:
                    nahty.add(y)
                    q.append(y)
        out.append(sorted(comp))
    return out


def _ryhma(rek: dict, eid: str) -> list[str]:
    for g in ryhmat(rek):
        if eid in g:
            return g
    return [eid]


def _virta(rek: dict, eid: str, ylos: bool) -> list[tuple[str, str]]:
    """Transitiivinen depends_on. Polku näytetään vaiheittain; same_claim-hyppy
    merkitään '=' ja depends_on '→'. Esiintymää ei koskaan väitetä riippuvaksi
    suoraan, jos yhteys kulkee same_claim-ryhmän kautta: polku näyttää välivaiheen."""
    ulos = defaultdict(list)  # lahde -> kohde (lahde nojaa kohteeseen)
    sisaan = defaultdict(list)
    for s in _aktiiviset(rek, "depends_on"):
        ulos[s["lahde"]].append(s["kohde"])
        sisaan[s["kohde"]].append(s["lahde"])
    seur = ulos if ylos else sisaan
    tulos: list[tuple[str, str]] = []
    nahty = {eid}
    q = deque()
    for m in _ryhma(rek, eid):
        alku = eid if m == eid else f"{eid} = {m}"
        nahty.add(m)
        q.append((m, alku))
    while q:
        x, polku = q.popleft()
        for y in sorted(seur.get(x, [])):
            if y in nahty:
                continue
            nahty.add(y)
            p = f"{polku} {'→' if ylos else '←'} {y}"
            tulos.append((y, p))
            q.append((y, p))
            for m in _ryhma(rek, y):
                if m not in nahty:
                    nahty.add(m)
                    pm = f"{p} = {m}"
                    tulos.append((m, pm))
                    q.append((m, pm))
    return tulos


def alavirta(rek: dict, eid: str) -> list[tuple[str, str]]:
    """Esiintymät, jotka nojaavat eid:hen (tai sen same_claim-ryhmään)."""
    return _virta(rek, eid, ylos=False)


def ylavirta(rek: dict, eid: str) -> list[tuple[str, str]]:
    """Esiintymät, joihin eid (tai sen same_claim-ryhmä) nojaa."""
    return _virta(rek, eid, ylos=True)


def rajaukset(rek: dict, eid: str) -> list[tuple[str, str]]:
    """qualifies-suhteet, jotka rajaavat eid:tä tai sen same_claim-ryhmää."""
    ryhma = set(_ryhma(rek, eid))
    out = []
    for s in _aktiiviset(rek, "qualifies"):
        if s["kohde"] in ryhma:
            via = "" if s["kohde"] == eid else f" (via {eid} = {s['kohde']})"
            out.append((s["lahde"], f"{s['lahde']} rajaa {s['kohde']}{via}: {s['perustelu']}"))
    return out


def liittyvat(rek: dict, eid: str) -> list[tuple[str, str]]:
    """related-suhteet. Eivät koskaan näy alavirrassa tai ylävirrassa."""
    out = []
    for s in _aktiiviset(rek, "related"):
        if eid in (s["lahde"], s["kohde"]):
            muu = s["kohde"] if s["lahde"] == eid else s["lahde"]
            out.append((muu, f"{eid} ~ {muu}: {s['perustelu']}"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("komento", choices=["tarkista", "alavirta", "ylavirta", "ryhmat", "rajaukset", "liittyvat"])
    ap.add_argument("rekisteri")
    ap.add_argument("id", nargs="?")
    ap.add_argument("--korpus")
    a = ap.parse_args(argv)
    rek = json.loads(Path(a.rekisteri).read_text(encoding="utf-8"))
    if a.komento == "tarkista":
        t = tarkista(rek, Path(a.korpus) if a.korpus else None)
        for nimi, lista in (("KONE", t.kone), ("IHMINEN", t.ihminen), ("AVOIN", t.avoin)):
            print(f"{nimi} ({len(lista)})")
            for x in lista:
                print("  " + x)
        print("Kone-ehdot " + ("läpi" if t.ok else "EIVÄT läpi")
              + ". Kone-ehtojen läpäisy ei kerro sisällön oikeellisuudesta.")
        return 0 if t.ok else 1
    if a.komento == "ryhmat":
        for g in ryhmat(rek):
            print(" = ".join(g))
        return 0
    if not a.id:
        ap.error("id vaaditaan")
    t = tarkista(rek)
    if not t.ok:
        print("Rekisteri ei läpäise kone-ehtoja; aja ensin 'tarkista'.", file=sys.stderr)
        return 1
    fn = {"alavirta": alavirta, "ylavirta": ylavirta, "rajaukset": rajaukset, "liittyvat": liittyvat}[a.komento]
    for _, rivi in fn(rek, a.id):
        print(rivi)
    return 0


if __name__ == "__main__":
    sys.exit(main())
