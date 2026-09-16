"""OGAS3 — yksikkötestit neljälle turvalukolle.

Aja: python3 -m pytest tests -q     (tai)     python3 tests/test_all.py
"""

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aggregator import aggregate, month_key, months_in_range, visibility_lag
from audit import explain_month, format_explain
from rri import (RRIError, compute_l, compute_rri_raw, monthly_l_ir_from_events,
                 scale_rri)
from scaler import ScalingError, scale_full, scale_pre
from schema import SchemaError
from validator import load_events, validate_event, validate_events

ROOT = Path(__file__).resolve().parents[1]


def base_event(**over):
    e = {
        "event_id": "E001",
        "occurred_at": "2026-03-05T09:00:00+03:00",
        "known_at": "2026-03-06T09:00:00+03:00",
        "retrieved_at": "2026-09-04T09:00:00+03:00",
        "source": "Hankeikkuna",
        "source_url": "https://api.hankeikkuna.fi/api/v2/kohteet/haku",
        "type": "D",
        "subtype": None,
        "parameters": {},
        "llm_classification": {"intensity": None, "targeting": 0.7,
                               "policy_proximity": 0.4, "uptake": 0.0},
        "irreversibility": 0.5,
        "impact_weight": 0.8,
        "evidence": [{"quote": "q", "location": "§ 1",
                      "source_url": "https://x", "retrieved_at": "2026-09-04T09:00:00+03:00"}],
    }
    e.update(over)
    return e


# ── Turvalukko 1: puuttuva kenttä ei muutu nollaksi ──────────────────
def test_missing_field_raises():
    for k in ("event_id", "occurred_at", "known_at", "retrieved_at", "type", "source"):
        d = base_event()
        del d[k]
        try:
            validate_event(d)
        except SchemaError as e:
            assert k in str(e), f"virheviesti ei nimeä kenttää {k}: {e}"
        else:
            raise AssertionError(f"{k} puuttui mutta validointi meni läpi")


def test_missing_classification_key_raises_not_zero():
    d = base_event()
    del d["llm_classification"]["uptake"]
    try:
        validate_event(d)
    except SchemaError as e:
        assert "uptake" in str(e) and "nolla" in str(e)
    else:
        raise AssertionError("puuttuva uptake ei nostanut virhettä")


def test_explicit_null_is_allowed_and_distinct_from_zero():
    # intensity on ROE v0.3:ssa vain L-tapahtumalla, joten testi käyttää L:ää
    a = validate_event(base_event(type="L", impact_weight=None))     # intensity None
    b = validate_event(base_event(type="L", impact_weight=None, llm_classification={
        "intensity": 0.0, "targeting": 0.7, "policy_proximity": 0.4, "uptake": 0.0}))
    assert a.llm_classification["intensity"] is None
    assert b.llm_classification["intensity"] == 0.0
    assert a.llm_classification["intensity"] != b.llm_classification["intensity"]


def test_out_of_range_raises():
    for bad in (-0.1, 1.4):
        try:
            validate_event(base_event(irreversibility=bad))
        except SchemaError:
            pass
        else:
            raise AssertionError(f"{bad} hyväksyttiin välillä 0–1")


def test_naive_timestamp_rejected():
    try:
        validate_event(base_event(occurred_at="2026-03-05T09:00:00"))
    except SchemaError as e:
        assert "aikavyöhyke" in str(e)
    else:
        raise AssertionError("naiivi aikaleima hyväksyttiin")


def test_causal_order_enforced():
    try:
        validate_event(base_event(known_at="2026-03-01T09:00:00+03:00"))
    except SchemaError as e:
        assert "known_at" in str(e)
    else:
        raise AssertionError("known_at ennen occurred_at hyväksyttiin")


def test_evidence_required():
    try:
        validate_event(base_event(evidence=[]))
    except SchemaError as e:
        assert "evidence" in str(e)
    else:
        raise AssertionError("tapahtuma ilman todistetta hyväksyttiin")


def test_duplicate_ids_rejected():
    try:
        validate_events([base_event(), base_event()])
    except SchemaError as e:
        assert "duplikaatti" in str(e)
    else:
        raise AssertionError("duplikaattitunnus hyväksyttiin")


# ── Turvalukko 2: no look-ahead ──────────────────────────────────────
def test_pre_uses_known_at_full_uses_occurred_at():
    e = validate_event(base_event(
        occurred_at="2026-03-05T09:00:00+03:00",
        known_at="2026-07-01T09:00:00+03:00"))
    pre = aggregate([e], "PRE", months_in_range("2026-03", "2026-07"))
    full = aggregate([e], "FULL", months_in_range("2026-03", "2026-07"))
    assert pre["2026-03"].counts["D"] == 0, "PRE näki tapahtuman ennen kuin se oli tiedossa"
    assert pre["2026-07"].counts["D"] == 1
    assert full["2026-03"].counts["D"] == 1
    assert full["2026-07"].counts["D"] == 0


def test_expanding_scaling_ignores_future_months():
    evs = validate_events([
        base_event(event_id="A", occurred_at="2026-01-05T09:00:00+03:00",
                   known_at="2026-01-05T09:00:00+03:00", impact_weight=0.2),
        base_event(event_id="B", occurred_at="2026-02-05T09:00:00+03:00",
                   known_at="2026-02-05T09:00:00+03:00", impact_weight=1.0),
    ])
    months = months_in_range("2026-01", "2026-02")
    sc = scale_pre(aggregate(evs, "PRE", months), "expanding")
    # tammikuussa nähdään vain tammikuu -> rajat 0.2..0.2 -> degeneroitunut -> 0
    assert sc["2026-01"].bounds["D"] == (0.2, 0.2)
    assert sc["2026-01"].scaled["D"] == 0.0
    assert sc["2026-01"].n_months_in_basis == 1
    # helmikuussa rajat laajenevat
    assert sc["2026-02"].bounds["D"] == (0.2, 1.0)
    assert sc["2026-02"].scaled["D"] == 100.0


def test_full_window_scaling_refused_for_pre():
    evs = validate_events([base_event()])
    try:
        scale_full(aggregate(evs, "PRE", ["2026-03"]))
    except ScalingError as e:
        assert "look-ahead" in str(e)
    else:
        raise AssertionError("koko ikkunan skaalaus sallittiin PRE-tilassa")


def test_baseline_requires_explicit_bounds():
    evs = validate_events([base_event()])
    try:
        scale_pre(aggregate(evs, "PRE", ["2026-03"]), "baseline")
    except ScalingError as e:
        assert "baseline" in str(e)
    else:
        raise AssertionError("baseline-tila hyväksyi puuttuvat rajat")


# ── Turvalukko 3: FULL ei ole ennuste, mutta se on eri sarja ─────────
def test_pre_and_full_differ_on_real_data():
    evs = load_events(ROOT / "synthetic_events.json")
    months = months_in_range("2026-01", "2026-12")
    pre = aggregate(evs, "PRE", months)
    full = aggregate(evs, "FULL", months)
    diffs = [m for m in months if pre[m].counts != full[m].counts]
    assert diffs, "PRE ja FULL identtiset — aikaleimasemantiikka ei vaikuta mihinkään"
    assert sum(sum(pre[m].counts.values()) for m in months) == \
           sum(sum(full[m].counts.values()) for m in months), "tapahtumia katosi"


# ── SP = D + O + S on ainoa lukittu kaava ────────────────────────────
def test_sp_is_sum_of_three():
    evs = load_events(ROOT / "synthetic_events.json")
    months = months_in_range("2026-01", "2026-12")
    sc = scale_full(aggregate(evs, "FULL", months))
    for m in months:
        s = sc[m]
        assert abs(s.structural_pressure - sum(s.scaled[t] for t in ("D", "O", "S"))) < 1e-9


