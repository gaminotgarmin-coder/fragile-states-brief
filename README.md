# 분쟁취약국 동향 데이터베이스

분쟁취약국 기사와 국제기구 동향을 매일 아침(06:49 KST) 레코드로 누적해 지역, 국가, 기구, 기간으로 찾아보는 정적 사이트. 빌드 없이 Vercel에 그대로 배포된다.

## 구조

```
index.html                 조회 페이지(스타일과 스크립트 인라인)
data/manifest.json         월 목록, 마지막 갱신일, 건수, 최신 호 링크
data/orgs.json             기구 마스터(코드, 이름, 그룹, KOICA 공여 여부, 별칭)
data/countries.json        국가 마스터(정식 표기, 지역, 별칭)
data/stories-YYYY-MM.json  기사 레코드(호 날짜 기준 월별)
data/org-events-YYYY-MM.json  기구 동향 레코드(호 날짜 기준 월별)
briefs/YYYY-MM-DD.html     아침 클리핑 보관본
briefs/index.json          보관본 목록
scripts/backfill.py        클리핑 HTML에서 기사 레코드 추출
scripts/tag.py             기구, 주제 태그 부여
scripts/validate.py        커밋 전 데이터 검증
tests/                     pytest, Playwright e2e
```

## 갱신 절차(예약 작업 「분쟁취약국 동향 DB 아침 갱신」이 매일 06:49 KST 수행)

1. 저장소를 세션에 붙이고 clone.
2. 지난 24~48시간의 분쟁취약국 기사를 수집해 이번 달 `data/stories-YYYY-MM.json`에 레코드로 바로 덧붙이고 `scripts/tag.py`로 기구와 주제 태그를 붙임.
3. 기구 동향을 기사와 별도로 3~8건 수집해 `data/org-events-YYYY-MM.json`에 덧붙임(id 중복 금지).
4. `data/manifest.json`의 updated, latest_issue, months, counts 갱신. 2026-11-20부터 클리핑 아티팩트는 만들지 않으므로 latest_brief_url은 빈 값.
5. `python scripts/validate.py data/` 통과 확인.
6. 커밋, push. Vercel이 자동 배포.

`briefs/`에는 2026-11-03~11-19에 발행한 클리핑 보관본이 남아 있다.

## 레코드 규칙

날짜 `YYYY-MM-DD`, 기사 id `s-YYYYMMDD-NN`, 기구 동향 id `o-YYYYMMDD-NN`, region은 `mideast | ssa | myanmar | png | intl`, 기구 코드는 `orgs.json`에 있는 것만, 국가명은 `countries.json`의 정식 표기.
