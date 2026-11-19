#!/usr/bin/env python3
"""데이터 검증. 사용: python scripts/validate.py data/
오류가 있으면 목록을 출력하고 exit 1. 경고(WARN:)는 stderr로만 낸다."""
import json
import re
import sys
from pathlib import Path

REGIONS = {"mideast", "ssa", "myanmar", "png", "intl"}
TOPICS = {"분쟁", "실향", "식량", "보건", "재난", "정치", "자금", "접근제한", "보호"}
EVENT_TYPES = {"회의", "결의", "보고서", "호소", "인사", "자금", "성명", "일정"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STORY_ID_RE = re.compile(r"^s-\d{8}-\d{2}$")
EVENT_ID_RE = re.compile(r"^o-\d{8}-\d{2}$")
STORY_KEYS = ["id", "issue", "issue_date", "date", "region", "countries", "places", "orgs",
              "topics", "headline", "summary", "numbers", "note", "sources", "country_label"]
EVENT_KEYS = ["id", "issue", "issue_date", "date", "org", "also", "type", "title", "summary",
              "numbers", "note", "sources", "countries"]
FORBIDDEN = re.compile("[–—→·]")


def warn(msg):
    print("WARN: " + msg, file=sys.stderr)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def check_sources(rec, errors, where):
    for s in rec.get("sources", []):
        if not isinstance(s, dict) or not s.get("url", "").startswith("http"):
            errors.append(f"{where}: sources 항목에 url이 없음")


def validate(data_dir):
    data_dir = Path(data_dir)
    errors = []
    try:
        orgs = {o["code"] for o in load(data_dir / "orgs.json")}
        countries = {c["name_ko"] for c in load(data_dir / "countries.json")}
        manifest = load(data_dir / "manifest.json")
    except Exception as e:  # noqa: BLE001
        return [f"마스터 파일을 읽을 수 없음: {e}"]

    seen = set()
    stories_total = 0
    events_total = 0
    months_found = set()

    for path in sorted(data_dir.glob("stories-*.json")):
        months_found.add(path.stem.replace("stories-", ""))
        try:
            stories = load(path)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{path.name}: JSON 오류 {e}")
            continue
        for rec in stories:
            stories_total += 1
            where = f"{path.name} {rec.get('id', '?')}"
            for k in STORY_KEYS:
                if k not in rec:
                    errors.append(f"{where}: 필수 키 {k} 없음")
            sid = rec.get("id", "")
            if not STORY_ID_RE.match(sid):
                errors.append(f"{where}: id 형식 오류")
            if sid in seen:
                errors.append(f"{where}: id 중복 {sid}")
            seen.add(sid)
            for dk in ("date", "issue_date"):
                if not DATE_RE.match(str(rec.get(dk, ""))):
                    errors.append(f"{where}: {dk} 형식 오류")
            if rec.get("issue_date", "")[:7] != path.stem.replace("stories-", ""):
                errors.append(f"{where}: issue_date가 월 파일과 다름")
            if rec.get("region") not in REGIONS:
                errors.append(f"{where}: region 값 오류 {rec.get('region')}")
            topics = rec.get("topics", [])
            if not topics:
                warn(f"{where}: topics 비어 있음")
            elif not set(topics) <= TOPICS or len(topics) > 3:
                errors.append(f"{where}: topics 값 오류 {topics}")
            for c in rec.get("countries", []):
                if c not in countries:
                    warn(f"{where}: 미등록 국가 {c}")
            for o in rec.get("orgs", []):
                if o not in orgs:
                    warn(f"{where}: 미등록 기구 {o}")
            check_sources(rec, errors, where)
            for k in ("headline", "summary", "note"):
                if FORBIDDEN.search(str(rec.get(k, ""))):
                    warn(f"{where}: {k}에 금지 문자(줄표, 화살표, 가운데점)")

    for path in sorted(data_dir.glob("org-events-*.json")):
        months_found.add(path.stem.replace("org-events-", ""))
        try:
            events = load(path)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{path.name}: JSON 오류 {e}")
            continue
        for rec in events:
            events_total += 1
            where = f"{path.name} {rec.get('id', '?')}"
            for k in EVENT_KEYS:
                if k not in rec:
                    errors.append(f"{where}: 필수 키 {k} 없음")
            eid = rec.get("id", "")
            if not EVENT_ID_RE.match(eid):
                errors.append(f"{where}: id 형식 오류")
            if eid in seen:
                errors.append(f"{where}: id 중복 {eid}")
            seen.add(eid)
            for dk in ("date", "issue_date"):
                if not DATE_RE.match(str(rec.get(dk, ""))):
                    errors.append(f"{where}: {dk} 형식 오류")
            if rec.get("type") not in EVENT_TYPES:
                errors.append(f"{where}: type 값 오류 {rec.get('type')}")
            if rec.get("org") not in orgs:
                warn(f"{where}: 미등록 기구 {rec.get('org')}")
            for o in rec.get("also", []):
                if o not in orgs:
                    warn(f"{where}: 미등록 기구 {o}")
            check_sources(rec, errors, where)

    counts = manifest.get("counts", {})
    if counts.get("stories") != stories_total or counts.get("org_events") != events_total:
        errors.append(f"manifest counts 불일치: 실제 stories {stories_total}, org_events {events_total}, manifest {counts}")
    if set(manifest.get("months", [])) != months_found:
        errors.append(f"manifest months 불일치: 실제 {sorted(months_found)}, manifest {manifest.get('months')}")
    for k in ("updated", "latest_issue"):
        if k not in manifest:
            errors.append(f"manifest에 {k} 없음")
    return errors


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data"
    errs = validate(target)
    for e in errs:
        print("ERROR: " + e)
    print(f"{'실패' if errs else '통과'}: 오류 {len(errs)}건")
    sys.exit(1 if errs else 0)