def test_missing_weight_not_counted_as_zero():
    evs = validate_events([
        base_event(event_id="W1", impact_weight=0.5),
        base_event(event_id="W2", impact_weight=None),
    ])
    b = aggregate(evs, "FULL", ["2026-03"])["2026-03"]
    assert b.counts["D"] == 2, "tapahtuma katosi"
    assert abs(b.raw["D"] - 0.5) < 1e-9, "puuttuva paino laskettiin mukaan"
    assert b.unweighted["D"] == ("W2",), "puuttuvaa painoa ei kirjattu"


# ── Turvalukko 4: audit trail + tarkoituksellinen aukko ──────────────
# ── GATE 2-4: RRI:n laskenta (lukittu 5.9.2026) ─────────────────────
def test_compute_l_is_product_of_four():
    c = {"intensity": 0.5, "targeting": 0.8, "policy_proximity": 0.5, "uptake": 0.4}
    assert abs(compute_l(c) - 0.5*0.8*0.5*0.4) < 1e-9


def test_compute_l_none_when_component_missing():
    c = {"intensity": None, "targeting": 0.8, "policy_proximity": 0.5, "uptake": 0.4}
    assert compute_l(c) is None, "puuttuva komponentti tuotti luvun — None ei ole nolla"


def test_compute_l_rejects_out_of_range():
    for bad in (-0.1, 1.5):
        try:
            compute_l({"intensity": bad, "targeting": .5, "policy_proximity": .5, "uptake": .5})
        except RRIError:
            pass
        else:
            raise AssertionError(f"{bad} hyväksyttiin")


def test_l_and_ir_aggregate_as_max_not_mean():
    """Lukkiutuminen ei keskiarvoistu — yksi vahva ei laimennu heikoista."""
    strong = validate_event(base_event(event_id="L1", type="L", impact_weight=None, llm_classification={
        "intensity": 1.0, "targeting": 1.0, "policy_proximity": 1.0, "uptake": 1.0}))
    weak = validate_event(base_event(event_id="L2", type="L", impact_weight=None, llm_classification={
        "intensity": 0.2, "targeting": 0.2, "policy_proximity": 0.2, "uptake": 0.2}))
    ir_hi = validate_event(base_event(event_id="R1", type="IR", impact_weight=None, irreversibility=1.0))
    ir_lo = validate_event(base_event(event_id="R2", type="IR", impact_weight=None, irreversibility=0.2))
    m = monthly_l_ir_from_events("2026-03", [strong, weak, ir_hi, ir_lo])
    assert m.l == 1.0 and m.l_source_event == "L1"
    assert m.ir == 1.0 and m.ir_source_event == "R1"
    assert m.l_events_seen == 2 and m.ir_events_seen == 2


def test_incomplete_l_classification_not_counted_as_zero():
    part = validate_event(base_event(event_id="LX", type="L", impact_weight=None, llm_classification={
        "intensity": None, "targeting": .9, "policy_proximity": .9, "uptake": .9}))
    m = monthly_l_ir_from_events("2026-03", [part])
    assert m.l_events_incomplete == ("LX",), "keskeneräistä luokitusta ei kirjattu"
    assert m.l == 0.0 and m.l_source_event is None


def test_empty_month_is_zero_by_design():
    m = monthly_l_ir_from_events("2026-03", [])
    assert m.l == 0.0 and m.ir == 0.0
    assert "tarkoituksella" in m.basis
    assert compute_rri_raw(150.0, m.l, m.ir) == 0.0


def test_rri_formula():
    assert abs(compute_rri_raw(100.0, 0.5, 0.5) - 75.0) < 1e-9      # 100*0.5*1.5
    assert compute_rri_raw(300.0, 1.0, 1.0) == 600.0                # teoreettinen max
    for bad in ((-1, .5, .5), (301, .5, .5), (100, 1.1, .5), (100, .5, 1.1)):
        try:
            compute_rri_raw(*bad)
        except RRIError:
            pass
        else:
            raise AssertionError(f"{bad} hyväksyttiin")


def test_rri_scaling_expanding_has_no_look_ahead():
    raw = {"2026-01": 10.0, "2026-02": 40.0, "2026-03": 20.0}
    s = scale_rri(raw, "expanding")
    assert s["2026-01"] == 100.0, "ensimmäinen kuukausi on oma maksiminsa"
    assert s["2026-02"] == 100.0
    assert s["2026-03"] == 50.0, "maaliskuu skaalattu helmikuun maksimiin"
    f = scale_rri(raw, "full-window")
    assert f["2026-01"] == 25.0, "full-window käyttää koko ikkunan maksimia"


def test_rri_baseline_requires_explicit_max():
    try:
        scale_rri({"2026-01": 10.0}, "baseline")
    except RRIError as e:
        assert "baseline" in str(e)
    else:
        raise AssertionError("baseline hyväksyi puuttuvan rajan")


def test_rri_all_zero_scales_to_zero_not_hundred():
    s = scale_rri({"2026-01": 0.0, "2026-02": 0.0}, "expanding")
    assert all(v == 0.0 for v in s.values()), "degeneroitunut tapaus ei saa antaa 100"


def test_audit_trail_reaches_evidence():
    evs = load_events(ROOT / "synthetic_events.json")
    months = months_in_range("2026-01", "2026-12")
    buckets = aggregate(evs, "FULL", months)
    scaled = scale_full(buckets)
    m = next(m for m in months if sum(buckets[m].counts.values()) > 0)
    lir = monthly_l_ir_from_events(m, evs)
    x = explain_month(m, buckets[m], scaled[m], evs, lir=lir, rri_scaled=None)
    assert x["events"], "audit trail ei sisällä yhtään tapahtumaa"
    e0 = x["events"][0]
    assert e0["evidence"] and e0["evidence"][0]["retrieved_at"], "todisteesta puuttuu hakuhetki"
    assert x["RRI"]["formula"] == "SP x L x (1 + IR)"
    assert x["RRI"]["raw"] is not None
    assert isinstance(format_explain(x), str)


# ── fetch_statements: virhe ei saa kadota (korjattu 2026-09-05) ──────
def test_fetch_statements_does_not_swallow_errors():
    """Ainoa hakija joka aiemmin nielaisi poikkeuksen.

    Rikkinäinen proxy tuotti tyhjän listan ilman virhettä, ja tulos
    näytti siltä että lausuntoja ei ole.
    """
    import fetchers
    orig = fetchers._post
    fetchers._post = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("proxy alhaalla"))
    try:
        # A) ilman errors-listaa poikkeus nousee läpi
        try:
            fetchers.fetch_statements(["X:1/2026"])
        except RuntimeError as e:
            assert "proxy alhaalla" in str(e)
        else:
            raise AssertionError("poikkeus nieltiin — tyhjä tulos ilman virhettä")

        # B) errors-listan kanssa virhe kirjataan eikä katoa
        errs = []
        out = fetchers.fetch_statements(["X:1/2026", "Y:2/2026"], errors=errs)
        assert out == [], "rikkinäinen haku tuotti tapahtumia"
        assert len(errs) == 2, f"virheitä kirjattiin {len(errs)}, odotettiin 2"
        assert all("proxy alhaalla" in e["error"] for e in errs)
        assert all(e["tunnus"] for e in errs), "virheestä puuttuu tunnus"
    finally:
        fetchers._post = orig


def test_fetch_statements_distinguishes_missing_from_empty():
    """Hanketta ei löytynyt EI ole sama kuin nolla lausuntoa."""
    import fetchers
    orig = fetchers._post
    fetchers._post = lambda *a, **k: {"data": {"result": []}}
    try:
        errs = []
        out = fetchers.fetch_statements(["Z:9/2026"], errors=errs)
        assert out == []
        assert len(errs) == 1 and "ei löytynyt" in errs[0]["error"]
    finally:
        fetchers._post = orig


