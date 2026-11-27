import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import datavahti as vahti  # noqa: E402

J = Path(__file__).resolve().parents[1]
SARJAT = json.loads((J / "data/datavahti/sarjat.json").read_text(encoding="utf-8"))
NYT = datetime(2026, 12, 2, 12, 0, tzinfo=timezone.utc)
S = {"id": "X", "ds": 124, "resoluutio_min": 15, "max_viive_h": 3, "min": 3000, "max": 16000, "vaihtelee": True}


def rivit(n=24, loppu=NYT, askel=15, arvo=lambda i: 8000 + i):
    return [{"startTime": (loppu - timedelta(minutes=askel * (n - i))).strftime("%Y-%m-%dT%H:%M:%S.000Z"), "value": arvo(i)} for i in range(n)]


def test_ok():
    assert vahti.tarkista_sarja(S, rivit(), NYT) == ("OK", [])


def test_vanhentunut_aukko_resoluutio():
    assert vahti.tarkista_sarja(S, rivit(loppu=NYT - timedelta(hours=5)), NYT)[0] == "VANHENTUNUT"
    r = rivit(); del r[10]
    assert vahti.tarkista_sarja(S, r, NYT)[0] == "AUKKO"
    assert vahti.tarkista_sarja(S, rivit(askel=60), NYT)[0] == "AUKKO"
    assert vahti.tarkista_sarja(S, [], NYT)[0] == "AUKKO"


def test_epauskottava():
    assert vahti.tarkista_sarja(S, rivit(arvo=lambda i: 0), NYT)[0] == "EPÄUSKOTTAVA"  # DS 105 -tyyppinen nollasarja
    assert vahti.tarkista_sarja(S, rivit(arvo=lambda i: 8000), NYT)[0] == "EPÄUSKOTTAVA"  # vakio, vaikka pitäisi vaihdella
    assert vahti.tarkista_sarja(S, rivit(arvo=lambda i: 99999 if i == 3 else 8000 + i), NYT)[0] == "EPÄUSKOTTAVA"
    ydin = dict(S, min=0, max=4600, vaihtelee=False)
    assert vahti.tarkista_sarja(ydin, rivit(arvo=lambda i: 4390), NYT)[0] == "OK"  # ydinvoima saa olla tasainen
    r = rivit(); r.append(dict(r[-1]))
    assert vahti.tarkista_sarja(S, r, NYT)[0] == "EPÄUSKOTTAVA"


def test_rajapinta():
    rt = SARJAT["rajapintatesti"]
    a = vahti._aika(rt["alku"])
    hyva = [{"startTime": (a + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%S.000Z")} for i in range(8)]
    assert vahti.tarkista_rajapinta(rt, hyva)[0] == "OK"
    assert vahti.tarkista_rajapinta(rt, hyva[:1])[0] == "RAJAPINTA"  # size ohitettu → 1 piste
    assert vahti.tarkista_rajapinta(rt, rivit(n=8))[0] == "RAJAPINTA"  # live-data ikkunan sijaan


def test_lukitut_tiedostot_ja_toisto():
    for t in SARJAT["tiedostot"]:
        assert vahti.tarkista_tiedosto(t, J) == ("OK", []), t["id"]
    muutettu = dict(SARJAT["tiedostot"][0], sha256_16="0" * 16)
    assert vahti.tarkista_tiedosto(muutettu, J)[0] == "EPÄUSKOTTAVA"


def test_keruu_ja_muutokset(tmp_path):
    k = {"id": "K", "polku": "k.json", "kentta": "haettu", "max_ika_vrk": 35, "kaudella_kk": [12]}
    assert vahti.tarkista_keruu(k, tmp_path, NYT)[0] == "VANHENTUNUT"
    (tmp_path / "k.json").write_text(json.dumps({"haettu": "2026-11-30T05:00:00+00:00"}))
    assert vahti.tarkista_keruu(k, tmp_path, NYT)[0] == "OK"
    assert vahti.tarkista_keruu(dict(k, kaudella_kk=[6]), tmp_path, NYT) == ("OK", ["ei kaudella"])
    vanha = {"tilat": {"A": {"tila": "OK"}, "B": {"tila": "AUKKO"}}}
    uusi = {"tilat": {"A": {"tila": "VANHENTUNUT", "syyt": ["x"]}, "B": {"tila": "AUKKO", "syyt": []}, "C": {"tila": "OK", "syyt": []}}}
    assert vahti.muutokset(vanha, uusi) == ["MUUTOS A: OK → VANHENTUNUT (x)"]


def test_aja_hakuvirhe_ei_ole_ok(tmp_path):
    def rikki(*a):
        raise RuntimeError("Fingrid returned 429")
    t = vahti.aja(SARJAT, J, NYT, hakija=rikki, tauko=0)
    assert all(t["tilat"][s["id"]]["tila"] == "EI_TARKISTETTAVISSA" for s in SARJAT["fingrid"])
    assert t["tilat"]["FG-RAJAPINTA"]["tila"] == "EI_TARKISTETTAVISSA"
