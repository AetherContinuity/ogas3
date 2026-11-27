import copy, importlib.util, json, pathlib
spec = importlib.util.spec_from_file_location("vr", pathlib.Path(__file__).parents[1] / "tools" / "vaiterekisteri.py")
vr = importlib.util.module_from_spec(spec); spec.loader.exec_module(vr)
FIX = pathlib.Path(__file__).parent / "fixtures" / "vaiterekisteri" / "synteettinen.json"

def rek():
    return json.loads(FIX.read_text(encoding="utf-8"))

def virheet(r, korpus=None):
    return vr.tarkista(r, korpus).kone

# --- validointi: kelvollinen aineisto ---------------------------------------
def test_kelvollinen_lapaisee_kone_ehdot():
    t = vr.tarkista(rek())
    assert t.ok, t.kone
    assert any("lainausta ei tarkistettu" in x for x in t.avoin)      # ilman korpusta = avoin
    assert any("s2:" in x and "tarkistamatta" in x for x in t.avoin)  # ei tarkistajaa = avoin
    assert not any(x.startswith("s1:") and "tarkistamatta" in x for x in t.avoin)
    assert any("P1-b" in x for x in t.avoin)
    assert any(x.startswith("s2:") for x in t.ihminen)                # semanttinen arvio ihmiselle
    assert not any(x.startswith("s1:") for x in t.ihminen)            # tarkistettu ei enää arvioitava
    assert not any(x.startswith("s7:") for x in t.avoin + t.ihminen)  # hylätty on päätös, ei avoin
    assert any("P1-c: [A]-väite ilman countertestiä" in x for x in t.ihminen)

# --- validointi: virheelliset tapaukset -------------------------------------
def test_puuttuva_kentta_ja_vaara_laji():
    r = rek(); del r["esiintymat"][0]["lainaus"]; r["suhteet"][0]["laji"] = "supports"
    v = virheet(r)
    assert any("'lainaus'" in x for x in v) and any("supports" in x for x in v)

def test_tuntematon_viite_ja_itseensa():
    r = rek(); r["suhteet"][1]["kohde"] = "EI-OLE"; r["suhteet"][2]["kohde"] = "P2-a"
    v = virheet(r)
    assert any("EI-OLE" in x for x in v) and any("itseensä" in x for x in v)

def test_kaksoisid_ja_kaksoissuhde_suuntaamaton():
    r = rek(); r["esiintymat"][1]["id"] = "P1-a"
    r["suhteet"].append({"id": "s8", "lahde": "P1-a", "kohde": "P2-a", "laji": "same_claim", "perustelu": "x", "kirjaaja": "t"})
    v = virheet(r)
    assert any("toistuu" in x and "P1-a" in x for x in v)
    assert any("sama suhde toistuu" in x for x in v)

def test_related_ja_depends_on_ristiriita():
    r = rek(); r["suhteet"].append({"id": "s8", "lahde": "P2-c", "kohde": "P1-a", "laji": "depends_on", "perustelu": "x", "kirjaaja": "t"})
    assert any("'related' ja" in x for x in virheet(r))

def test_same_claim_ja_depends_on_ristiriita():
    r = rek(); r["suhteet"].append({"id": "s8", "lahde": "P2-a", "kohde": "P1-a", "laji": "depends_on", "perustelu": "x", "kirjaaja": "t"})
    assert any("same_claim" in x and "depends_on" in x for x in virheet(r))

def test_hylatty_ei_aiheuta_ristiriitaa():
    r = rek()  # s7 hylatty depends_on P2-c -> P1-c; ei ristiriitaa eikä sykliä
    assert vr.tarkista(r).ok

def test_sykli():
    r = rek(); r["suhteet"].append({"id": "s8", "lahde": "P1-b", "kohde": "P1-c", "laji": "depends_on", "perustelu": "x", "kirjaaja": "t"})
    assert any("sykli" in x for x in virheet(r))

def test_tarkistettu_vaatii_eri_tarkistajan():
    r = rek(); r["suhteet"][1]["tila"] = "tarkistettu"
    assert any("vaatii tarkistajan" in x for x in virheet(r))
    r["suhteet"][1]["tarkistaja"] = "testi"
    assert any("sama kuin kirjaaja" in x for x in virheet(r))

def test_countertest_saannot():
    r = rek(); ct = r["esiintymat"][6]["countertest"]; ct["note"] = ""
    assert any("note vaaditaan" in x for x in virheet(r))
    r = rek(); r["esiintymat"][0]["countertest"]["note"] = "x"
    assert any("note sallitaan vain" in x for x in virheet(r))
    r = rek(); r["esiintymat"][0]["countertest"]["status"] = "confirmed"
    assert any("countertest.status" in x for x in virheet(r))
    r = rek(); r["esiintymat"][0]["countertest"]["condition"] = ""
    assert any("condition vaaditaan" in x for x in virheet(r))

def test_vaara_merkinta():
    r = rek(); r["esiintymat"][0]["merkinta"] = "X"
    assert any("merkinta" in x for x in virheet(r))

# --- lainauksen sanatarkkuus korpusta vasten --------------------------------
def test_lainaus_korpusta_vasten(tmp_path):
    (tmp_path / "p1.html").write_text("<p>Siltaa ei rakenneta, koska <em>kukaan</em> ei omista&nbsp;sitä.</p>"
                                      "<p>Lautta lopetettiin   2010.</p><p>Nimetään sillalle omistaja.</p>", encoding="utf-8")
    (tmp_path / "p2.html").write_text("<p>Pullonkaula on omistajuus.</p>", encoding="utf-8")
    t = vr.tarkista(rek(), tmp_path)
    assert t.ok, t.kone
    r = rek(); r["esiintymat"][1]["lainaus"] = "Lautta lopetettiin 2011."
    assert any("ei löydy sanatarkasti" in x for x in virheet(r, tmp_path))
    r = rek(); r["esiintymat"][3]["tiedosto"] = "puuttuu.html"
    assert any("tiedostoa ei löydy" in x for x in virheet(r, tmp_path))

