#!/usr/bin/env python3
"""클리핑 HTML에서 기사 레코드를 뽑는다.
사용: python scripts/backfill.py briefs/*.html --out data/
월 파일(data/stories-YYYY-MM.json)을 새로 쓰고 briefs/index.json을 만든다.
orgs와 topics는 비워 두며 tag.py가 채운다."""
import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
REGION_IDS = {"mideast", "ssa", "myanmar", "png", "intl"}
SRC_DATE_RE = re.compile(r"\((\d{1,2})\.(\d{1,2})(?:~[\d.]+)?\)\s*$")
BARE_DATE_RE = re.compile(r"\((\d{1,2})\.(\d{1,2})")


def _load_countries():
    return json.loads((DATA_DIR / "countries.json").read_text(encoding="utf8"))


_COUNTRIES = None


def normalize_countries(label, region, countries=None):
    """h3 라벨을 정식 국가명 목록과 세부 지명 목록으로 바꾼다."""
    global _COUNTRIES
    if countries is None:
        if _COUNTRIES is None:
            _COUNTRIES = _load_countries()
        countries = _COUNTRIES
    by_name = {c["name_ko"]: c for c in countries}
    alias = {}
    for c in countries:
        for a in c.get("aliases", []):
            alias.setdefault(a, c["name_ko"])
    names, places = [], []
    for part in [p.strip() for p in label.split(",") if p.strip()]:
        if part in by_name:
            if part not in names:
                names.append(part)
        elif part in alias:
            canon = alias[part]
            if canon not in names:
                names.append(canon)
            # 비국가 라벨(치안, 정치 등)은 세부 지명이 아니다
            if by_name[canon]["region"] in ("mideast", "ssa") or part in ("로힝야", "콕스바자르", "부건빌", "엥가"):
                places.append(part)
        else:
            # 모르는 라벨: 지역이 국가 하나로 고정된 섹션이면 그 국가로
            if region == "myanmar" and "미얀마" not in names and not names:
                names.append("미얀마")
            elif region == "png" and "파푸아뉴기니" not in names and not names:
                names.append("파푸아뉴기니")
    return names, places