def test_basis_distinguishes_undetermined_from_observed_zero():
    """Kaikki luokitukset kesken EI ole sama kuin todettu nolla.

    Molemmissa l == 0.0. Ensimmäisessä nolla on tiedon puute,
    toisessa havainto. basis-teksti ja l_is_determined erottavat ne.
    """
    from rri import monthly_l_ir_from_events

    # A) kaikki kesken — uptake None (lausunto ei voi todistaa uptakea)
    kesken = validate_event(base_event(event_id="LK", type="L", impact_weight=None,
        llm_classification={"intensity": .4, "targeting": .7,
                            "policy_proximity": .4, "uptake": None}))
    a = monthly_l_ir_from_events("2026-03", [kesken])
    assert a.l == 0.0
    assert a.l_source_event is None
    assert a.l_events_incomplete == ("LK",)
    assert a.l_is_determined is False
    assert "MÄÄRITTÄMÄTÖN" in a.basis and "tiedon" in a.basis

    # B) täysi luokitus jossa aito nolla
    nolla = validate_event(base_event(event_id="LN", type="L", impact_weight=None,
        llm_classification={"intensity": .4, "targeting": .7,
                            "policy_proximity": .4, "uptake": 0.0}))
    b = monthly_l_ir_from_events("2026-03", [nolla])
    assert b.l == 0.0
    assert b.l_source_event == "LN"
    assert b.l_events_incomplete == ()
    assert b.l_is_determined is True
    assert "havaintona" in b.basis

    # C) ei lainkaan L-tapahtumia
    c = monthly_l_ir_from_events("2026-03", [])
    assert c.l_is_determined is True and "tarkoituksella" in c.basis

    # Kaikki kolme antavat l == 0.0 mutta ovat eri tiloja
    assert a.basis != b.basis != c.basis


# ── Laatijan talteenotto ja normalisointi ────────────────────────────
def test_actor_from_title_recovers_missing_actors():
    """29/2265 lausunnolta puuttui laatija-kenttä; nimi oli nimekkeessä."""
    from fetchers import actor_from_title
    cases = {
        "Erkki Hurtig; lausunto": "Erkki Hurtig",
        "Saamelaiskäräjät; lausunto": "Saamelaiskäräjät",
        "Korkein hallinto-oikeus; Ei lausuttavaa": "Korkein hallinto-oikeus",
        "Ålands Landskapsregering; Utlåtande": "Ålands Landskapsregering",
        "Matkailu- ja Ravintolapalvelut MaRa ry; täydentävä lausunto":
            "Matkailu- ja Ravintolapalvelut MaRa ry",
    }
    for src, want in cases.items():
        assert actor_from_title(src) == want, f"{src!r} -> {actor_from_title(src)!r}"


def test_actor_from_title_rejects_filenames_and_empty():
    """Väärä nimi on huonompi kuin merkitty puuttuva."""
    from fetchers import actor_from_title
    for bad in ("KL_Lausunto_vesilaki_merituulivoima_120826",
                "Syken_lausunto_HE_laiksi_vesilainmuuttamisesta",
                "LVV lausunto TEM VL_muutos merituulivoima",
                "(nimeke puuttuu)", "", None, "lausunto"):
        assert actor_from_title(bad) is None, f"{bad!r} hyväksyttiin"


def test_normalize_actor_strips_index_suffix_only():
    """(n) on rakenteellinen tunniste, EI aluejärjestön erotin.

    Todennettu 5.9.2026: yksikään kantanimi ei esiinny kahdessa eri
    numeroidussa muodossa, ja kantanimi ilman numeroa puuttuu 7/8
    tapauksessa kokonaan.
    """
    from fetchers import normalize_actor
    assert normalize_actor("Elinkeinoelämän keskusliitto EK (1)") == \
           "Elinkeinoelämän keskusliitto EK"
    assert normalize_actor("Varsinais-Suomen ELY-keskus (2)") == \
           "Varsinais-Suomen ELY-keskus"
    assert normalize_actor("Suomen Omakotiliitto ry ") == "Suomen Omakotiliitto ry"
    # oikeushenkilömuotoa EI poisteta — se erottaa aidosti eri toimijoita
    assert normalize_actor("Fingrid Oyj") == "Fingrid Oyj"
    assert normalize_actor(None) is None


# ── actor_role: säännöt, poikkeukset, aliakset, provenienssi ─────────
def test_actor_role_compound_suffix_anchor():
    """Ankkuri on X\\b — ei \\bX (yhdyssana) eikä X$ (perässä lyhenne)."""
    from actors import actor_role
    cases = {
        "Energiavirasto": "viranomainen",                       # yhdyssana
        "Turvallisuus- ja kemikaalivirasto TUKES": "viranomainen",  # perässä lyhenne
        "Työ- ja elinkeinoministeriö": "viranomainen",
        "Energiateollisuus ry": "etujarjesto",
        "Suomen Arkkitehtiliitto ry SAFA": "etujarjesto",       # ry keskellä
        "Elinkeinoelämän keskusliitto EK": "etujarjesto",       # keskusliitto != keskus
        "Fortum Oyj": "toimija",
        "Espoon kaupunki": "kunta",
        "Nurmijärven kunta": "kunta",
        "Aalto-yliopisto": "tutkija",
        "Suomen ilmastopaneeli": "tutkija",
    }
    for name, want in cases.items():
        role, src, conf, _ = actor_role(name)
        assert role == want, f"{name!r} -> {role!r}, odotettiin {want!r}"
        assert src == "saanto" and conf == 0.9


def test_actor_role_named_exceptions():
    """Peruste on intressi, ei oikeudellinen muoto."""
    from actors import actor_role
    for name, want in (("Suomen Kuntaliitto ry", "etujarjesto"),
                       ("Saamelaiskäräjät", "etujarjesto"),
                       ("Fingrid Oyj", "toimija")):
        role, src, conf, reason = actor_role(name)
        assert role == want and src == "poikkeus" and conf == 0.9
        assert reason and len(reason) > 40, "poikkeukselta puuttuu perustelu"


def test_actor_role_never_guesses():
    """Ratkaisematon palauttaa None, ei arvausta.

    Neljä avointa roolikysymystä: tuomioistuimet, maakuntaliitot,
    valtion tutkimuslaitokset, yksityishenkilöt.
    """
    from actors import actor_role
    for name in ("Korkein hallinto-oikeus", "Uudenmaan liitto - Nylands förbund",
                 "Erkki Hurtig", "WWF Suomi", "Keva"):
        role, src, conf, reason = actor_role(name)
        assert role is None and src is None and conf is None, f"{name!r} sai roolin {role!r}"
        assert reason and "arvata" in reason


def test_canonical_merges_measured_aliases_only():
    """Alias-taulukko on mitattu luettelo, ei kaava."""
    from actors import canonical, NOT_ALIASES
    # sama organisaatio
    assert canonical("Suomen ympäristökeskus SYKE") == "Suomen ympäristökeskus (Syke)"
    assert canonical("Elinkeinoelämän Keskusliitto EK") == "Elinkeinoelämän keskusliitto EK"
    # organisaatiohierarkia: yksikkö -> emo
    assert canonical("Suomen ympäristökeskuksen kv. YVA- ja SOVA -asiat") == \
           "Suomen ympäristökeskus (Syke)"
    # EI yhdistetä: piirijärjestö on eri toimija
    for name in NOT_ALIASES:
        assert canonical(name) == name, f"{name!r} yhdistettiin — sen ei pitäisi"


def test_canonical_strips_zero_width_characters():
    """U+200B nimen lopussa teki VTT:stä kaksi toimijaa. Ei näy silmällä."""
    from actors import canonical
    a = canonical("Teknologian tutkimuskeskus VTT Oy\u200b")
    b = canonical("Teknologian tutkimuskeskus VTT Oy")
    assert a == b == "Teknologian tutkimuskeskus VTT Oy"


def test_yksityishenkilo_role_exists_but_is_not_rule_derived():
    """430/752 laatijaa esiintyy kerran; osa on yksityishenkilöitä.

    Rooli on ROLES-listalla, mutta sääntö EI tuota sitä — henkilönimeä
    ei voi tunnistaa regexillä. role_source olisi "extractor".
    """
    from actors import ROLES, actor_role
    assert "yksityishenkilo" in ROLES
    role, src, conf, _ = actor_role("Erkki Hurtig")
    assert role is None and src is None and conf is None