# --- kyselyt ------------------------------------------------------------------
def test_ryhmat_sailyttavat_esiintymat():
    g = vr.ryhmat(rek())
    assert ["P1-a", "P2-a"] in g and ["P1-b", "P2-b"] in g
    assert len(rek()["esiintymat"]) == 7  # ei yhdistetty olioksi

def test_alavirta_nayttaa_valivaiheen():
    rivit = dict(vr.alavirta(rek(), "P2-b"))
    # P2-b = P1-b; P1-a nojaa P1-b:hen; P2-a = P1-a; P1-c nojaa P1-a:han
    assert rivit["P1-a"] == "P2-b = P1-b ← P1-a"
    assert rivit["P1-c"] == "P2-b = P1-b ← P1-a ← P1-c"
    assert "P2-a" in rivit and " = P2-a" in rivit["P2-a"]

def test_related_ei_koskaan_virrassa():
    for eid in ("P1-a", "P2-a", "P1-b"):
        assert "P2-c" not in dict(vr.alavirta(rek(), eid))
        assert "P2-c" not in dict(vr.ylavirta(rek(), eid))
    assert [m for m, _ in vr.liittyvat(rek(), "P1-a")] == ["P2-c"]

def test_hylatty_suhde_ei_virrassa():
    assert "P2-c" not in dict(vr.ylavirta(rek(), "P2-c")) and vr.ylavirta(rek(), "P2-c") == []

def test_ylavirta():
    rivit = dict(vr.ylavirta(rek(), "P1-c"))
    assert rivit["P1-a"] == "P1-c → P1-a" and rivit["P1-b"] == "P1-c → P1-a → P1-b"

def test_rajaukset_ryhman_kautta():
    r = vr.rajaukset(rek(), "P1-a")
    assert len(r) == 1 and r[0][0] == "P3-a" and "via P1-a = P2-a" in r[0][1]
    assert vr.rajaukset(rek(), "P1-b") == []

def test_cli_tarkista(capsys):
    assert vr.main(["tarkista", str(FIX)]) == 0
    out = capsys.readouterr().out
    assert "KONE (0)" in out and "ei kerro sisällön oikeellisuudesta" in out

# --- kovennus: täyttäjän rakenteelliset virheet eivät kaada validointia -------
VAARAT_ARVOT = [None, 0, 1.5, True, [], ["x"], {}, {"a": 1}]

def test_vaarat_tyypit_raportoidaan_eivat_kaada():
    pohja = rek()
    for ryhma, i in (("esiintymat", 0), ("esiintymat", 6), ("suhteet", 0), ("suhteet", 1)):
        for k in list(pohja[ryhma][i].keys()) + ["tarkistaja", "tila", "tiedosto"]:
            for arvo in VAARAT_ARVOT:
                r = copy.deepcopy(pohja); r[ryhma][i][k] = arvo
                vr.tarkista(r)  # ei poikkeusta
    for k in ("condition", "evidence_required", "status", "note"):
        for arvo in VAARAT_ARVOT:
            r = copy.deepcopy(pohja); r["esiintymat"][6]["countertest"][k] = arvo
            vr.tarkista(r)
    for juuri in (None, [], "x", {"esiintymat": "x", "suhteet": []}, {"esiintymat": [1, "x"], "suhteet": [None]}):
        assert not vr.tarkista(juuri).ok

def test_numero_kentassa_on_kone_virhe():
    r = rek(); r["suhteet"][0]["tarkistaja"] = 5
    assert any("'tarkistaja' ei ole merkkijono" in x for x in virheet(r))
    r = rek(); r["esiintymat"][6]["countertest"]["note"] = 42
    assert any("'note' ei ole merkkijono" in x for x in virheet(r))
    r = rek(); r["esiintymat"][0]["tiedosto"] = 7
    assert any("'tiedosto' ei ole merkkijono" in x for x in virheet(r))
    r = rek(); r["suhteet"][1]["lahde"] = ["P1-a"]
    assert any("'lahde'" in x for x in virheet(r))

def test_tiedostopolku_ei_saa_poistua_korpuksesta(tmp_path):
    korpus = tmp_path / "korpus"; korpus.mkdir()
    (tmp_path / "salainen.html").write_text("Siltaa ei rakenneta, koska kukaan ei omista sitä.", encoding="utf-8")
    for polku in ("../salainen.html", str(tmp_path / "salainen.html"), "a/../../salainen.html"):
        r = rek(); r["esiintymat"][0]["tiedosto"] = polku
        assert any("korpuksen ulkopuolelle" in x for x in virheet(r, korpus)), polku

def test_kyselykomennot_validoivat_ensin(tmp_path, capsys):
    r = rek(); r["suhteet"][2]["lahde"] = ["P2-a"]   # virheellinen same_claim-rivi
    f = tmp_path / "rikki.json"; f.write_text(json.dumps(r), encoding="utf-8")
    for komento in (["ryhmat", str(f)], ["alavirta", str(f), "P1-a"], ["ylavirta", str(f), "P1-c"],
                    ["rajaukset", str(f), "P1-a"], ["liittyvat", str(f), "P1-a"]):
        assert vr.main(komento) == 1, komento   # ei poikkeusta, hallittu virhe
    assert "kone-ehtoja" in capsys.readouterr().err
