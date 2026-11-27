"""Synapsimoottori v0: ehdokassynapsit sarjojen ajallisesta yhteisesiintymästä. Ei semantiikkaa, ei LLM:ää.

Ketju: sarja → aktivaatiot (jaksot, ei yksittäiset vartit) → parin yhteisesiintymä viiveittäin →
nollamalli kiertosiirrolla (säilyttää sarjan oman autokorrelaation) → BH-korjaus pareittain ja
viiveittäin → ehdokkaat. Moottori ei koskaan aseta hyväksyntää; tila on aina "ehdokas", ja ihmisen
päätös kirjataan erikseen.

KÄYTTÖRAJA: moottoria ei ajeta talven 2026–2027 todelliseen aineistoon (data/sarjat/, data/wem-lopputulos/)
ennen kuin aktivaatiosäännöt, viive, kierrokset, tunnettujen kytkösten lista ja arviointimittarit on
ennakkokirjattu. Kehitys ja testit vain synteettisellä datalla.

Synapsi ei tarkoita kausaalisuutta. Se on havaittu assosiaatio, jolla on havaintohistoria.

AKTIVAATIOSÄÄNNÖT (parametrit lukitaan ennakkokirjauksessa ennen todellisen datan ajoa)
  {"tyyppi": "poikkeama", "ikkuna": N, "z": Z, "suunta": "ylos"|"alas"|"molemmat"}
      robusti z = (x − mediaani) / (1.4826·MAD) edeltävästä N vartista (ei nykyistä); |z| ≥ Z
  {"tyyppi": "kynnys", "ehto": "<"|">"|"<="|">=", "raja": R}
  {"tyyppi": "muutos", "askel": k, "raja": D}   |x_t − x_{t−k}| ≥ D
Peräkkäiset aktiiviset vartit yhdistetään jaksoksi; jakson alku on tapahtuma.

YHTEISESIINTYMÄ: A:n tapahtuma t ja B:n tapahtuma s, s − t = viive ∈ [0, max_viive] (suunnattu A → B).
Yksi A-tapahtuma lasketaan kerran per viive.

Käyttö (kirjasto): aktivaatiot(sarja, sääntö) · yhteiset(a, b, max_viive) · arvioi(sarjat, säännöt, ...)
Vain vakiokirjasto.
"""
from __future__ import annotations

import random
import statistics
from bisect import bisect_left


