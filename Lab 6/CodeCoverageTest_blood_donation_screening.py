import pytest

from blood_donation_screening import process_donor_cohort, verify_storage_centrifuge


def donor(age=25, weight=65, hb=14):
    return {"age": age, "weight_kg": weight, "hb": hb}


def clinic(*donors, **settings):
    return {"clinic_registered": True, "donors": list(donors), **settings}


def test_zero_volume_is_invalid():
    with pytest.raises(ValueError, match="Invalid cohort list or volume"):
        process_donor_cohort([], 0)


def test_skip_unregistered_and_collect_fast_track_bonus():
    closed = clinic(donor(), clinic_registered=False, fast_track=True)
    active = clinic(donor(age=16), donor(hb=18.1), donor(), fast_track=True)
    assert process_donor_cohort([closed, active], 450) == {
        "collected_ml": 500, "status": "ACCEPTED"
    }


def test_high_altitude_resets_collection_and_skips_remaining_donors():
    cohorts = [clinic(donor()), clinic(donor(hb=12), donor(), type="high_altitude")]
    assert process_donor_cohort(cohorts, 450) == {
        "collected_ml": 0, "status": "ZERO_YIELD"
    }


def test_five_deferrals_take_priority_over_zero_yield():
    cohorts = [clinic(*[donor(weight=49) for _ in range(5)])]
    assert process_donor_cohort(cohorts, 450) == {
        "collected_ml": 0, "status": "HIGH_DEFERRAL"
    }


@pytest.mark.parametrize(("runs", "status"), [
    ([], "NO_DATA"),
    ([[3000, 2800]], "STABLE"),
    ([[2999, 2999]], "ABORT_SPIN"),
])
def test_spin_results(runs, status):
    assert verify_storage_centrifuge(runs) == status
