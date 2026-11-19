import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import backfill  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "brief-2026-11-12.html"


@pytest.fixture(scope="module")
def parsed():
    return backfill.parse_brief(FIX.read_text(encoding="utf8"))


def test_parse_issue_and_date(parsed):
    assert parsed["issue"] == 10
    assert parsed["issue_date"] == "2026-11-12"


def test_story_count_and_regions(parsed):
    assert len(parsed["stories"]) == 27
    assert Counter(s["region"] for s in parsed["stories"]) == {
        "mideast": 6, "ssa": 10, "myanmar": 4, "png": 3, "intl": 4}


def test_first_story_fields(parsed):
    s = parsed["stories"][0]
    assert s["id"] == "s-20261112-01"
    assert s["country_label"] == "가자"
    assert s["countries"] == ["팔레스타인"] and s["places"] == ["가자"]
    assert s["headline"].startswith("나세르 의료단지")
    assert "6명" in s["numbers"]
    assert "ksat.com" in s["sources"][0]["url"]
    assert s["sources"][0]["date"] == "11.12"
    assert s["date"] == "2026-11-12"
    assert "미확인" in s["note"]
    assert s["issue"] == 10 and s["issue_date"] == "2026-11-12"


def test_summary_is_plain_text(parsed):
    s = parsed["stories"][0]
    assert "<" not in s["summary"]
    assert "\n\n" in s["summary"]
    assert s["summary"].startswith("11월 12일 새벽")


def test_normalize_countries():
    assert backfill.normalize_countries("가자, 요르단", "mideast") == (["팔레스타인", "요르단"], ["가자"])
    assert backfill.normalize_countries("치안", "png") == (["파푸아뉴기니"], [])
    assert backfill.normalize_countries("DR콩고, 케냐", "ssa") == (["DR콩고", "케냐"], [])
    assert backfill.normalize_countries("WHO, 콜레라", "intl") == ([], [])
