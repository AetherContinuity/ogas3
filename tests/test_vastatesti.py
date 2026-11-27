import copy
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import vastatesti as vt  # noqa: E402

JUURI = Path(__file__).resolve().parents[1]
SPEC = json.loads((JUURI / "data/vastatestit/t1.json").read_text(encoding="utf-8"))
LOPPU = date(2027, 6, 30)


def aineisto(rivit, haettu="2027-06-03T05:30:00+00:00", **muu):
    d = {"lahde": "x", "raaka_sha256": "0" * 64, "activeFrom": "2026-10-01", "haettu": haettu, "rivit": rivit}
    d.update(muu)
    return d


def r(kk, n, med, p90, alue="Suomenlahti"):
    return {"merialue": alue, "kuukausi": kk, "odotuksia": n, "mediaani_h": med, "p90_h": p90}


def aja(tmp_path, d, luokitus="keskimääräinen", pvm=LOPPU, spec=SPEC):
    (tmp_path / "data/talvimeri").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/vastatestit").mkdir(parents=True, exist_ok=True)
    if d is not None:
        (tmp_path / "data/talvimeri/2026-2027.json").write_text(json.dumps(d), encoding="utf-8")
    u = tmp_path / "data/vastatestit/t1-ulkoiset.json"
    if luokitus is None:
        u.unlink(missing_ok=True)
    else:
        (tmp_path / "data/vastatestit/t1-ulkoiset.json").write_text(json.dumps({"jaatalvi_luokitus": luokitus}), encoding="utf-8")
    return vt.arvioi(spec, tmp_path, pvm)


def test_vahvistuu_mediaani_ja_p90(tmp_path):
    assert aja(tmp_path, aineisto([r("2027-02", 40, 2.6, 5.0)]))["tila"] == "VAHVISTUU"
    assert aja(tmp_path, aineisto([r("2027-02", 40, 1.0, 12.5)]))["tila"] == "VAHVISTUU"


def test_raja_on_aito_ylitys(tmp_path):
    assert aja(tmp_path, aineisto([r("2027-02", 40, 2.5, 12)]))["tila"] == "KUMOUTUU"


def test_alle_30_ei_kelpaa(tmp_path):
    t = aja(tmp_path, aineisto([r("2027-02", 29, 9.0, 30.0), r("2027-02", 200, 9.0, 30.0, alue="Perämeri")]))
    assert t["tila"] == "RATKEAMATON" and t["kelpaavat_kuukaudet"] == []


def test_ankara_ohittaa_ylityksen(tmp_path):
    t = aja(tmp_path, aineisto([r("2027-02", 40, 5.0, 20.0)]), luokitus="ankara")
    assert t["tila"] == "RATKEAMATON" and t["ylitykset"]


def test_havainto_puuttuu_ei_koskaan_vahvista(tmp_path):
    assert aja(tmp_path, None)["tila"] == "HAVAINTO_PUUTTUU"
    assert aja(tmp_path, aineisto([r("2027-02", 40, 5.0, 20.0)]), luokitus=None)["tila"] == "HAVAINTO_PUUTTUU"
    assert aja(tmp_path, aineisto([r("2027-02", 40, 5.0, 20.0)]), luokitus="kova")["tila"] == "HAVAINTO_PUUTTUU"
    vanha = aineisto([r("2027-02", 40, 5.0, 20.0)], haettu="2027-05-03T05:30:00+00:00")
    assert aja(tmp_path, vanha)["tila"] == "HAVAINTO_PUUTTUU"
    assert aja(tmp_path, aineisto([r("2027-02", 40, 5.0, 20.0)], activeFrom="2025-10-01"))["tila"] == "HAVAINTO_PUUTTUU"
    assert aja(tmp_path, aineisto([r("2027-02", 40, None, 20.0)]))["tila"] == "HAVAINTO_PUUTTUU"
    (tmp_path / "data/talvimeri/2026-2027.json").write_text("{rikki", encoding="utf-8")
    assert vt.arvioi(SPEC, tmp_path, LOPPU)["tila"] == "HAVAINTO_PUUTTUU"


def test_avoin_ennen_tarkistuspaivaa(tmp_path):
    t = aja(tmp_path, aineisto([r("2027-02", 40, 5.0, 20.0)], haettu="2027-03-03T05:30:00+00:00"), pvm=date(2027, 3, 3))
    assert t["tila"] == "AVOIN" and t["ylitykset"]


def test_negatiivikontrolli_vertailutaso(tmp_path):
    """Talven 2025–2026 koosteet T1:n säännöllä (kuukaudet siirretty vuodella): Suomenlahden ainoa
    kelpaava kuukausi (helmikuu, 43 odotusta, mediaani 1,25 h, p90 8,13 h) ei ylitä rajoja."""
    d = json.loads((JUURI / "data/talvimeri/2025-2026.json").read_text(encoding="utf-8"))
    siirretty = copy.deepcopy(d)
    for x in siirretty["rivit"]:
        y, m = x["kuukausi"].split("-")
        x["kuukausi"] = f"{int(y) + 1}-{m}"
    siirretty["activeFrom"] = "2026-10-01"; siirretty["haettu"] = "2027-06-03T05:30:00+00:00"
    t = aja(tmp_path, siirretty)
    assert t["tila"] == "KUMOUTUU" and t["kelpaavat_kuukaudet"] == ["2027-02"]
