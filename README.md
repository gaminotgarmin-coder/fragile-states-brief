# 분쟁취약국 동향 데이터베이스

「분쟁취약국 아침 클리핑」(매일 06:49 KST 자동 발행)의 기사와 국제기구 동향을 레코드로 누적해 지역, 국가, 기구, 기간으로 찾아보는 정적 사이트. 빌드 없이 Vercel에 그대로 배포된다.

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

## 갱신 절차(예약 작업이 매일 수행)

1. 저장소 clone.
2. 그날 발행한 클리핑 HTML을 `briefs/YYYY-MM-DD.html`로 저장하고 `briefs/index.json`에 추가.
3. 기사 레코드를 이번 달 `data/stories-YYYY-MM.json`에, 기구 동향을 `data/org-events-YYYY-MM.json`에 덧붙임(id 중복 금지).
4. `data/manifest.json`의 updated, latest_issue, latest_brief_url, months, counts 갱신.
5. `python scripts/validate.py data/` 통과 확인.
6. 커밋, push. Vercel이 자동 배포.

## 레코드 규칙

설계 문서 `docs/superpowers/specs/2026-11-19-clipping-db-design.md` 5항 참고. 요약: 날짜 `YYYY-MM-DD`, 기사 id `s-YYYYMMDD-NN`, 기구 동향 id `o-YYYYMMDD-NN`, region은 `mideast | ssa | myanmar | png | intl`, 기구 코드는 `orgs.json`에 있는 것만, 국가명은 `countries.json`의 정식 표기.
