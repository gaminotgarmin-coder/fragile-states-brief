# 인계 메모 (새 대화에서 이어서 할 일)

이 저장소는 「분쟁취약국 동향 데이터베이스」의 전체 소스다. 설계와 계획은 `/home/claude/docs/superpowers/` 아래에 있었으나 저장소 밖이므로, 요지는 README.md와 docs/routine-addendum.md에 있다.

남은 일(계획의 6~7단계):
1. `gh auth status`로 GitHub 인증을 확인하고 `gh repo create fragile-states-brief --private --source . --push` (저장소 공개 여부는 사용자에게 확인).
2. Vercel 커넥터로 `git_namespaces`를 확인해 GitHub가 Vercel에 연결돼 있으면 `create_git_project`(repo owner/fragile-states-brief, 개인 계정)로 연결. 연결이 없으면 Vercel 대시보드에서 GitHub 연결을 사용자에게 요청하고, 그동안 `create_deployment`로 인라인 배포는 하지 않는다(파일이 커서 비효율).
3. 배포 URL을 `data/manifest.json`의 `site_url`에 적고 커밋, push.
4. `docs/routine-addendum.md`의 단락을 예약 작업(trigger_id trig_01BZ9nbPsQ1Qmv7YT7xjetbW, 이름 「분쟁취약국 아침 클리핑」)의 기존 프롬프트 끝에 덧붙여 `update_trigger`로 갱신한다. `<REPO_URL>`과 `<SITE_URL>`을 채운다. 기존 프롬프트는 `list_triggers`로 읽어 그대로 보존한다.
5. 검증: 공개 URL에서 `node tests/e2e/page.spec.mjs <SITE_URL>` 통과.

복원 방법(아티팩트 파일에서): `base64 -d repo.bundle.b64.txt > repo.bundle && git clone repo.bundle fragile-states-brief`.
