"""OGAS3 — yksikkötestit neljälle turvalukolle.

Aja: python3 -m pytest tests -q     (tai)     python3 tests/test_all.py
"""

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aggregator import aggregate, month_key, months_in_range, visibility_lag
from audit import compute_l, compute_rri, explain_month, format_explain
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
    a = validate_event(base_event())                       # intensity None
    b = validate_event(base_event(llm_classification={
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
def test_rri_and_l_refuse_to_guess():
    for fn in (compute_rri, compute_l):
        try:
            fn(None)
        except NotImplementedError as e:
            assert "specified" in str(e)
        else:
            raise AssertionError(f"{fn.__name__} palautti arvon vaikka kaavaa ei ole")


def test_audit_trail_reaches_evidence():
    evs = load_events(ROOT / "synthetic_events.json")
    months = months_in_range("2026-01", "2026-12")
    buckets = aggregate(evs, "FULL", months)
    scaled = scale_full(buckets)
    m = next(m for m in months if sum(buckets[m].counts.values()) > 0)
    x = explain_month(m, buckets[m], scaled[m], evs)
    assert x["events"], "audit trail ei sisällä yhtään tapahtumaa"
    e0 = x["events"][0]
    assert e0["evidence"] and e0["evidence"][0]["retrieved_at"], "todisteesta puuttuu hakuhetki"
    assert x["RRI"]["status"].startswith("NOT SPECIFIED")
    assert isinstance(format_explain(x), str)


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
