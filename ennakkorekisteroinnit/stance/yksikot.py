"""Luokitteluyksiköt otoksesta — sama teksti ihmiselle ja malleille.

Kehikon yksikkötaulukon mukaan:
  kysymyksittain / pykalittain  jokainen extractorin vastaus erikseen
  yksi_kentta                   vastausten tekstit yhdessä; jos vastauksia
                                ei jäsentynyt, koko teksti
  vapaa_asiakirja               koko teksti

Tuottaa `yksikot.json` (yksiköt + teksti + sha256) ja tyhjän
koodauspohjan `ihminen.json`, jonka rekisteröijä täyttää ENNEN mallien
ajoa. Ajo:  python3 ennakkorekisteroinnit/stance/yksikot.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from extractor import parse_form  # noqa: E402

LUOKAT = ["kannattaa", "kannattaa_muutoksin", "vastustaa", "ei_kantaa", "epaselva"]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def main() -> int:
    otos = json.loads((HERE / "otos.json").read_text(encoding="utf-8"))
    yksikot = []
    for d in otos["valitut"]:
        txt = (HERE / "teksti" / f"{d['uuid']}.txt").read_text(encoding="utf-8")
        if hashlib.sha256(txt.encode()).hexdigest() != d["teksti_sha256"]:
            raise SystemExit(f"{d['uuid']}: tekstin tiiviste ei täsmää otokseen")
        form = parse_form(txt)
        if form.form_type in ("kysymyksittain", "pykalittain"):
            osat = [(i, a.section, a.text) for i, a in enumerate(form.answers)]
        elif form.form_type == "yksi_kentta" and form.answers:
            osat = [(0, None, " ".join(a.text for a in form.answers))]
        else:
            osat = [(0, None, _norm(txt))]
        for i, sec, t in osat:
            yksikot.append({
                "id": f"{d['uuid']}#{i}",
                "uuid": d["uuid"], "indeksi": i, "section": sec,
                "hanke": d["hanke"], "laatija": d["laatija"],
                "form_type": form.form_type,
                "teksti": t,
                "teksti_sha256": hashlib.sha256(t.encode()).hexdigest(),
            })
    (HERE / "yksikot.json").write_text(
        json.dumps({"_schema": "aci/stance-yksikot/v0.1", "luokat": LUOKAT,
                    "yksikot": yksikot}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    pohja = {"_schema": "aci/stance-ihminen/v0.1", "koodaaja": "Marko Ruotsalainen",
             "ohje": "stance yksi luokista; quote sanatarkka ote yksikön tekstistä "
                     "(<= 300 merkkiä), ei_kantaa voi jättää tyhjäksi. Älä katso "
                     "mallien tuloksia ennen kuin tämä on committattu.",
             "koodit": [{"id": y["id"], "stance": None, "quote": None} for y in yksikot]}
    p = HERE / "ihminen.json"
    if p.exists():
        raise SystemExit("ihminen.json on jo olemassa — ei ylikirjoiteta")
    p.write_text(json.dumps(pohja, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    pituudet = sorted(len(y["teksti"]) for y in yksikot)
    print(f"yksiköitä {len(yksikot)}, merkkejä mediaani {pituudet[len(pituudet)//2]}, "
          f"max {pituudet[-1]}, yhteensä {sum(pituudet)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