def test_role_confidence_flags_ambiguous_suffixes():
    """`laitos` ja `keskus` osuvat sekä virastoihin että tutkimuslaitoksiin.

    role_source: "saanto" kertoo että pääte tunnistettiin, EI että se on
    luotettava. Ilman role_confidencea "Energiavirasto" ja "Suomen
    ympäristökeskus" saisivat identtisen merkinnän.
    """
    from actors import actor_role
    # yksikäsitteinen
    for name in ("Energiavirasto", "Verohallinto", "Työ- ja elinkeinoministeriö",
                 "Varsinais-Suomen ELY-keskus"):
        role, src, conf, _ = actor_role(name)
        assert (role, src, conf) == ("viranomainen", "saanto", 0.9), \
            f"{name!r} -> {(role, src, conf)}"
    # monitulkintainen: valtion tutkimuslaitos
    for name in ("Suomen ympäristökeskus (Syke)", "Luonnonvarakeskus (Luke)",
                 "Ilmatieteen laitos", "Valtion taloudellinen tutkimuskeskus VATT"):
        role, src, conf, reason = actor_role(name)
        assert role == "viranomainen" and src == "saanto", f"{name!r}"
        assert conf == 0.5, f"{name!r} sai luottamuksen {conf}, odotettiin 0.5"
        assert "MONITULKINTAINEN" in reason


def test_ely_rule_precedes_generic_keskus_rule():
    """Järjestysvirhe löytyi mittaamalla: viisi ELY-keskusta sai 0.5."""
    from actors import actor_role
    for name in ("Varsinais-Suomen ELY-keskus", "Etelä-Pohjanmaan ELY-keskus"):
        assert actor_role(name)[2] == 0.9, f"{name!r} merkittiin monitulkintaiseksi"


def test_named_state_agencies_resolve_to_09():
    """Yhdeksän virastoa nimetty poikkeuksina: tehtävä ei ole tutkimus.

    Sama käsittely kuin Fingrid sai — päätös funktion perusteella, ei
    rekisteristä. Valtiokonttorin kirjanpitoyksikköluettelo todistaa
    että nämä ovat valtion virastoja, mutta EI erottele tutkimus-
    laitosta hallintovirastosta.
    """
    from actors import actor_role
    for name in ("Tilastokeskus", "Maanmittauslaitos", "Säteilyturvakeskus",
                 "Huoltovarmuuskeskus", "Rajavartiolaitos",
                 "Innovaatiorahoituskeskus Business Finland",
                 "Oikeusrekisterikeskus", "Kansaneläkelaitos (Kela)",
                 "Onnettomuustutkintakeskus"):
        role, src, conf, reason = actor_role(name)
        assert (role, src, conf) == ("viranomainen", "poikkeus", 0.9), \
            f"{name!r} -> {(role, src, conf)}"
        assert reason and len(reason) > 25


def test_ely_written_out_and_2026_successor():
    """11 nimeä jäi 0.5:een: sääntö tunsi vain lyhenteen ELY-keskus."""
    from actors import actor_role
    for name in ("Uudenmaan elinkeino-, liikenne- ja ympäristökeskus",
                 "Etelä-Pohjanmaan elinkeino-, liikenne- ja ympäristökeskus",
                 "Lounais-Suomen elinvoimakeskus",      # 2026-uudistuksen nimi
                 "Sisä-Suomen elinvoimakeskus"):
        role, src, conf, _ = actor_role(name)
        assert (role, conf) == ("viranomainen", 0.9), f"{name!r} -> {(role, conf)}"


def test_university_department_is_not_state_agency():
    """`laitos` osui ennen `yliopisto`-sääntöä."""
    from actors import actor_role
    role, _, conf, _ = actor_role("Itä-Suomen yliopisto, oikeustieteiden laitos")
    assert (role, conf) == ("tutkija", 0.9)


def test_municipal_utility_is_kunta_not_state():
    """`Oulun Vesi -liikelaitos` luokittui valtion viranomaiseksi."""
    from actors import actor_role
    role, _, conf, _ = actor_role("Oulun Vesi -liikelaitos")
    assert (role, conf) == ("kunta", 0.9)


def test_genuinely_dual_institutes_stay_ambiguous():
    """Kuusi tutkimuslaitosta jää 0.5:een — päätös on auki, ei arvattu."""
    from actors import actor_role
    for name in ("Suomen ympäristökeskus (Syke)", "Luonnonvarakeskus (Luke)",
                 "Ilmatieteen laitos", "Geologian tutkimuskeskus",
                 "Terveyden ja hyvinvoinnin laitos THL",
                 "Valtion taloudellinen tutkimuskeskus VATT"):
        role, src, conf, reason = actor_role(name)
        assert conf == 0.5, f"{name!r} sai luottamuksen {conf} — päätöstä ei ole tehty"
        assert "MONITULKINTAINEN" in reason


def test_structural_limitation_is_documented():
    """actor_role kuvaa toimijaa, ei tekoa — rajoite on kirjattava.

    Testi ei testaa logiikkaa vaan sitä, että rajoite pysyy koodissa.
    Se paikannettiin 5.9.2026 kun intressiperuste romahti
    hyvinvointialueeseen: jokaisella julkisella toimijalla on
    rahoitusintressi, joten se ei erottele mitään.

    Seuraus: RRI ei erota asiantuntijalausuntoa edunvalvonnasta.
    Ne saavat saman L:n. Rajoite, ei bugi — mutta se on tiedettävä
    ennen kuin sarjasta sanotaan mitään vaikuttamisesta.
    """
    import inspect
    import actors
    src = inspect.getsource(actors)
    for marker in ("RAKENTEELLINEN RAJOITE",
                   "kuvaa TOIMIJAA, ei TEKOA",
                   "ei erota asiantuntija",
                   "KOLME ERI LAJIA AUKI",
                   # tarkennus: korjaus ei ole toimijakohtainen kenttä
                   "TOIMIJAN JA ASIAN VÄLINEN",
                   "TAPAHTUMAKOHTAINEN luokitus"):
        assert marker in src, f"rajoitteen kirjaus puuttuu: {marker!r}"


def test_open_cases_are_classified_by_kind():
    """Kolme eri lajia auki — ne eivät ratkea samalla korjauksella."""
    import inspect
    import actors
    src = inspect.getsource(actors)
    for kind in ("AMBIGUUS", "PUUTTUVA", "PÄÄTETTÄVÄ"):
        assert kind in src, f"luokitus puuttuu: {kind}"
    # tuomioistuin on PUUTTUVA (perustuslaillinen), ei ambiguus
    assert "vallan\n#                         kolmijako" in src or "kolmijako" in src


# ── Decision Trace (lisätty 2026-09-07) ─────────────────────────────
def _mk_trace(tmp, **over):
    import json, tempfile, os
    d = {
        "_schema": "aci/decision-trace/v0.1",
        "_locked_at": "2026-09-07",
        "_revision": 1,
        "subject": {"nimi": "Testihanke"},
        "observed": [{
            "node_id": "n1", "kind": "observed",
            "occurred_at": "2026-08-10T00:00:00+03:00",
            "known_at": "2026-08-10T12:00:00+03:00",
            "retrieved_at": "2026-09-07T10:00:00+00:00",
            "source": "testi",
            "evidence": [{"quote": "q", "location": "l",
                          "source_url": "https://x",
                          "retrieved_at": "2026-09-07T10:00:00+00:00"}],
        }],
        "expected": [{"step": "seuraava vaihe", "status": "ei tapahtunut"}],
    }
    d.update(over)
    p = os.path.join(tmp, "t.json")
    open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
    return p


