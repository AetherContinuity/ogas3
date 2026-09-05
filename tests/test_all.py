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
