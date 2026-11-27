import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import wem_lopputulos as wl  # noqa: E402

J = Path(__file__).resolve().parents[1]
SPEC = json.loads((J / "data/wem-lopputulos/rekisterointi.json").read_text(encoding="utf-8"))
LOPPU = datetime(2027, 4, 2, tzinfo=timezone.utc)


def test_vertailutaso_toistuu():
    """Lukittu vertailutaso (talvi 2025–2026) samalla koodilla: arvot täsmäävät rekisteröintiin."""
    base = json.loads((J / "tests/fixtures/wem/rp-margin-talvi-2025-2026.json").read_text(encoding="utf-8"))
    spec = json.loads(json.dumps(SPEC))
    spec["ikkuna"].update(alku="2025-10-01T00:00:00Z", loppu="2026-04-01T00:00:00Z")
    t = wl.laske(spec, base["data"])
    assert t["muuttujat"] == SPEC["vertailutaso"]["arvot"]
    assert t["kelpaavat"]["margin"] == SPEC["vertailutaso"]["kelpaavia_vartteja"]
    assert t["puuttuvat"]["margin"]["lkm"] == 2


def test_tilat(tmp_path):
    p = tmp_path / "a.json"
    assert wl.arvioi(SPEC, p, LOPPU)["tila"] == "HAVAINTO_PUUTTUU"
    d = {"haettu": "2027-04-02T06:00:00+00:00", "raaka_sha256": "x",
         "data": {"2026-10-01T00:00:00.000Z": {"offered_up": 100, "activated": 90, "price": 600},
                  "2026-10-01T00:15:00.000Z": {"offered_up": 100, "activated": 110, "price": 10}}}
    p.write_text(json.dumps(d)); t = wl.arvioi(SPEC, p, LOPPU)
    assert t["tila"] == "MITATTU"
    assert t["tulos"]["muuttujat"] == {"margin_alle_20": 2, "margin_alle_5": 1, "margin_negatiivinen": 1, "hinta_vahintaan_500": 1}
    assert t["tulos"]["puuttuvat"]["margin"]["lkm"] == 17470  # puuttuva ei ole nolla
    d["haettu"] = "2027-03-03T06:00:00+00:00"; p.write_text(json.dumps(d))
    t = wl.arvioi(SPEC, p, datetime(2027, 3, 3, tzinfo=timezone.utc))
    assert t["tila"] == "HAVAINTO_PUUTTUU" and "valihavainto" in t
    d["haettu"] = "2027-04-02T06:00:00+00:00"
    for v in d["data"].values():
        v.pop("price")
    p.write_text(json.dumps(d)); assert wl.arvioi(SPEC, p, LOPPU)["tila"] == "HAVAINTO_PUUTTUU"