def test_trace_refuses_expected_with_timestamp():
    """Odotettu vaihe EI saa olla aikaleimaa.

    expected-solmuilla on usein `estimate`-kentta ("vko 44/2026",
    "2030-2032"), ja se on houkutteleva lukea aikaleimana. Jos niin
    tehdaan, sarja tayttyy tapahtumista joita ei ole tapahtunut ja
    PRE/FULL-erottelu menettaa merkityksensa.
    """
    import tempfile
    from traces import load_trace, TraceError
    with tempfile.TemporaryDirectory() as tmp:
        p = _mk_trace(tmp, expected=[{"step": "x",
                                      "occurred_at": "2027-01-01T00:00:00+02:00"}])
        try:
            load_trace(p)
        except TraceError as e:
            assert "EI OLE TAPAHTUMA" in str(e)
        else:
            raise AssertionError("expected sai aikaleiman lapi")


def test_trace_expected_never_converted():
    import tempfile
    from traces import load_trace, to_raw_events
    with tempfile.TemporaryDirectory() as tmp:
        t = load_trace(_mk_trace(tmp))
        events, skipped = to_raw_events(t)
        assert len(events) == 1, "observed ei muuntunut"
        assert skipped == [], "turha ohitus"
        assert t.n_expected == 1
        # expected EI ole events-listalla eika skipped-listalla:
        # se ei ole ehdokas.
        assert not any("seuraava" in str(e) for e in events)


def test_trace_does_not_infer_type():
    """Luokitus on Extractorin tyo. Tyyppia ei pääpäätellä."""
    import tempfile
    from traces import load_trace, to_raw_events
    with tempfile.TemporaryDirectory() as tmp:
        t = load_trace(_mk_trace(tmp))
        events, _ = to_raw_events(t)
        assert events[0]["type"] is None
        assert all(v is None for v in events[0]["llm_classification"].values())


def test_trace_known_at_may_be_missing_but_is_flagged():
    """known_at None = 'julkiseksitulohetkea ei tiedeta', ei nolla viivetta."""
    import tempfile
    from traces import load_trace, to_raw_events, summarize
    with tempfile.TemporaryDirectory() as tmp:
        p = _mk_trace(tmp, observed=[{
            "node_id": "n1", "kind": "observed",
            "occurred_at": "2025-01-01T00:00:00+02:00",
            "known_at": None,
            "retrieved_at": "2026-09-07T10:00:00+00:00", "source": "s",
            "evidence": [{"quote": "q", "location": "l", "source_url": "https://x",
                          "retrieved_at": "2026-09-07T10:00:00+00:00"}]}])
        t = load_trace(p)
        events, _ = to_raw_events(t)
        assert events[0]["known_at"] is None
        assert events[0]["_known_at_missing"] is True
        assert summarize(t)["known_at_missing"] == 1


def test_trace_causal_order_skips_not_fixes():
    import tempfile
    from traces import load_trace, to_raw_events
    with tempfile.TemporaryDirectory() as tmp:
        p = _mk_trace(tmp, observed=[{
            "node_id": "bad", "kind": "observed",
            "occurred_at": "2026-08-10T00:00:00+03:00",
            "known_at": "2026-07-01T00:00:00+03:00",
            "retrieved_at": "2026-09-07T10:00:00+00:00", "source": "s",
            "evidence": [{"quote": "q", "location": "l", "source_url": "https://x",
                          "retrieved_at": "2026-09-07T10:00:00+00:00"}]}])
        t = load_trace(p)
        events, skipped = to_raw_events(t)
        assert events == [] and len(skipped) == 1
        assert "kausaalijärjestys" in skipped[0]["reason"]


def test_trace_requires_lock_date_and_known_domain():
    import tempfile
    from traces import load_trace, TraceError, DOMAINS, DECISION_BODIES
    assert "fiskaali" in DOMAINS and "energia" in DOMAINS
    assert "kunnanvaltuusto" in DECISION_BODIES
    with tempfile.TemporaryDirectory() as tmp:
        for over, marker in (({"_locked_at": None}, "LUKITTU"),
                             ({"domain": "avaruus"}, "tuntematon domain")):
            try:
                load_trace(_mk_trace(tmp, **over))
            except TraceError as e:
                assert marker in str(e), f"{over} -> {e}"
            else:
                raise AssertionError(f"{over} meni lapi")


def test_trace_revision_and_hash_detect_silent_overwrite():
    """Sama _locked_at eri sisallolla ei saa mennä lapi huomaamatta.

    VIKA JOKA TAMAN AIHEUTTI: lansirata-trace lahetettiin neljasti,
    jokaisessa _locked_at 2026-09-07, tiedosto kasvoi 4 372 -> 14 961
    tavuun. Vanhempi versio olisi korvannut uudemman jos vastaanottaja
    ei olisi diffannut SISALTOA — polun tarkistus ei riittanyt.
    """
    import json, tempfile, os
    from traces import load_trace, content_hash, TraceError
    with tempfile.TemporaryDirectory() as tmp:
        p = _mk_trace(tmp)
        d = json.load(open(p, encoding="utf-8"))
        d["_content_hash"] = content_hash(d)
        open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))

        t = load_trace(p)
        assert t.revision == 1
        assert t.hash_matches is True

        # muokkaus tiivisteen laskemisen jalkeen -> hylataan
        d["subject"]["nimi"] = "muutettu"
        open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
        try:
            load_trace(p)
        except TraceError as e:
            assert "_content_hash ei täsmää" in str(e)
            assert "nosta _revision" in str(e)
        else:
            raise AssertionError("muokattu trace meni lapi")


def test_trace_hash_none_is_not_mismatch():
    """Tiivisteen puuttuminen != ristiriita. Vanhat tracet ovat ilman."""
    import tempfile
    from traces import load_trace
    with tempfile.TemporaryDirectory() as tmp:
        t = load_trace(_mk_trace(tmp))       # ei _content_hash-kenttaa
        assert t.content_hash_stored is None
        assert t.hash_matches is None, "puuttuva tiiviste luettiin ristiriidaksi"
        assert t.content_hash_actual, "laskettu tiiviste puuttuu"


def test_trace_rejects_bad_revision():
    import tempfile
    from traces import load_trace, TraceError
    with tempfile.TemporaryDirectory() as tmp:
        for bad in (0, -1, "1", 1.5):
            try:
                load_trace(_mk_trace(tmp, _revision=bad))
            except TraceError as e:
                assert "_revision" in str(e)
            else:
                raise AssertionError(f"_revision={bad!r} meni lapi")


def test_trace_hash_stable_under_key_order():
    """Tiiviste ei saa muuttua avainjarjestyksesta."""
    from traces import content_hash
    a = {"z": 1, "a": {"y": 2, "b": 3}, "_content_hash": "vanha"}
    b = {"a": {"b": 3, "y": 2}, "z": 1}
    assert content_hash(a) == content_hash(b)


# ── Extractor (lisätty 2026-09-09) ──────────────────────────────────
FI_FORM = """Lausunto
Lausunnonantajan taho
        Toimiala- tai etujärjestö
Kasvihuonekaasujen vähentäminen (strategian luku 2.2)
        -
Avoin vastaus kasvihuonekaasuja koskien
        Kannatamme tavoitetta mutta pidämme aikataulua liian tiukkana.
Ydinenergian käyttö (strategian luku 2.7)
        -
Avoin vastaus ydinenergiaa koskien
        -
Muuta kommentoitavaa
        Yleinen huomio lopuksi.
                                Lausuntopalvelu.fi        1/3
"""

SV_FORM = """Utlåtande
Utlåtandegivarens instans
        Annan instans
Minskning av växthusgasutsläpp (kapitel 2.2 i strategin)
        -
Fritt svar om minskning av växthusgasutsläpp
        Vi stöder målet men tidtabellen är för snäv.
Forskning och konkurrenskraft (kapitel 2. 9 i strategin)
        -
Fritt svar om forskning
        Mera resurser behövs.
"""


