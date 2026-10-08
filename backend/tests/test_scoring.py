import pytest

from app.services.scoring import (
    DEFAULT_WEIGHTS,
    ReportForScoring,
    ValidationForScoring,
    compute_priority,
)


def make_report(**overrides):
    base = dict(
        affected_people=0,
        duration_days=0,
        interruption_frequency="rare",
        has_alternative_source=True,
        alternative_distance_km=0.0,
        severity_reported="low",
        water_quality_risk=False,
    )
    base.update(overrides)
    return ReportForScoring(**base)


def breakdown_map(result):
    return {entry.criterion: entry for entry in result.breakdown}


def test_minimum_report_scores_only_the_floor_of_severity_and_frequency():
    # affected_people=0, duration=0, has_alternative(dist=0), no quality risk:
    # all score 0. "low" severity (0.25) and "rare" frequency (0.1) are the
    # lowest categories but are not zero by design (see section 7's table).
    report = make_report()
    result = compute_priority(report)
    assert result.score == round(0.25 * 15 + 0.1 * 10)


def test_people_affected_caps_at_max_points_for_1000_or_more():
    report = make_report(affected_people=1000)
    result = compute_priority(report)
    entry = breakdown_map(result)["people_affected"]
    assert entry.points == pytest.approx(25)
    report_over = make_report(affected_people=5000)
    result_over = compute_priority(report_over)
    assert breakdown_map(result_over)["people_affected"].points == pytest.approx(25)


def test_people_affected_scales_linearly_below_cap():
    report = make_report(affected_people=500)
    result = compute_priority(report)
    entry = breakdown_map(result)["people_affected"]
    assert entry.points == pytest.approx(12.5)
    assert entry.reason_key == "priority.people_affected"
    assert entry.reason_params == {"count": 500}


def test_duration_caps_at_30_days():
    report = make_report(duration_days=30)
    assert breakdown_map(compute_priority(report))["duration"].points == pytest.approx(15)
    report_over = make_report(duration_days=90)
    assert breakdown_map(compute_priority(report_over))["duration"].points == pytest.approx(15)


def test_duration_scales_linearly_below_cap():
    report = make_report(duration_days=15)
    entry = breakdown_map(compute_priority(report))["duration"]
    assert entry.points == pytest.approx(7.5)


@pytest.mark.parametrize(
    "frequency,factor",
    [
        ("permanent", 1.0),
        ("daily", 0.8),
        ("weekly", 0.5),
        ("monthly", 0.25),
        ("rare", 0.1),
    ],
)
def test_frequency_factors(frequency, factor):
    report = make_report(interruption_frequency=frequency)
    entry = breakdown_map(compute_priority(report))["frequency"]
    assert entry.points == pytest.approx(factor * 10)


def test_no_alternative_source_awards_full_points_for_that_criterion():
    report = make_report(has_alternative_source=False, alternative_distance_km=None)
    entry = breakdown_map(compute_priority(report))["no_alternative"]
    assert entry.points == pytest.approx(15)
    assert entry.reason_key == "priority.no_alternative"


def test_has_alternative_source_gives_zero_points_for_no_alternative_criterion():
    report = make_report(has_alternative_source=True, alternative_distance_km=1.0)
    entry = breakdown_map(compute_priority(report))["no_alternative"]
    assert entry.points == 0
    assert entry.reason_key == "priority.has_alternative"


def test_no_alternative_source_gives_full_distance_points_too():
    report = make_report(has_alternative_source=False, alternative_distance_km=None)
    entry = breakdown_map(compute_priority(report))["distance"]
    assert entry.points == pytest.approx(10)
    assert entry.reason_key == "priority.distance_no_alternative"


def test_distance_scales_linearly_below_5km_cap():
    report = make_report(has_alternative_source=True, alternative_distance_km=2.5)
    entry = breakdown_map(compute_priority(report))["distance"]
    assert entry.points == pytest.approx(5)
    assert entry.reason_key == "priority.distance"
    assert entry.reason_params == {"km": 2.5}


def test_distance_caps_at_5km():
    report = make_report(has_alternative_source=True, alternative_distance_km=20)
    entry = breakdown_map(compute_priority(report))["distance"]
    assert entry.points == pytest.approx(10)


@pytest.mark.parametrize(
    "severity,factor",
    [("low", 0.25), ("medium", 0.5), ("high", 0.75), ("critical", 1.0)],
)
def test_severity_uses_reported_severity_when_no_validation(severity, factor):
    report = make_report(severity_reported=severity)
    entry = breakdown_map(compute_priority(report))["severity"]
    assert entry.points == pytest.approx(factor * 15)
    assert entry.reason_params == {"severity": severity}


def test_expert_urgency_opinion_overrides_reported_severity():
    report = make_report(severity_reported="low")
    validation = ValidationForScoring(urgency_opinion="critical")
    result = compute_priority(report, validation)
    entry = breakdown_map(result)["severity"]
    assert entry.points == pytest.approx(15)
    assert entry.reason_params == {"severity": "critical"}


def test_validation_adds_expert_confirmed_informational_entry():
    report = make_report()
    validation = ValidationForScoring(urgency_opinion="low")
    result = compute_priority(report, validation)
    entries = breakdown_map(result)
    assert "expert_confirmation" in entries
    assert entries["expert_confirmation"].points == 0
    assert entries["expert_confirmation"].reason_key == "priority.expert_confirmed"


def test_no_validation_has_no_expert_confirmed_entry():
    report = make_report()
    result = compute_priority(report)
    assert "expert_confirmation" not in breakdown_map(result)


def test_water_quality_risk_awards_full_points():
    report = make_report(water_quality_risk=True)
    entry = breakdown_map(compute_priority(report))["water_quality_risk"]
    assert entry.points == pytest.approx(10)
    assert entry.reason_key == "priority.water_quality_risk"


def test_no_water_quality_risk_awards_zero_points():
    report = make_report(water_quality_risk=False)
    entry = breakdown_map(compute_priority(report))["water_quality_risk"]
    assert entry.points == 0
    assert entry.reason_key == "priority.no_quality_risk"


def test_score_is_rounded_int_sum_of_all_criteria():
    report = make_report(
        affected_people=1000,
        duration_days=30,
        interruption_frequency="permanent",
        has_alternative_source=False,
        alternative_distance_km=None,
        severity_reported="critical",
        water_quality_risk=True,
    )
    result = compute_priority(report)
    assert result.score == 100
    assert isinstance(result.score, int)


def test_score_never_exceeds_100_or_goes_below_0():
    report = make_report()
    result = compute_priority(report)
    assert 0 <= result.score <= 100


def test_breakdown_sorted_by_points_descending():
    report = make_report(
        affected_people=1000,
        duration_days=5,
        water_quality_risk=True,
    )
    result = compute_priority(report)
    points = [e.points for e in result.breakdown]
    assert points == sorted(points, reverse=True)


def test_custom_weights_change_points():
    report = make_report(affected_people=1000)
    custom_weights = dict(DEFAULT_WEIGHTS)
    custom_weights["people_affected"] = 50
    entry = breakdown_map(compute_priority(report, weights=custom_weights))["people_affected"]
    assert entry.points == pytest.approx(50)


def test_every_criterion_has_seven_entries_plus_optional_expert():
    report = make_report()
    result = compute_priority(report)
    criteria = {e.criterion for e in result.breakdown}
    assert criteria == {
        "people_affected",
        "duration",
        "frequency",
        "no_alternative",
        "distance",
        "severity",
        "water_quality_risk",
    }
