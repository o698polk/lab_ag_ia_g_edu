# Ref: seeder integral | Skill: K-006
"""Catalog invariants of the integral academic seeder."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from seed_academic import CAREERS, SUBJECTS, TEACHERS, TERMS, _enroll_levels


@pytest.mark.unit
def test_seed_catalog_counts():
    assert len(CAREERS) == 3
    assert {item["code"] for item in CAREERS} == {"DSW", "MAU", "MAG"}
    assert sum(item["students"] for item in CAREERS) == 300
    assert sum(item["teachers"] for item in CAREERS) == 16
    assert len(SUBJECTS) == 15
    assert len(TEACHERS) == 16
    assert len(TERMS) == 3
    assert sum(1 for item in TERMS if item["status"] == "ACTIVE") == 1
    by_career = {}
    for career_code, _level, _code, _name, *_rest in SUBJECTS:
        by_career[career_code] = by_career.get(career_code, 0) + 1
    assert by_career == {"DSW": 5, "MAU": 5, "MAG": 5}
    assert len({row[0] for row in TEACHERS}) == 16


@pytest.mark.unit
def test_seed_enrollment_progression():
    assert _enroll_levels(1, "IPA-2026") == set()
    assert _enroll_levels(2, "IPA-2026") == {1}
    assert _enroll_levels(3, "IPA-2026") == {2}
    assert _enroll_levels(1, "IIPA-2026") == {1}
    assert _enroll_levels(2, "IIPA-2026") == {2}
    assert _enroll_levels(3, "IIPA-2026") == {3}
    assert _enroll_levels(1, "IPA-2027") == {2}
    assert _enroll_levels(2, "IPA-2027") == {3}
    assert _enroll_levels(3, "IPA-2027") == set()
