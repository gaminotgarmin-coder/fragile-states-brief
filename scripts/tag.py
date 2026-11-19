#!/usr/bin/env python3
"""기사 레코드에 기구 코드와 주제를 붙인다.
사용: python scripts/tag.py data/stories-2026-11.json  (제자리 갱신, 이미 값이 있으면 유지)
--force 를 주면 다시 계산한다."""
import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

TOPIC_RULES = [
    ("실향", ["실향", "피란", "피난", "난민", "귀환", "유입"]),
    ("식량", ["식량", "기근", "IPC", "영양실조", "기아", "굶"]),
    ("보건", ["콜레라", "에볼라", "홍역", "병원", "보건", "백신", "의료", "질병", "디프테리아", "수막염", "말라리아"]),
    ("재난", ["홍수", "폭우", "가뭄", "엘니뇨", "지진", "산사태", "태풍", "사이클론", "폭풍"]),
    ("자금", ["달러", "유로", "파운드", "자금", "확보율", "호소", "모금", "지원 공약", "기여"]),
    ("정치", ["선거", "쿠데타", "총리", "대통령", "의회", "협정", "협상", "제재", "정상회의", "장관", "외교"]),
    ("접근제한", ["접근 제한", "접근 제약", "봉쇄", "통로", "검문소", "반입", "구호 트럭", "접근이"]),
    ("보호", ["학살", "납치", "구금", "고문", "성폭력", "아동", "인권", "민간인 사망", "처형"]),
    ("분쟁", ["공습", "교전", "포격", "드론", "공격", "전투", "휴전", "사망", "무장", "군"]),
]


def _alias_patterns(orgs):
    pats = []
    for o in orgs:
        names = [o["code"], o.get("name_ko", ""), o.get("name_en", "")] + o.get("aliases", [])
        for n in names:
            n = n.strip()
            if not n or len(n) < 2:
                continue
            if re.fullmatch(r"[A-Za-z][A-Za-z\- ]*", n):
                # 영문은 단어 경계로
                pats.append((re.compile(r"(?<![A-Za-z])" + re.escape(n) + r"(?![A-Za-z])"), o["code"]))
            else:
                pats.append((re.compile(re.escape(n)), o["code"]))
    return pats


_PATS = None


def detect_orgs(text, src_labels, orgs):
    """본문과 출처 라벨에서 기구 코드를 찾는다. 출처 라벨에서 찾은 것이 앞에 온다."""
    global _PATS
    if _PATS is None or _PATS[0] is not orgs:
        _PATS = (orgs, _alias_patterns(orgs))
    pats = _PATS[1]
    found = []
    for hay in list(src_labels) + [text]:
        for pat, code in pats:
            if code not in found and pat.search(hay):
                found.append(code)
    return found


def detect_topics(text):
    hits = []
    for topic, kws in TOPIC_RULES:
        if any(k in text for k in kws):
            hits.append(topic)
    hits = [t for t in hits if t != "분쟁"][:3] or ["분쟁"]
    return hits


def main():
    force = "--force" in sys.argv
    files = [a for a in sys.argv[1:] if not a.startswith("--")]
    orgs = json.loads((DATA_DIR / "orgs.json").read_text(encoding="utf8"))
    for f in files:
        p = Path(f)
        stories = json.loads(p.read_text(encoding="utf8"))
        n = 0
        for s in stories:
            if force or not s.get("orgs"):
                labels = [src["title"] for src in s["sources"]] + [s["country_label"]]
                s["orgs"] = detect_orgs(s["headline"] + "\n" + s["summary"], labels, orgs)
            if force or not s.get("topics"):
                s["topics"] = detect_topics(s["headline"] + "\n" + s["summary"])
            n += 1
        p.write_text(json.dumps(stories, ensure_ascii=False, indent=1) + "\n", encoding="utf8")
        print(f"{p.name}: {n}건 태그")


if __name__ == "__main__":
    main()