def test_extractor_parses_both_languages():
    """Lomake on kaksikielinen. Yksikielinen jäsennin luki
    ruotsinkielisen lausunnon TYHJÄKSI ja se raportoitiin havaintona."""
    from extractor import parse_form
    fi = parse_form(FI_FORM)
    sv = parse_form(SV_FORM)
    assert fi.sections_answered == ["2.2"], fi.sections_answered
    assert sv.sections_answered == ["2.2", "2.9"], sv.sections_answered
    # "kapitel 2. 9" — välilyönti numerossa
    assert not sv.is_empty


def test_extractor_free_text_pairs_with_preceding_section():
    """`Avoin vastaus` kuuluu EDELTÄVÄLLE luvulle, ei omakseen."""
    from extractor import parse_form
    f = parse_form(FI_FORM)
    secs = {a.section for a in f.answers}
    assert "2.2" in secs
    # 2.7:n vapaa kenttä oli "-", joten sitä EI kirjata
    assert "2.7" not in f.sections_answered
    # yleinen kenttä on None-avaimella
    assert None in secs


def test_extractor_empty_differs_from_unparsed():
    """is_empty ja parse_confidence: low ovat ERI ASIOITA.

    Tyhjä lausunto = lomake jäsentyi, sisältöä ei ole.
    Jäsentymätön    = lomaketta ei tunnistettu — voi olla mitä tahansa.
    """
    from extractor import parse_form
    empty = parse_form("Otsikko (strategian luku 2.2)\n        -\n"
                       "Avoin vastaus jotain\n        -\n")
    assert empty.is_empty
    assert empty.parse_confidence == "high", "jäsentyi kyllä"

    junk = parse_form("Satunnaista tekstia ilman lomaketta.")
    assert junk.parse_confidence == "low"
    assert junk.n_questions_seen == 0


def test_extractor_intensity_does_not_scale_with_coverage():
    """MÄÄRÄ EI OLE VOIMAKKUUS.

    Ilmastopaneeli vastasi 12/12 lukuun ja 17 494 merkkiin. Jos
    intensity skaalattaisiin kattavuudella, se saisi automaattisesti
    korkeimman arvon — mutta se on lakisaateinen asiantuntijaelin joka
    lausuu kokonaisuudesta. Eri rooli, ei vahvempi vaikuttaminen.
    """
    from extractor import parse_form, roe_from_form
    wide = parse_form(FI_FORM + "".join(
        f"Luku (strategian luku 2.{i})\n        -\nAvoin vastaus {i}\n"
        f"        Pitka vastaus {'x'*400}\n" for i in range(3, 12)))
    narrow = parse_form(FI_FORM)
    a = roe_from_form(wide, "tutkija")
    b = roe_from_form(narrow, "etujarjesto")
    assert a["intensity"] == b["intensity"] == 0.40, "kattavuus vaikutti intensityyn"
    assert a["form"]["total_chars"] > b["form"]["total_chars"] * 3


def test_extractor_empty_statement_has_no_intensity():
    """Tyhjä lausunto ei ole intensity 0.40 vaan ei kantaa lainkaan."""
    from extractor import parse_form, roe_from_form
    f = parse_form("Otsikko (strategian luku 2.2)\n        -\n"
                   "Avoin vastaus x\n        -\n")
    r = roe_from_form(f, "toimija")
    assert r["intensity"] is None
    assert "TYHJÄ" in r["_intensity_note"]
    assert r["targeting"] is None


def test_extractor_never_invents_targeting_number():
    """targeting luetaan lomakkeesta; numeroarvoa EI keksitä."""
    from extractor import parse_form, roe_from_form
    for txt, role in ((FI_FORM, "etujarjesto"), (SV_FORM, "toimija")):
        r = roe_from_form(parse_form(txt), role)
        assert r["targeting"] is None, "targeting-numero keksittiin"
        assert r["form"]["sections_answered"], "kohde puuttuu lomakkeesta"
        assert r["uptake"] is None
        assert r["stance"] is None
        assert r["policy_proximity"] == 0.40


# ── snapshot_trace (lisätty 2026-09-16) ─────────────────────────────
_KOHDE = {
    "tunnus": "XX001:00/2026", "asianumerot": ["VN/1/2026"],
    "nimi": {"fi": "Testihanke"}, "tila": "KAYNNISSA",
    "aloitusPaiva": "2026-08-10", "julkaisuaika": "2026-08-10T12:00:00",
}
_ETAPIT = [{"alku": "2026-09-03", "loppu": "2026-10-02",
            "valmisteluvaihe": "LAUSUNTOMENETTELY", "vaihe": "KAYNNISSA"}]
_ASIAK = [{"uuid": "aaaabbbb-cccc", "tyyppi": "LAUSUNTOPYYNTO",
           "laatimispaiva": "2026-09-03", "luotu": "2026-09-03T08:00:00Z",
           "nimi": {"fi": "Lausuntopyyntö"}, "laatija": {"fi": "TEM"}},
          {"uuid": "ddddeeee-ffff", "tyyppi": "KIRJE",
           "laatimispaiva": "2026-09-03", "luotu": "2026-09-03T08:00:00Z",
           "nimi": None, "laatija": {"fi": "TEM"}}]


def test_snapshot_ei_keksi_puuttuvaa_paivaa():
    """occurred_at ei saa syntya tyhjasta."""
    from snapshot_trace import nodes_from_kohde
    assert nodes_from_kohde({}, "2026-09-16T00:00:00+00:00") == []
    k = dict(_KOHDE); k.pop("aloitusPaiva")
    assert nodes_from_kohde(k, "2026-09-16T00:00:00+00:00") == []


def test_snapshot_merkitsee_asettamispaivan_puuttumisen():
    """asettamisPaiva ja aloitusPaiva ovat ERI KENTTIA eri semantiikalla."""
    from snapshot_trace import nodes_from_kohde
    n = nodes_from_kohde(_KOHDE, "2026-09-16T00:00:00+00:00")[0]
    assert n["occurred_at_source"] == "aloitusPaiva"
    assert n["_derived"]["asettamisPaiva_puuttuu"] is True
    k = dict(_KOHDE, asettamisPaiva="2026-08-01")
    n2 = nodes_from_kohde(k, "2026-09-16T00:00:00+00:00")[0]
    assert n2["occurred_at_source"] == "asettamisPaiva"
    assert n2["occurred_at"].startswith("2026-08-01")


def test_snapshot_ohittaa_nimettoman_asiakirjan():
    """Hankeikkuna palauttaa duplikaatteja joilla nimi on None."""
    from snapshot_trace import nodes_from_asiakirjat
    n = nodes_from_asiakirjat(_ASIAK, "2026-09-16T00:00:00+00:00")
    assert len(n) == 1, "nimeton duplikaatti paasi lapi"
    assert n[0]["doc_type"] == "LAUSUNTOPYYNTO"


def test_snapshot_laskettu_tila_ei_ole_proosaa():
    """Jokainen arvo on funktio hakutuloksesta, ei tulkintaa."""
    from snapshot_trace import derive_state
    s = derive_state(_KOHDE, _ETAPIT, _ASIAK, "2026-09-16")
    assert s["asiakirjat_yhteensa"] == 2
    assert s["asiakirjat_tyypeittain"] == {"LAUSUNTOPYYNTO": 1, "KIRJE": 1}
    assert s["lausuntoja_hankeikkunassa"] == 0
    assert s["lausuntokierros_auki_vrk"] == 13
    assert s["lausuntokierros_jaljella_vrk"] == 16
    # uptake EI saa olla 0
    assert s["uptake"] is None


def test_snapshot_uptake_ei_koskaan_nolla():
    from snapshot_trace import derive_state
    for et in ([], _ETAPIT):
        assert derive_state(_KOHDE, et, [], "2026-09-16")["uptake"] is None