class _Brief(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.issue = None
        self.issue_date = None
        self.region = None
        self.stories = []
        self.cur = None
        self.stack = []  # (tag, classes)
        self.text_target = None
        self.buf = []
        self.in_folio_top = False
        self.folio_spans = []
        self.cur_src = None
        self.num_depth = 0
        self.para_kind = None

    def _cls(self, attrs):
        return (dict(attrs).get("class") or "").split()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = self._cls(attrs)
        self.stack.append((tag, cls))
        if tag == "section" and a.get("id") in REGION_IDS:
            self.region = a["id"]
        if tag == "div" and "folio__top" in cls:
            self.in_folio_top = True
        if tag == "span" and self.in_folio_top:
            self.text_target = "folio"
            self.buf = []
        if tag == "time" and "folio__date" in cls:
            self.issue_date = a.get("datetime")
        if tag == "article" and "story" in cls:
            self.cur = {"region": self.region, "country_label": "", "headline": "", "paras": [],
                        "numbers": [], "note": "", "sources": []}
        if self.cur is None:
            return
        if tag == "h3" and "country" in cls:
            self.text_target = "country"; self.buf = []
        elif tag == "h4" and "headline" in cls:
            self.text_target = "headline"; self.buf = []
        elif tag == "p":
            if "note" in cls:
                self.para_kind = "note"
            elif "src" in cls:
                self.para_kind = "src"
            else:
                self.para_kind = "body"
            if self.para_kind != "src":
                self.text_target = "para"; self.buf = []
        elif tag == "span" and "num" in cls and self.para_kind == "body":
            self.num_depth = 1; self.numbuf = []
        elif tag == "a" and self.para_kind == "src":
            self.cur_src = {"title": "", "url": a.get("href", ""), "date": ""}
            self.text_target = "src"; self.buf = []

    def handle_endtag(self, tag):
        if self.stack:
            self.stack.pop()
        if tag == "div" and self.in_folio_top and self.text_target != "folio":
            self.in_folio_top = False
        if tag == "span" and self.text_target == "folio":
            self.folio_spans.append("".join(self.buf).strip()); self.text_target = None
            return
        if self.cur is None:
            return
        if tag == "h3" and self.text_target == "country":
            self.cur["country_label"] = " ".join("".join(self.buf).split()); self.text_target = None
        elif tag == "h4" and self.text_target == "headline":
            self.cur["headline"] = " ".join("".join(self.buf).split()); self.text_target = None
        elif tag == "span" and self.num_depth:
            self.num_depth = 0
            self.cur["numbers"].append("".join(self.numbuf).strip())
        elif tag == "a" and self.text_target == "src":
            title = " ".join("".join(self.buf).split())
            m = BARE_DATE_RE.search(title)
            self.cur_src["title"] = title
            if m:
                self.cur_src["date"] = f"{int(m.group(1))}.{int(m.group(2))}"
            self.cur["sources"].append(self.cur_src); self.cur_src = None; self.text_target = None
        elif tag == "p" and self.para_kind:
            if self.text_target == "para":
                text = " ".join("".join(self.buf).split())
                if self.para_kind == "note":
                    self.cur["note"] = text
                elif self.para_kind == "body":
                    self.cur["paras"].append(text)
                self.text_target = None
            self.para_kind = None
        elif tag == "article":
            self.stories.append(self.cur); self.cur = None

    def handle_data(self, data):
        if self.text_target in ("folio", "country", "headline", "para", "src"):
            self.buf.append(data)
        if self.num_depth:
            self.numbuf.append(data)


def _issue_number(folio_spans):
    for s in folio_spans:
        m = re.match(r"제(\d+)호", s)
        if m:
            return int(m.group(1))
    return None


def _story_date(story, issue_date):
    year = issue_date[:4]
    for s in story["sources"]:
        if s["date"]:
            mm, dd = s["date"].split(".")
            return f"{year}-{int(mm):02d}-{int(dd):02d}"
    return issue_date


def parse_brief(html):
    p = _Brief()
    p.feed(html)
    issue = _issue_number(p.folio_spans)
    issue_date = p.issue_date
    if issue is None or not issue_date:
        raise ValueError("호수 또는 날짜를 찾지 못함")
    stories = []
    for i, st in enumerate(p.stories, 1):
        countries, places = normalize_countries(st["country_label"], st["region"])
        stories.append({
            "id": f"s-{issue_date.replace('-', '')}-{i:02d}",
            "issue": issue, "issue_date": issue_date,
            "date": _story_date(st, issue_date),
            "region": st["region"], "countries": countries, "places": places,
            "orgs": [], "topics": [],
            "headline": st["headline"], "summary": "\n\n".join(st["paras"]),
            "numbers": st["numbers"], "note": st["note"], "sources": st["sources"],
            "country_label": st["country_label"],
        })
    return {"issue": issue, "issue_date": issue_date, "stories": stories}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default=str(DATA_DIR))
    ap.add_argument("--briefs-index", default=None)
    args = ap.parse_args()
    out = Path(args.out)
    by_month = {}
    index = []
    seen_issue = {}
    for f in sorted(args.files):
        html = Path(f).read_text(encoding="utf8")
        res = parse_brief(html)
        if res["issue"] in seen_issue:
            raise SystemExit(f"호수 중복: 제{res['issue']}호 {f} 와 {seen_issue[res['issue']]}")
        seen_issue[res["issue"]] = f
        by_month.setdefault(res["issue_date"][:7], []).extend(res["stories"])
        index.append({"date": res["issue_date"], "issue": res["issue"],
                      "path": f"briefs/{Path(f).name}", "stories": len(res["stories"])})
    for month, stories in by_month.items():
        stories.sort(key=lambda s: s["id"])
        (out / f"stories-{month}.json").write_text(
            json.dumps(stories, ensure_ascii=False, indent=1) + "\n", encoding="utf8")
        print(f"stories-{month}.json: {len(stories)}건")
    index.sort(key=lambda x: x["issue"])
    idx_path = Path(args.briefs_index) if args.briefs_index else Path(args.files[0]).parent / "index.json"
    idx_path.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf8")
    print(f"{idx_path}: {len(index)}개 호")


if __name__ == "__main__":
    main()
