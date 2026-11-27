"""Koneellinen vastatesti: ennakkokirjauksen tilan päivitys proxyn koosteesta ilman ihmistä.

Ensimmäinen kohde T1 (data/vastatestit/t1.json). Määrittely on käännös SM-024 § 06:n tekstistä;
lähdeteksti ratkaisee ristiriidassa, ja käännöksen muutos kirjataan poikkeamana.

TILAT (järjestys ratkaisee)
 1. HAVAINTO_PUUTTUU  aineistotiedosto puuttuu tai ei jäsenny; activeFrom väärä; lähde- tai
                      sha-kenttä puuttuu; tiedosto haettu ennen haettu_vahintaan (vanhentunut tai
                      kesken); rivin luku ei ole numero. Myös: ulkoinen luokitus puuttuu tai ei
                      ole sallittu arvo. Puuttuva havainto ei ole koskaan vahvistus eikä kumoutuminen.
 2. AVOIN             arviointipäivä < tarkistuspaiva. Välihavainnot (kelpaavat kuukaudet, ylitykset)
                      raportoidaan, mutta tuomiota ei anneta.
 3. RATKEAMATON       ulkoinen luokitus kuuluu ratkeamaton_jos-joukkoon, tai kelpaavia kuukausia
                      (odotuksia >= min_odotuksia) ei ole.
 4. VAHVISTUU         jokin kelpaava kuukausi: suure > raja jollekin ehdolle.
 5. KUMOUTUU          muuten.
Raja on aito ylitys (>), kuten T1:ssä ("ylittää").

Käyttö: python3 tools/vastatesti.py data/vastatestit/t1.json [--pvm YYYY-MM-DD] [--juuri .] [--out TILA.json]
Exit 0 aina kun arvio tehtiin (myös HAVAINTO_PUUTTUU); 2 jos määrittely on rikki.
Vain vakiokirjasto.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path


def _lue(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"tiedosto puuttuu: {p}"
    except (OSError, ValueError) as e:
        return None, f"tiedosto ei jäsenny: {p} ({type(e).__name__})"


def arvioi(spec: dict, juuri: Path, pvm: date) -> dict:
    a = spec["aineisto"]
    tulos = {"id": spec["id"], "arvioitu": pvm.isoformat(), "tarkistuspaiva": spec["tarkistuspaiva"],
             "tila": None, "syyt": [], "kelpaavat_kuukaudet": [], "ylitykset": [], "ulkoiset": {}}

    def puuttuu(syy):
        tulos["tila"] = "HAVAINTO_PUUTTUU"; tulos["syyt"].append(syy); return tulos

    d, virhe = _lue(juuri / a["tiedosto"])
    if virhe:
        return puuttuu(virhe)
    if not isinstance(d, dict) or not isinstance(d.get("rivit"), list):
        return puuttuu("aineistossa ei ole rivit-listaa")
    if d.get("activeFrom") != a["activeFrom"]:
        return puuttuu(f"activeFrom {d.get('activeFrom')!r} ≠ {a['activeFrom']}")
    if not d.get("lahde") or not d.get("raaka_sha256"):
        return puuttuu("lähde- tai raaka_sha256-kenttä puuttuu")
    try:
        haettu = datetime.fromisoformat(str(d.get("haettu"))).astimezone(timezone.utc).date()
    except ValueError:
        return puuttuu(f"haettu-aika ei jäsenny: {d.get('haettu')!r}")
    tulos["aineisto_haettu"] = haettu.isoformat()
    tulos["raaka_sha256"] = d["raaka_sha256"]

    kelpaavat, ylit = [], []
    for r in d["rivit"]:
        if not isinstance(r, dict) or any(r.get(k) != v for k, v in a["suodatin"].items()):
            continue
        if r.get("kuukausi") not in a["kuukaudet"]:
            continue
        n = r.get("odotuksia")
        if not isinstance(n, int) or isinstance(n, bool):
            return puuttuu(f"{r.get('kuukausi')}: odotuksia ei ole kokonaisluku")
        if n < a["min_odotuksia"]:
            continue
        kelpaavat.append(r["kuukausi"])
        for e in spec["vahvistuu_jos_jokin"]:
            x = r.get(e["suure"])
            if not isinstance(x, (int, float)) or isinstance(x, bool):
                return puuttuu(f"{r['kuukausi']}: {e['suure']} puuttuu tai ei ole luku")
            if x > e["yli"]:
                ylit.append({"kuukausi": r["kuukausi"], "suure": e["suure"], "arvo": x, "raja": e["yli"], "odotuksia": n})
    tulos["kelpaavat_kuukaudet"], tulos["ylitykset"] = kelpaavat, ylit

    tark = date.fromisoformat(spec["tarkistuspaiva"])
    if pvm < tark:
        tulos["tila"] = "AVOIN"
        tulos["syyt"].append(f"ennen tarkistuspäivää {tark}; välihavainnot eivät ole tuomio")
        return tulos
    if haettu < date.fromisoformat(a["haettu_vahintaan"]):
        return puuttuu(f"aineisto haettu {haettu}, vaaditaan ≥ {a['haettu_vahintaan']} (kausi kesken tai keruu epäonnistui)")

    ratk = []
    for u in spec.get("ulkoiset", []):
        ud, virhe = _lue(juuri / u["tiedosto"])
        arvo = ud.get(u["nimi"]) if isinstance(ud, dict) else None
        if virhe or arvo not in u["sallitut"]:
            return puuttuu(f"ulkoinen {u['nimi']} puuttuu tai ei sallittu ({virhe or repr(arvo)}); lähde: {u['lahde']}")
        tulos["ulkoiset"][u["nimi"]] = arvo
        if arvo in u["ratkeamaton_jos"]:
            ratk.append(f"{u['nimi']} = {arvo}")
    if ratk:
        tulos["tila"] = "RATKEAMATON"; tulos["syyt"] += ratk; return tulos
    if not kelpaavat:
        tulos["tila"] = "RATKEAMATON"
        tulos["syyt"].append(f"ei kuukautta, jossa ≥ {a['min_odotuksia']} odotusta")
        return tulos
    tulos["tila"] = "VAHVISTUU" if ylit else "KUMOUTUU"
    tulos["syyt"].append(f"{len(ylit)} ylitystä {len(kelpaavat)} kelpaavassa kuukaudessa")
    return tulos


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--pvm"); ap.add_argument("--juuri", default=".")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    try:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
        pvm = date.fromisoformat(a.pvm) if a.pvm else datetime.now(timezone.utc).date()
        t = arvioi(spec, Path(a.juuri), pvm)
    except (KeyError, ValueError, OSError) as e:
        print(f"määrittely rikki: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    s = json.dumps(t, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(s + "\n", encoding="utf-8")
    print(s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