def test_snapshot_tuottaa_validin_tracen():
    """Kirjoitettu tiedosto menee traces.py:n validoinnin lapi."""
    import tempfile, json as _j
    from pathlib import Path
    from traces import load_trace
    import snapshot_trace as st
    orig = st.fetch_hankeikkuna
    st.fetch_hankeikkuna = lambda t, tries=3: {
        "kohde": _KOHDE, "etapit": _ETAPIT, "asiakirjat": _ASIAK}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            p, s = st.make_snapshot("XX001:00/2026", tmp, today="2026-09-16")
            t = load_trace(p)
            assert t.hash_matches is True, "tiiviste ei tasmaa"
            assert t.n_observed == 3          # kohde + etappi + 1 asiakirja
            assert t.n_expected == 0
            assert s["_diff"]["uusia_solmuja"] == 3
    finally:
        st.fetch_hankeikkuna = orig


def test_snapshot_ei_muuta_edellista():
    """EDELLISTA EI KOSKETA. Uusi tiedosto, _supersedes viittaa."""
    import tempfile, json as _j
    from pathlib import Path
    import snapshot_trace as st
    orig = st.fetch_hankeikkuna
    st.fetch_hankeikkuna = lambda t, tries=3: {
        "kohde": _KOHDE, "etapit": _ETAPIT, "asiakirjat": _ASIAK}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            p1, s1 = st.make_snapshot("XX001:00/2026", tmp, today="2026-09-16")
            ennen = p1.read_bytes()
            p2, s2 = st.make_snapshot("XX001:00/2026", tmp, today="2026-09-20",
                                      prev_path=p1)
            assert p1.read_bytes() == ennen, "EDELLISTA MUUTETTIIN"
            assert p1 != p2
            assert s2["_supersedes"]["content_hash"] == s1["_content_hash"]
            assert s2["_diff"]["uusia_solmuja"] == 0   # mikaan ei muuttunut
    finally:
        st.fetch_hankeikkuna = orig


def test_snapshot_expected_kannetaan_eika_keksita():
    """Automaatti EI lisaa expected-rivejä. Se kantaa ne edellisesta."""
    import tempfile, json as _j
    from pathlib import Path
    import snapshot_trace as st
    orig = st.fetch_hankeikkuna
    st.fetch_hankeikkuna = lambda t, tries=3: {
        "kohde": _KOHDE, "etapit": _ETAPIT, "asiakirjat": _ASIAK}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            p1, _ = st.make_snapshot("XX001:00/2026", tmp, today="2026-09-16")
            d = _j.loads(p1.read_text(encoding="utf-8"))
            d["expected"] = [
                {"step": "aanestys", "status": "ei tapahtunut"},
                {"step": "asiakirja saapuu", "status": "ei tapahtunut",
                 "_fulfilled_by": "asiakirja-aaaabbbb"},
            ]
            p1.write_text(_j.dumps(d, ensure_ascii=False), encoding="utf-8")
            p2, s2 = st.make_snapshot("XX001:00/2026", tmp, today="2026-09-20",
                                      prev_path=p1)
            steps = [e["step"] for e in s2["expected"]]
            assert "aanestys" in steps, "kantamaton"
            assert "asiakirja saapuu" not in steps, "toteutunutta ei poistettu"
            assert not any("occurred_at" in e for e in s2["expected"])
    finally:
        st.fetch_hankeikkuna = orig


# ── collect.py + laajennettu traces.py (lisätty 2026-09-16) ─────────
def _node(nid="n1", **kw):
    d = {"node_id": nid, "kind": "observed",
         "occurred_at": "2026-09-09T00:00:00+03:00",
         "known_at": "2026-09-09T00:00:00+03:00",
         "retrieved_at": "2026-09-16T00:00:00+00:00", "source": "s",
         "evidence": [{"quote": "q", "location": "l", "source_url": None,
                       "retrieved_at": "2026-09-16T00:00:00+00:00"}]}
    d.update(kw); return d


def _trace(nodes, **kw):
    from traces import content_hash
    t = {"_schema": "aci/decision-trace/v0.1", "_locked_at": "2026-09-16",
         "_revision": 1, "subject": {"nimi": "t"}, "observed": nodes,
         "expected": []}
    t.update(kw); t["_content_hash"] = content_hash(t); return t


def _write(t, tmp, name="t.json"):
    import json, os
    p = os.path.join(tmp, name)
    open(p, "w", encoding="utf-8").write(json.dumps(t, ensure_ascii=False))
    return p


def test_decision_bodies_kattaa_yhtion_hallituksen():
    """Liian kapea enum pakotti Carunan ja PPA:n arvoon yhtiokokous.

    Carunan myynnista paatti Fortumin HALLITUS; PPA on kahden yhtion
    valinen SOPIMUS. Kumpikaan ei ole yhtiokokouspaatos.
    """
    from traces import DECISION_BODIES
    for b in ("yhtion_hallitus", "sopimusosapuolet", "ministerio"):
        assert b in DECISION_BODIES, f"{b} puuttuu"
    assert len(DECISION_BODIES) >= 9


def test_completed_at_ei_saa_edeltaa_paatosta():
    """occurred_at = PAATOS, completed_at = TOTEUMA.

    Carunassa occurred_at oli 2014-03-12 = kaupan toteuma; paatos
    tehtiin 2013. Jos OGAS3 jaljittaa paatoksia, se tarvitsee
    paatospaivan.
    """
    import tempfile
    from traces import load_trace, TraceError
    with tempfile.TemporaryDirectory() as tmp:
        ok = _write(_trace([_node(completed_at="2026-10-01T00:00:00+03:00")]), tmp)
        assert load_trace(ok).n_observed == 1
        bad = _write(_trace([_node(completed_at="2026-01-01T00:00:00+02:00")]),
                     tmp, "b.json")
        try:
            load_trace(bad)
        except TraceError as e:
            assert "completed_at" in str(e) and "ENNEN" in str(e)
        else:
            raise AssertionError("toteuma ennen paatosta meni lapi")


def test_negotiation_ei_saa_alkaa_paatoksen_jalkeen():
    import tempfile
    from traces import load_trace, TraceError
    with tempfile.TemporaryDirectory() as tmp:
        ok = _write(_trace([_node(negotiation_started_at="2024-04-01T00:00:00+03:00")]), tmp)
        assert load_trace(ok).n_observed == 1
        bad = _write(_trace([_node(negotiation_started_at="2027-01-01T00:00:00+02:00")]),
                     tmp, "b.json")
        try:
            load_trace(bad)
        except TraceError as e:
            assert "negotiation_started_at" in str(e) and "JALKEEN" in str(e)
        else:
            raise AssertionError("neuvottelu paatoksen jalkeen meni lapi")


def test_aikaleimat_paatyvat_raweventtiin():
    import tempfile
    from traces import load_trace, to_raw_events
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(_trace([_node(completed_at="2026-10-01T00:00:00+03:00",
                                 negotiation_started_at="2024-04-01T00:00:00+03:00")]), tmp)
        ev, sk = to_raw_events(load_trace(p))
        assert sk == []
        assert ev[0]["parameters"]["completed_at"].startswith("2026-10-01")
        assert ev[0]["parameters"]["negotiation_started_at"].startswith("2024-04-01")


def test_collect_tyhja_ei_ole_havainto():
    """HAVAITTU 2026-09-16: ?ds=99999 ei anna virhetta.

    Fingrid palauttaa 200 OK ja {"data": [], "pagination": {"total": 0}}.
    Tuntematon datasetti ja aito tyhja ikkuna nayttavat TASMALLEEN
    samalta. Sama vikaluokka kuin DS 105:n vakionolla.
    """
    import collect
    f = collect.Fetch(proxy="fingrid", url="https://x/?ds=99999",
                      data={"data": []}, retrieved_at="2026-09-16T00:00:00+00:00")
    try:
        collect.assert_nonempty(f, [], mika="DS 99999")
    except collect.CollectError as e:
        assert "TYHJÄ TULOS" in str(e)
    else:
        raise AssertionError("tyhja meni lapi")
    # to_nodes tekee saman itse
    try:
        collect.to_nodes(f, rows=lambda d: d["data"], node_id=lambda r: "x",
                         occurred_at=lambda r: "2026-01-01T00:00:00+02:00",
                         quote=lambda r: "x", location="l", source="s")
    except collect.CollectError as e:
        assert "Tyhjä ei ole havainto" in str(e)
    else:
        raise AssertionError("to_nodes palautti tyhjan hiljaa")