def aktivaatiot(x: list[float | None], saanto: dict) -> list[int]:
    """Palauttaa aktivaatiojaksojen alkuindeksit. None = puuttuva vartti (katkaisee jakson, ei aktivoidu)."""
    n = len(x)
    akt = [False] * n
    t = saanto["tyyppi"]
    for i in range(n):
        v = x[i]
        if v is None:
            continue
        if t == "kynnys":
            r = saanto["raja"]
            akt[i] = {"<": v < r, ">": v > r, "<=": v <= r, ">=": v >= r}[saanto["ehto"]]
        elif t == "muutos":
            j = i - saanto["askel"]
            akt[i] = j >= 0 and x[j] is not None and abs(v - x[j]) >= saanto["raja"]
        elif t == "poikkeama":
            w = [y for y in x[max(0, i - saanto["ikkuna"]):i] if y is not None]
            if len(w) < max(8, saanto["ikkuna"] // 2):
                continue
            med = statistics.median(w)
            mad = statistics.median([abs(y - med) for y in w]) * 1.4826
            if mad == 0:
                continue
            z = (v - med) / mad
            s = saanto.get("suunta", "molemmat")
            akt[i] = (z >= saanto["z"] if s == "ylos" else z <= -saanto["z"] if s == "alas" else abs(z) >= saanto["z"])
        else:
            raise ValueError(f"tuntematon sääntö {t}")
    return [i for i in range(n) if akt[i] and (i == 0 or not akt[i - 1])]


def yhteiset(a: list[int], b: list[int], max_viive: int) -> list[int]:
    """Lukumäärä viiveittäin 0..max_viive: montako A-tapahtumaa, joita seuraa B-tapahtuma täsmälleen viiveellä."""
    bs = set(b)
    return [sum(1 for t in a if t + d in bs) for d in range(max_viive + 1)]


def _kierra(b: list[int], n: int, siirto: int) -> list[int]:
    return sorted((t + siirto) % n for t in b)


def _erot(a: list[int], b: list[int], n: int) -> list[int]:
    """Histogrammi H[k] = #{(t, u): (u − t) mod n = k}. Kierrolla s viiveen d osumat = H[(d − s) mod n]."""
    h = [0] * n
    for t in a:
        for u in b:
            h[(u - t) % n] += 1
    return h


def _nb_hanta(havaittu: int, nulli: list[int]) -> float:
    """P(X ≥ havaittu), kun X ~ negatiivinen binomi, jonka keskiarvo ja varianssi sovitetaan kiertojakaumaan
    (varianssi ≤ keskiarvo → Poisson). Käytetään, kun kiertoja on liian vähän tarkkaan p:hen (lyhyet sarjat)."""
    import math
    K = len(nulli)
    mu = sum(nulli) / K
    var = sum((c - mu) ** 2 for c in nulli) / max(1, K - 1)
    if havaittu <= 0:
        return 1.0
    if mu <= 0:
        return 1.0 / (1 + K)  # nollamallissa ei yhtään osumaa: tarkan menetelmän alaraja
    if var <= mu * 1.0000001:
        pmf = [math.exp(-mu)]
        for k in range(1, havaittu):
            pmf.append(pmf[-1] * mu / k)
    else:
        r = mu * mu / (var - mu); q = r / (r + mu)
        pmf = [q ** r]
        for k in range(1, havaittu):
            pmf.append(pmf[-1] * (k - 1 + r) / k * (1 - q))
    return max(0.0, min(1.0, 1.0 - sum(pmf)))


def arvioi(sarjat: dict[str, list], saannot: dict[str, dict], max_viive: int = 8, kierroksia: int | None = None,
           min_siirto: int | None = None, alfa: float = 0.05, siemen: int = 1, p_menetelma: str = "tarkka",
           parit: list[tuple[str, str]] | None = None, askelia_paivassa: int | None = None,
           min_paivia: int | None = None, rajaus: set[tuple[str, str, int]] | None = None) -> dict:
    """Kaikki suunnatut parit A → B. Nollamalli: B:n tapahtumat kierretään siirrolla s, min_siirto ≤ s ≤ n − min_siirto
    (oletus 4·max_viive), A pysyy paikallaan. Oletuksena käydään läpi KAIKKI sallitut siirrot (tarkka, deterministinen
    permutaatiojakauma); kierroksia=K arpoo K siirtoa siemenellä. p = (1 + #{null ≥ havaittu}) / (1 + K).
    Testisuure per viive. BH-korjaus kaikkien parien ja viiveiden yli (tai annettujen `parit`-parien yli).
    p_menetelma="nb": p kiertojakaumaan sovitetusta negatiivisesta binomista (poikkeama 1, polttoainekoe 1:
    lyhyillä sarjoilla tarkan p:n resoluutio 1/(K+1) ei riitä BH:lle). Tarkka p raportoidaan aina rinnalla.
    Monipäiväisyys (SYNAPSI-1 poikkeama 1): jos askelia_paivassa on annettu, jokaiselle ehdokkaalle lasketaan,
    monelleko eri päivälle (indeksi // askelia_paivassa, sarjan alusta) sen yhteisesiintymät jakautuvat (A-tapahtuman
    päivä). Jos min_paivia on annettu, ehdokas, jonka päiviä on vähemmän, siirretään listaan
    "hylatyt_monipaivaisyys". Se ei ole ehdokas, mutta se raportoidaan.
    rajaus: jos annettu, testataan vain nämä (a, b, viive) -kolmikot ja BH tehdään niiden yli (vahvistusjakso:
    vain löytöjakson ehdokkaat).
    Huom: yksi A-tapahtuma voi osua viiveellä d useampaan B-tapahtumaan vain, jos B:llä on kaksi tapahtumaa samassa
    vartissa, mikä ei jaksotuksen jälkeen ole mahdollista; histogrammilaskenta on siksi sama kuin yhteiset()."""
    n = len(next(iter(sarjat.values())))
    if any(len(v) != n for v in sarjat.values()):
        raise ValueError("sarjojen pituudet eroavat")
    ms = min_siirto if min_siirto is not None else 4 * max_viive
    siirrot = list(range(ms, n - ms + 1))
    if kierroksia is not None and kierroksia < len(siirrot):
        siirrot = random.Random(siemen).sample(siirrot, kierroksia)
    K = len(siirrot)
    tap = {k: aktivaatiot(sarjat[k], saannot[k]) for k in sarjat}
    testit = []
    kaikki = [(a, b) for a in sarjat for b in sarjat if a != b]
    if rajaus is not None:
        parit = sorted({(a, b) for a, b, _ in rajaus})
    for a, b in (parit if parit is not None else kaikki):
        if True:
            if not tap[a] or not tap[b]:
                continue
            h = _erot(tap[a], tap[b], n)
            for d in range(max_viive + 1):
                if rajaus is not None and (a, b, d) not in rajaus:
                    continue
                hav = h[d]
                nulli = [h[(d - s) % n] for s in siirrot]
                p_tarkka = (1 + sum(1 for c in nulli if c >= hav)) / (1 + K)
                p = _nb_hanta(hav, nulli) if p_menetelma == "nb" else p_tarkka
                testit.append({"a": a, "b": b, "viive": d, "yhteisia": hav, "odotettu": round(sum(nulli) / K, 3),
                               "n_a": len(tap[a]), "n_b": len(tap[b]), "p": p if p_menetelma == "nb" else round(p, 6),
                               "p_tarkka": round(p_tarkka, 6)})
    kierroksia = K
    m = len(testit)
    # Kiertojen määrä rajaa pienimmän mahdollisen p:n (1/(K+1)). Jos se ei alita BH:n tiukinta rajaa
    # alfa/m, mikään testi ei voi läpäistä: tulos olisi tyhjä riippumatta datasta. Raportoidaan.
    voima_ok = m == 0 or p_menetelma == "nb" or 1 / (1 + kierroksia) <= alfa / m
    jarj = sorted(range(m), key=lambda i: testit[i]["p"])
    raja = 0
    for r, i in enumerate(jarj, 1):
        if testit[i]["p"] <= alfa * r / m:
            raja = r
    hyv = set(jarj[:raja])
    ehdokkaat = [dict(testit[i], tila="ehdokas") for i in sorted(hyv, key=lambda i: testit[i]["p"]) if testit[i]["yhteisia"] > 0]
    hylatyt = []
    if askelia_paivassa:
        for e in ehdokkaat:
            bs = set(tap[e["b"]])
            e["paivia"] = len({t // askelia_paivassa for t in tap[e["a"]] if t + e["viive"] in bs})
        if min_paivia:
            hylatyt = [dict(e, tila="hylatty_monipaivaisyys") for e in ehdokkaat if e["paivia"] < min_paivia]
            ehdokkaat = [e for e in ehdokkaat if e["paivia"] >= min_paivia]
    return {"n_varttia": n, "tapahtumia": {k: len(v) for k, v in tap.items()}, "testeja": m, "alfa_bh": alfa,
            "kierroksia": kierroksia, "siemen": siemen, "kierrokset_riittavat": voima_ok,
            "kierroksia_vahintaan": int(m / alfa) + 1, "p_menetelma": p_menetelma, "min_paivia": min_paivia, "ehdokkaat": ehdokkaat,
            "hylatyt_monipaivaisyys": hylatyt}
