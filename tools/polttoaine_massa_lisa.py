"""Polttoainekoe 2, lisäanalyysit (katselmointi 28.11.2026). Eivät korvaa tulos-2:ta.

L1  Samat sarjat: ehdoton ja Brent-tapahtumasuodatettu ajo samoilla 40 sarjalla ja 810 parilla
    (suodatetun ajon sarjajoukko) → erottaa suodatuksen vaikutuksen verkon koon muutoksesta.
L2  NB-p:n kalibrointi tämän kokeen mittakaavassa: nolladata, jossa on kokeen sarjojen omat tapahtumaprosessit
    mutta ei todellista keskinäistä ajoitusta (A ja B eri vuosikymmeniltä).
    Mitataan (a) yksittäisten testien osuus p ≤ 0,05 ja p ≤ 0,01 ja (b) BH-ehdokkaiden määrä.
L3  Jaksojen todelliset havaintorajat.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import synapsi as sy  # noqa: E402
import polttoaine_massa as pm  # noqa: E402

SA = {"tyyppi": "kynnys", "ehto": ">=", "raja": 1}


def main() -> int:
    wob = json.loads(Path("data/polttoaine/wob-kaikki.json").read_text(encoding="utf-8"))
    brent = {date.fromisoformat(r["Date"]): float(r["Price"]) for r in csv.DictReader(open(sys.argv[1])) if r["Price"]}
    out = {}
    sar = {(j, e): pm.sarjat_jaksolle(wob, brent, al, lo, e) for j, (al, lo) in pm.JAKSOT.items() for e in (False, True)}
    out["L3_havaintorajat"] = {j: [sar[(j, False)][0][0], sar[(j, False)][0][-1]] for j in pm.JAKSOT}
    # L1
    s_e = {j: sar[(j, True)][1] for j in pm.JAKSOT}
    mukana = [k for k in s_e["loyto"] if k in s_e["vahvistus"]
              and all(len(sy.aktivaatiot(s_e[j][k], SA)) >= pm.MIN_AKT for j in pm.JAKSOT)]
    parit = [(a, b) for a in mukana for b in mukana if a != b and a.rsplit("_", 1)[1] == b.rsplit("_", 1)[1]]
    L1 = {}
    for nimi, ehd in (("ehdoton", False), ("suodatettu", True)):
        S = {j: sar[(j, ehd)][1] for j in pm.JAKSOT}
        L = sy.arvioi({k: S["loyto"][k] for k in mukana}, {k: SA for k in mukana}, max_viive=pm.VIIVE,
                      min_siirto=pm.MS, p_menetelma="nb", parit=parit)
        e = {(x["a"], x["b"], x["viive"]) for x in L["ehdokkaat"]}
        V = sy.arvioi({k: S["vahvistus"][k] for k in mukana}, {k: SA for k in mukana}, max_viive=pm.VIIVE,
                      min_siirto=pm.MS, p_menetelma="nb", rajaus=e) if e else {"ehdokkaat": []}
        L1[nimi] = {"sarjoja": len(mukana), "pareja": len(parit), "ehdokkaita": len(e), "sailyi": len(V["ehdokkaat"]),
                    "sailymisosuus": round(len(V["ehdokkaat"]) / len(e), 3) if e else None,
                    "tapahtumia_loyto": sum(len(sy.aktivaatiot(S["loyto"][k], SA)) for k in mukana)}
    # L1b: plasebo — sama määrä satunnaisia viikkoja poistettuna, samat 40 sarjaa ja parit
    pl = []
    for sd in range(5):
        S = {j: pm.sarjat_jaksolle(wob, brent, al, lo, True, plasebo=100 * sd + i)[1] for i, (j, (al, lo)) in enumerate(pm.JAKSOT.items())}
        L = sy.arvioi({k: S["loyto"][k] for k in mukana}, {k: SA for k in mukana}, max_viive=pm.VIIVE,
                      min_siirto=pm.MS, p_menetelma="nb", parit=parit)
        e = {(x["a"], x["b"], x["viive"]) for x in L["ehdokkaat"]}
        pl.append({"siemen": sd, "ehdokkaita": len(e), "tapahtumia_loyto": sum(len(sy.aktivaatiot(S["loyto"][k], SA)) for k in mukana)})
    L1["plasebo"] = pl
    out["L1_samat_sarjat"] = L1
    # L2: nolla = sarjat eri jaksoilta (A löytöjaksolta, B vahvistusjaksolta ja päinvastoin): todellinen tapahtumarakenne,
    # ei todellista keskinäistä ajoitusta. (Ensimmäinen yritys kierrätti jokaisen sarjan omalla satunnaisella siirrollaan;
    # se säilytti todellisen kytkennän niissä pareissa, joiden siirtojen ero osui välille 0–4, joten se ei ollut nolla.)
    S1 = sar[("loyto", False)][1]; S2 = sar[("vahvistus", False)][1]
    kaikki = [k for k in S1 if k in S2 and all(len(sy.aktivaatiot(x[k], SA)) >= pm.MIN_AKT for x in (S1, S2))]
    pp = [(a, b) for a in kaikki for b in kaikki if a != b and a.rsplit("_", 1)[1] == b.rsplit("_", 1)[1]]
    n = min(len(S1[kaikki[0]]), len(S2[kaikki[0]]))
    L2 = []
    for nimi, (X, Y) in {"A=2005-2015,B=2016-2026": (S1, S2), "A=2016-2026,B=2005-2015": (S2, S1)}.items():
        D = {k + "|A": X[k][:n] for k in kaikki}; D.update({k + "|B": Y[k][:n] for k in kaikki})
        R = sy.arvioi(D, {k: SA for k in D}, max_viive=pm.VIIVE, min_siirto=pm.MS, p_menetelma="nb",
                      parit=[(a + "|A", b + "|B") for a, b in pp])
        L2.append({"asetelma": nimi, "testeja": R["testeja"], "bh_ehdokkaita": len(R["ehdokkaat"]),
                   "osuus_p_le_005": R["osuus_p_le_005"], "osuus_p_le_001": R["osuus_p_le_001"]})
    out["L2_kalibrointi_nolla"] = L2
    Path("data/polttoaine/tulos-2-lisa.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
