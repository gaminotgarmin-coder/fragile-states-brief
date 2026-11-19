#!/usr/bin/env python3
"""소급용: 국제기구 섹션 기사를 기구 동향 레코드로 바꾼다(1회용).
사용: python scripts/events_from_intl.py data/stories-2026-11.json > data/org-events-2026-11.json"""
import json
import sys
from collections import defaultdict

TYPE_RULES = [
    ("결의", ["결의", "표결", "채택", "연장"]),
    ("일정", ["일정", "이번 주", "다음 주", "앞두고", "개막", "개최"]),
    ("호소", ["호소", "긴급 호소", "자금 요청", "필요하다"]),
    ("자금", ["기여", "배정", "지원한다", "약정", "달러", "유로", "파운드"]),
    ("인사", ["취임", "임명", "선출", "사무총장에", "이사장에", "신임"]),
    ("보고서", ["보고서", "분석", "집계", "발표", "현황"]),
    ("회의", ["회의", "브리핑", "협의", "정상회의", "포럼", "총회"]),
]
LABEL_ORG = {"안보리": "UNSC", "유엔 안보리": "UNSC", "UN 인권": "OHCHR", "유엔 인권": "OHCHR", "한국 정부": "KOR",
             "한국": "KOR", "공여국": "KOR", "조약기구": "OHCHR", "유엔 제네바 브리핑": "UNSG", "유엔 제네바": "UNSG",
             "UN 제네바 브리핑": "UNSG", "이번 주 일정": "UNSC", "다음 주 일정": "UNSC", "안보리 일정": "UNSC",
             "유니세프": "UNICEF", "유엔난민기구": "UNHCR", "세계보건기구": "WHO", "세계식량계획": "WFP",
             "UN 사무총장": "UNSG", "기후총회": "COP", "COP31": "COP", "교육 재원": "UNICEF", "교육은 기다릴 수 없다(ECW)": "UNICEF",
             "재난위험경감": "UNDRR", "군축": "UNSG", "인권": "OHCHR", "AU": "AU", "EU": "EU", "G7": "G7", "OCHA": "OCHA",
             "UNHCR": "UNHCR", "WHO": "WHO", "WFP": "WFP", "UNDRR": "UNDRR", "ITU": "ITU", "인도적 지원": "EU"}


def guess_type(text):
    for t, kws in TYPE_RULES:
        if any(k in text for k in kws):
            return t
    return "성명"


def main(path):
    stories = json.load(open(path, encoding="utf8"))
    per_day = defaultdict(int)
    events = []
    for s in stories:
        if s["region"] != "intl":
            continue
        labels = [p.strip() for p in s["country_label"].split(",")]
        org = None
        for lb in labels:
            if lb in LABEL_ORG:
                org = LABEL_ORG[lb]; break
        if org is None and s["orgs"]:
            org = s["orgs"][0]
        if org is None:
            org = "UNSG"
        also = [o for o in s["orgs"] if o != org][:4]
        day = s["issue_date"].replace("-", "")
        per_day[day] += 1
        events.append({
            "id": f"o-{day}-{per_day[day]:02d}",
            "issue": s["issue"], "issue_date": s["issue_date"], "date": s["date"],
            "org": org, "also": also, "type": guess_type(s["headline"]),
            "title": s["headline"], "summary": s["summary"], "numbers": s["numbers"],
            "note": s["note"], "sources": s["sources"], "countries": s["countries"],
            "from_story": s["id"],
        })
    print(json.dumps(events, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
