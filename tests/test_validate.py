import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate  # noqa: E402


def story(sid="s-20261112-01", **over):
    base = {
        "id": sid, "issue": 10, "issue_date": "2026-11-12", "date": "2026-11-12",
        "region": "mideast", "countries": ["팔레스타인"], "places": ["가자"],
        "orgs": ["OCHA"], "topics": ["보건"], "headline": "제목", "summary": "본문",
        "numbers": ["6명"], "note": "", "country_label": "가자",
        "sources": [{"title": "AP (11.12)", "url": "https://example.com", "date": "11.12"}],
    }
    base.update(over)
    return base


@pytest.fixture
def tmp_data(tmp_path):
    def write(stories, counts=None, events=None):
        (tmp_path / "orgs.json").write_text(json.dumps([
            {"code": "OCHA", "name_ko": "유엔 인도지원조정실", "name_en": "OCHA", "group": "UN 기구", "koica_partner": True},
        ]), encoding="utf8")
        (tmp_path / "countries.json").write_text(json.dumps([
            {"name_ko": "팔레스타인", "region": "mideast", "aliases": ["가자", "서안"]},
        ]), encoding="utf8")
        (tmp_path / "stories-2026-11.json").write_text(json.dumps(stories, ensure_ascii=False), encoding="utf8")
        events = events or []
        (tmp_path / "org-events-2026-11.json").write_text(json.dumps(events, ensure_ascii=False), encoding="utf8")
        if counts is None:
            counts = {"stories": len(stories), "org_events": len(events)}
        (tmp_path / "manifest.json").write_text(json.dumps({
            "updated": "2026-11-12", "latest_issue": 10, "latest_brief_url": "https://example.com",
            "months": ["2026-11"], "counts": counts,
        }), encoding="utf8")
        return tmp_path
    return write


def test_duplicate_id_is_error(tmp_data):
    d = tmp_data([story(), story()])
    errors = validate.validate(d)
    assert any("s-20261112-01" in e and "중복" in e for e in errors)


def test_unknown_org_is_warning_not_error(tmp_data, capsys):
    d = tmp_data([story(orgs=["KOR"])])
    errors = validate.validate(d)
    assert errors == []
    assert "WARN" in capsys.readouterr().err


def test_bad_date_is_error(tmp_data):
    d = tmp_data([story(date="2026/11/12")])
    assert any("date" in e for e in validate.validate(d))


def test_bad_region_is_error(tmp_data):
    d = tmp_data([story(region="africa")])
    assert any("region" in e for e in validate.validate(d))


def test_manifest_counts_must_match(tmp_data):
    d = tmp_data([story()], counts={"stories": 5, "org_events": 0})
    assert any("counts" in e for e in validate.validate(d))


def test_valid_data_passes(tmp_data):
    d = tmp_data([story()])
    assert validate.validate(d) == []