def test_collect_source_url_on_toistettava():
    """evidence.source_url on se kutsu jolla data haettiin."""
    import collect
    f = collect.Fetch(proxy="pxweb", url="https://p/?p=StatFin/x.px",
                      data={"rows": [{"v": 1}]},
                      retrieved_at="2026-09-16T00:00:00+00:00")
    n = collect.to_nodes(f, rows=lambda d: d["rows"], node_id=lambda r: "a",
                         occurred_at=lambda r: "2026-01-01T00:00:00+02:00",
                         quote=lambda r: "q", location="l", source="s")
    assert n[0]["evidence"][0]["source_url"] == f.url


def test_collect_tuntematon_proxy_nostaa_virheen():
    import collect
    try:
        collect.fetch("olematon", {})
    except collect.CollectError as e:
        assert "tuntematon proxy" in str(e)
    else:
        raise AssertionError("tuntematon proxy meni lapi")


# ── extractor form_type (lisätty 2026-09-16) ────────────────────────
PYKALA_FORM = """MCon Partners Oy
Lausunto
Asia: VN/7272/2024
Lausunnonantajan lausunto
Kommenttinne 1 §:ään – Soveltamisala
        -
Kommenttinne 2–3 §:ään – Purkamisvelvollisuus
        Kannatamme ehdotusta.
Kommenttinne 4–6 §:ään – Vakuutta koskevat säännökset
        Vakuuden taso on liian matala.
"""

YKSI_KENTTA = """Paliskuntain yhdistys
Lausunto
Asia: VN/1872/2025
Lausunnonantajan lausunto
Lausuntonne
        Esitys on kannatettava mutta poronhoitoalue tulee huomioida.
"""

NIMEAMATON_KENTTA = """Helsingin kaupunki
Lausunto
Lausunnonantajan lausunto
Lausuntopalaute lyhytvuokrausta koskeviin säännöksiin
        Kaupunki pitää sääntelyä tarpeellisena.
"""

VAPAA_ASIAKIRJA = """                        MMM lausunto
                        5.6.2024        VN/19961/2023
Suomen yhdennetyn energia- ja ilmastosuunnitelman päivitys
Maa- ja metsätalousministeriö toteaa lausuntonaan seuraavaa.
"""


def test_extractor_tunnistaa_pykalakohtaisen_lomakkeen():
    """KOKONAAN ERI LOMAKETYYPPI, ei muunnelma.

    YM012:00/2024 kysyy pykalittain: "Kommenttinne 1 §:aan".
    Sulkeita ei ole ja numero on ENNEN §-merkkia, joten
    (luku X) -regex ei osu. Jai tunnistamatta kokonaan:
    0 kysymysta 16:n sijaan.
    """
    from extractor import parse_form
    f = parse_form(PYKALA_FORM)
    assert f.form_type == "pykalittain", f.form_type
    assert f.n_questions_seen == 3
    assert f.parse_confidence == "high"
    # kaksi vastattua, ensimmainen oli "-"
    assert len(f.sections_answered) == 2


def test_extractor_pykalavali_ei_kaada_lajittelua():
    """Pykala voi kattaa VALIN: "4–6 §". int("4–6") kaatuu."""
    from extractor import parse_form
    f = parse_form(PYKALA_FORM)
    s = f.sections_answered          # ei saa nostaa ValueErroria
    assert "4–6" in s or "4-6" in s, s


def test_extractor_parse_confidence_ei_saa_olla_vaara_positiivinen():
    """high vaati aiemmin vain YHDEN merkin, ei kysymysrakennetta.

    Ajo kuuden hankkeen lausunnoilla:
      MCon Partners            high · 0 kysymysta · 3 merkkia
      Varsinais-Suomen liitto  high · 0 kysymysta · 87 merkkia

    `high` antoi ymmartaa etta targeting on luettavissa. EI ollut.
    """
    from extractor import parse_form
    f = parse_form(YKSI_KENTTA)
    assert f.n_questions_seen == 0
    assert f.parse_confidence == "low", "vaara positiivinen"


def test_extractor_form_type_erottaa_odotetun_viasta():
    """KOLME ERI ASIAA oli yhdessa virhetilassa.

      yksi_kentta      lomakkeessa EI OLE jakoa    -> odotettu
      vapaa_asiakirja  ei ole lomake lainkaan      -> odotettu
      tunnistamaton    rakenne ei osunut mihinkaan -> VIKA

    Aiemmin kaikki kolme olivat parse_confidence: low.
    """
    from extractor import parse_form, FORM_TYPES
    assert set(FORM_TYPES) >= {"kysymyksittain", "pykalittain",
                               "yksi_kentta", "vapaa_asiakirja",
                               "tunnistamaton"}
    assert parse_form(YKSI_KENTTA).form_type == "yksi_kentta"
    assert parse_form(VAPAA_ASIAKIRJA).form_type == "vapaa_asiakirja"
    assert parse_form(FI_FORM).form_type == "kysymyksittain"


def test_extractor_yleinen_rakenne_loytaa_nimeamattoman_kentan():
    """Kenttien NIMILISTA ei skaalaudu.

    YM004 kayttaa otsikkoa "Lausuntonne", YM002
    "Lausuntopalaute lyhytvuokrausta koskeviin saannoksiin".
    Nimia on yhta monta kuin lausuntokierroksia.

    Rakenne on aina sama: LP_MARKERin jalkeen sisentamaton rivi
    jota seuraa sisennetty sisalto ON kentta.
    """
    from extractor import parse_form
    f = parse_form(NIMEAMATON_KENTTA)
    assert f.form_type == "yksi_kentta"
    assert f.total_chars > 0, "sisaltoa ei poimittu"


def test_extractor_vapaa_asiakirja_ei_ole_vika():
    """Ministerion kirje ei ole jasentimen epaonnistuminen."""
    from extractor import parse_form, roe_from_form
    f = parse_form(VAPAA_ASIAKIRJA)
    r = roe_from_form(f, "viranomainen")
    assert r["form"]["form_type"] == "vapaa_asiakirja"
    assert r["targeting"] is None
    assert "ODOTETTU TULOS" in r["_targeting_note"]
    assert "vika" not in r["_targeting_note"].lower().split("ei vika")[0][:40]


def test_extractor_tunnistamaton_on_kapea_tila():
    """RAJOITE: luokitin ei erota ministerion kirjetta roskasta.

    Kumpikin saa `vapaa_asiakirja`, koska ainoa kriteeri on
    LP_MARKERin puuttuminen. `tunnistamaton` vaatii etta LP_MARKER
    ON mutta yhtaan kenttaa ei loydy — se on kapea ja harvinainen.

    Tama testi KIRJAA rajoitteen, ei vaadi sen korjaamista.
    Korjaus vaatisi paatoksen siita mika erottaa asiakirjan
    roskasta, eika sellaista ole tehty.
    """
    from extractor import parse_form, roe_from_form
    # roska ja ministerion kirje saavat SAMAN tyypin
    assert parse_form("Satunnaista tekstia.").form_type == "vapaa_asiakirja"
    assert parse_form(VAPAA_ASIAKIRJA).form_type == "vapaa_asiakirja"
    # tunnistamaton on saavutettavissa: LP_MARKER ilman kenttia
    f = parse_form("Lausunnonantajan lausunto\n")
    assert f.form_type == "tunnistamaton", f.form_type
    r = roe_from_form(f, "toimija")
    assert "VIKA" in r["_targeting_note"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for f in fns:
        try:
            f()
            ok += 1
            print(f"  PASS  {f.__name__}")
        except Exception as exc:
            print(f"  FAIL  {f.__name__}: {exc}")
    print(f"\n{ok}/{len(fns)} testiä läpi")
    sys.exit(0 if ok == len(fns) else 1)
