import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import synapsi as sy  # noqa: E402


def test_aktivaatio_jaksot_ja_puuttuvat():
    x = [0, 5, 6, 0, None, 7, 0]
    assert sy.aktivaatiot(x, {"tyyppi": "kynnys", "ehto": ">", "raja": 4}) == [1, 5]
    assert sy.aktivaatiot([1, 1, 9, 9, 1], {"tyyppi": "muutos", "askel": 1, "raja": 5}) == [2, 4]


def test_poikkeama_ei_kayta_nykyista_arvoa():
    x = [10 + (i % 3) for i in range(40)] + [40] + [10 + (i % 3) for i in range(10)]
    assert sy.aktivaatiot(x, {"tyyppi": "poikkeama", "ikkuna": 24, "z": 5, "suunta": "ylos"}) == [40]


def test_yhteiset():
    assert sy.yhteiset([10, 50], [12, 53], 4) == [0, 0, 1, 1, 0]


def synteettinen(n=3000, siemen=7):
    r = random.Random(siemen)
    def kohina():
        return [r.gauss(0, 1) for _ in range(n)]
    A, B, C = kohina(), kohina(), kohina()
    D = [0.0]
    for _ in range(n - 1):
        D.append(D[-1] * 0.98 + r.gauss(0, 1))  # vahvasti autokorreloitunut, itsenäinen
    piikit = sorted(r.sample(range(50, n - 20), 25))
    for t in piikit:
        A[t] += 8
        B[t + 3] += 8  # istutettu A → B, viive 3
    for t in r.sample(range(50, n - 20), 25):
        C[t] += 8      # sama tapahtumatiheys, ei kytköstä
    return {"A": A, "B": B, "C": C, "D": D}


def test_istutettu_yhteys_loytyy_eika_vaaria():
    s = synteettinen()
    saanto = {"tyyppi": "kynnys", "ehto": ">", "raja": 5}
    saannot = {"A": saanto, "B": saanto, "C": saanto, "D": {"tyyppi": "muutos", "askel": 1, "raja": 3.2}}
    vajaa = sy.arvioi(s, saannot, max_viive=6, kierroksia=499, siemen=3)
    assert vajaa["kierrokset_riittavat"] is False and vajaa["ehdokkaat"] == []  # tyhjä tulos ei ole löydös
    t = sy.arvioi(s, saannot, max_viive=6, siemen=3)
    assert t["kierrokset_riittavat"]
    parit = {(e["a"], e["b"], e["viive"]) for e in t["ehdokkaat"]}
    assert ("A", "B", 3) in parit
    assert not any({a, b} != {"A", "B"} for a, b, _ in parit), parit
    assert all(e["tila"] == "ehdokas" for e in t["ehdokkaat"])


def test_negatiivikontrolli_ilman_rakennetta():
    s = synteettinen()
    r = random.Random(11)
    s["B"] = s["B"][1500:] + s["B"][:1500]  # rikotaan istutettu ajoitus
    saanto = {"tyyppi": "kynnys", "ehto": ">", "raja": 5}
    t = sy.arvioi({k: s[k] for k in "ABC"}, {k: saanto for k in "ABC"}, max_viive=6)
    assert t["kierrokset_riittavat"] and t["ehdokkaat"] == []


def test_histogrammi_vastaa_suoraa_laskentaa():
    r = random.Random(5); n = 500
    a = sorted(r.sample(range(n), 30)); b = sorted(r.sample(range(n), 30))
    h = sy._erot(a, b, n)
    for s in (0, 37, 250):
        bb = sy._kierra(b, n, s)
        assert sy.yhteiset(a, bb, 6) == [h[(d - s) % n] for d in range(7)]
