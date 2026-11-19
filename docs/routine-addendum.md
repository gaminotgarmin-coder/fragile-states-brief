# 예약 작업 프롬프트에 덧붙일 단락 (초안)

아래 단락을 기존 「분쟁취약국 아침 클리핑」 예약 작업 프롬프트의 "## 3. 게시" 뒤에 붙인다. `<REPO_URL>`과 `<SITE_URL>`은 GitHub 저장소와 Vercel 주소로 바꾼다.

---

## 4. 데이터베이스 갱신 (클리핑 게시 후, 반드시 수행)

호수와 날짜 규칙: 이 작업이 도는 날의 한국 시간 날짜가 호 날짜이고, 호수는 2026년 11월 3일을 제1호로 하루에 1씩 더한 번호다(예: 11월 20일은 제18호). 클리핑 folio와 데이터 레코드 모두 이 규칙을 따른다.

1. 저장소 준비: `git clone <REPO_URL> /home/claude/fragile-states-brief` (이미 있으면 `git pull`). `README.md`와 `docs/superpowers/specs/2026-11-19-clipping-db-design.md` 5항의 레코드 규칙을 읽는다.
2. 클리핑 보관: 이번 호 HTML(완전한 문서)을 `briefs/YYYY-MM-DD.html`로 저장하고 `briefs/index.json`에 `{date, issue, path, stories}`를 추가한다.
3. 기사 레코드: `python scripts/backfill.py briefs/YYYY-MM-DD.html --out /tmp/new --briefs-index /tmp/new/index.json`으로 이번 호 기사만 뽑은 뒤, `python scripts/tag.py /tmp/new/stories-YYYY-MM.json`으로 기구와 주제 태그를 붙이고, 결과를 검토해 잘못 붙은 기구(단순 언급이 아닌 출처나 주체만 남긴다)와 주제를 고친 다음 `data/stories-YYYY-MM.json` 끝에 덧붙인다. id는 `s-YYYYMMDD-NN`이며 기존 id와 겹치면 안 된다. 월이 바뀌면 새 월 파일을 만들고 manifest의 months에 추가한다.
4. 기구 동향 수집(클리핑 수집과 별도로 3~8건): 대상은 UN 본부(안보리 표결과 결의, 총회, 사무총장 성명, 대변인실 정오 브리핑의 주요 발표), `data/orgs.json`에서 `koica_partner: true`인 기구의 새 보고서와 호소, 자금 발표, 수장 인사, 주요 회의, 그리고 진행 중인 다자 회의(COP, HLPF, G7, G20 등)의 결과. 채널: UN News, UN 대변인실 브리핑(transcripts.un.org/en/briefing/sg/YYYY-MM-DD), 유엔 제네바 브리핑(unognewsroom.org), 각 기구 보도자료, Security Council Report, ReliefWeb. 지난 24~48시간 발표분. 클리핑 기사와 겹치는 내용은 기구 관점(결의 번호, 호소 금액, 일정)으로 한 줄로 쓰고 같은 출처를 단다. 수치, 날짜, 출처 확인 규칙은 클리핑과 같다. 각 건을 `org_event` 레코드로 써서 `data/org-events-YYYY-MM.json`에 덧붙인다: `{id: "o-YYYYMMDD-NN", issue, issue_date, date, org: 기구 코드 하나, also: [관련 기구 코드], type: 회의|결의|보고서|호소|인사|자금|성명|일정, title, summary(2~3문장 평문, 문단은 \n\n), numbers: [핵심 수치], note: "" 또는 미확인 안내, sources: [{title, url, date:"M.D"}], countries: [관련 국가]}`. 기구 코드는 orgs.json에 있는 것만 쓰고, 꼭 필요한 새 기구는 orgs.json에 `{code, name_ko, name_en, group, koica_partner, aliases}`로 추가한다.
5. `data/manifest.json`의 `updated`(호 날짜), `latest_issue`, `latest_brief_url`(오늘 게시한 클리핑 아티팩트 URL), `months`, `counts`(stories와 org_events 총계)를 갱신한다.
6. `python scripts/validate.py data/`가 "통과"여야 한다. 오류가 있으면 고친 뒤 다시 돌린다. 경고(WARN)는 허용하되 "미등록 기구"는 코드 오타가 아닌지 확인한다.
7. 커밋과 push: `git add -A && git commit -m "data: 제N호 YYYY-MM-DD" && git push`. push가 성공하면 Vercel이 자동 배포한다. push가 실패하면(인증 불가 등) Vercel 커넥터의 `create_deployment`로 `index.html`, `data/*`, `briefs/*`, `vercel.json`을 인라인 파일로 올려 프로젝트 `fragile-states-brief`에 production 배포하고, 알림에 "저장소 push 실패, Vercel 직접 배포"를 한 줄 적는다. 둘 다 실패하면 알림에 "DB 갱신 실패"와 이유를 적는다.
8. 사용자 알림(PushNotification)의 요약 끝에 "DB 갱신: 기사 N건, 기구 동향 N건 추가, <SITE_URL>"을 한 줄 덧붙인다.
