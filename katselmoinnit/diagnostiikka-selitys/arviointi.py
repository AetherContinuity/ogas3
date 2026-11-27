"""Diagnostiikan mittarit M1–M3 README.md:n mukaan. Käyttö: python3 arviointi.py (hakemistossa tai polulla)."""
import importlib.util, json, re, sys
from pathlib import Path
H = Path(__file__).parent
_s = importlib.util.spec_from_file_location("vr", H.parents[1] / "tools" / "vaiterekisteri.py")
vr = importlib.util.module_from_spec(_s); _s.loader.exec_module(vr)
T = vr.normalisoi((H / "korpus/papers/dg-001-seudullinen-talvikunnossapito.html").read_text(encoding="utf-8"))
J = {"K": ("Yhteisen varakaluston arvo", "Tämä ei ole hankintaehdotus."),
     "P": ("Kunta arvioi katuverkkoa", "Yhteisen varakaluston arvo"),
     "C": ("Sama kahden vajeen rakenne", "Tietovaje:"),
     "V": ("Tietovaje:", "Ankarana talvena hälytysreittien")}
R = {k: (T.index(a), T.index(b, T.index(a) + 1)) for k, (a, b) in J.items()}

def pura(md):
    # ensimmäinen lohko on workflow'n metatieto; rekisteri on lohko, jossa on "esiintymat"
    lohkot = [json.loads(x) for x in re.findall(r"```json\s*\n(.*?)\n```", md, flags=re.S)]
    rek = [x for x in lohkot if isinstance(x, dict) and "esiintymat" in x]
    if len(rek) != 1:
        raise SystemExit(f"rekisterilohkoja {len(rek)}")
    return rek[0]

print("| ajo | esiintymiä | suhteita | M1 K | M2 K→P | M3 kontrolli | KONE | K:n suhteet |")
print("|---|---|---|---|---|---|---|---|")
for v in sorted(H.glob("dg-*-vastaus-*.md")):
    ajo = v.name.split("-vastaus")[0]
    rek = pura(v.read_text(encoding="utf-8"))
    (H / f"{ajo}-kimi.json").write_text(json.dumps(rek, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    m = {k: [] for k in J}
    for e in rek["esiintymat"]:
        pos = T.find(vr.normalisoi(e["lainaus"]))
        for k, (i, j) in R.items():
            if i <= pos < j:
                m[k].append(e["id"])
    g = lambda k: set().union(*[set(vr._ryhma(rek, x)) for x in m[k]]) if m[k] else set()
    G = {k: g(k) for k in J}
    s = [x for x in rek["suhteet"] if x.get("tila", "ehdotettu") != "hylatty"]
    m2 = [x for x in s if x["laji"] == "depends_on" and x["lahde"] in G["K"] and x["kohde"] in G["P"]]
    m3 = bool(m["C"]) and any((x["lahde"] in G["V"] and x["kohde"] in G["C"]) or (x["kohde"] in G["V"] and x["lahde"] in G["C"]) for x in s)
    ks = [f"{x['laji']} {x['lahde']}→{x['kohde']} [{x.get('perusta')}]" for x in s if x["lahde"] in G["K"] or x["kohde"] in G["K"]]
    t = vr.tarkista(rek, H / "korpus")
    print(f"| {ajo} | {len(rek['esiintymat'])} | {len(s)} | {bool(m['K'])} | {bool(m2)} {[x.get('perusta') for x in m2]} | {m3} | {len(t.kone)} | {'; '.join(ks) or '—'} |")
