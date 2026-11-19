import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tag  # noqa: E402

ORGS = json.loads((Path(__file__).resolve().parents[1] / "data" / "orgs.json").read_text(encoding="utf8"))


def test_detect_orgs_from_source_label():
    assert "OCHA" in tag.detect_orgs("본문", ["OCHA 팔레스타인 점령지 사무소 (11.11)"], ORGS)


def test_detect_orgs_aliases():
    assert tag.detect_orgs("세계식량계획이 밝혔다", [], ORGS) == ["WFP"]
    assert tag.detect_orgs("유엔 제네바 사무소 브리핑", [], ORGS) == []
    assert "UNSC" in tag.detect_orgs("안보리는 12일 표결했다", [], ORGS)


def test_detect_orgs_no_false_positive_on_substring():
    # "AU"가 "AUSSOM" 밖의 영문 단어 안에서 잡히면 안 된다
    assert "AU" not in tag.detect_orgs("Taunggyi AUTHORITY", [], ORGS)


def test_detect_topics():
    assert "실향" in tag.detect_topics("3만 명이 실향했다")
    assert "보건" in tag.detect_topics("콜레라 확진")
    assert tag.detect_topics("아무 단서 없음") == ["분쟁"]
    assert len(tag.detect_topics("실향 식량 보건 재난 자금 정치")) <= 3
