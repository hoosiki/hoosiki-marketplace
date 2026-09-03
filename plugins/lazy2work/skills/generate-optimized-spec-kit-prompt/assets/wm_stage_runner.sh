#!/usr/bin/env bash
# wm_stage_runner.sh — workmux worktree 의 단일 pane 안에서 도는 스크립트.
#
# 브랜치 이름으로 웨이브를 판별하고 speckit_pipeline.sh 를 호출한다.
# tmux pane 은 드라이버의 환경변수를 상속한다는 보장이 없으므로, 브랜치 이름이 유일하게 확실한 채널이다.
#
#   build/<wave-name>   → Phase 2: 그 웨이브의 feature 들을 waves.json 순서대로 03_plan ~ 08_converge
#
# 웨이브는 의존성 "체인"이다 — 웨이브 안은 순차 실행이고, 앞 feature 의 코드가 같은 워킹트리에
# 이미 커밋돼 있으므로 뒤 feature 의 plan 은 그것을 실제로 읽을 수 있다.
#
# Phase 1(spec) 은 worktree 를 쓰지 않는다 — 드라이버가 메인 워킹트리에서 백그라운드 병렬로 돌린다.
#
# 완료되면 exit → pane 종료 → tmux 창/세션이 닫힘 → 드라이버의 -W/--max-concurrent 가 다음으로 진행한다.
# ⚠️ pane 은 반드시 1개여야 한다. 2개면 둘 다 종료해야 창이 닫혀 드라이버가 영원히 멈춘다.
#
# 성공/실패는 exit code 가 아니라 상태 파일로 보고한다 (-W 는 exit code 를 전파하지 않는다).
# 상태 파일은 worktree 가 지워져도 남도록 반드시 "메인 저장소"에 쓴다.
#
# Usage (보통 .workmux.yaml 의 layouts.speckit pane command 로 실행):
#   bash utilities/<project>/wm_stage_runner.sh [PROMPTS_PATH]
#
#   PROMPTS_PATH 생략 시: 워크트리 → 메인 저장소 순서로 .speckit-prompts/*/waves.json 을 자동 탐지.
set -uo pipefail

WT_ROOT="$(git rev-parse --show-toplevel)"
cd "$WT_ROOT"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
PHASE="${BRANCH%%/*}"
WAVE="${BRANCH#*/}"

case "$PHASE" in
build)
	if [ -z "$WAVE" ] || [ "$WAVE" = "$BRANCH" ]; then
		echo "❌ 웨이브 이름이 없는 브랜치입니다: '$BRANCH' (build/<wave-name> 이어야 함)"
		sleep 5
		exit 2
	fi
	;;
spec)
	echo "❌ Phase 1(spec) 은 worktree 를 쓰지 않습니다 — 드라이버가 메인 워킹트리에서 직접 돌립니다."
	echo "   './utilities/<project>/speckit_parallel.sh spec' 을 쓰세요. (구버전 브랜치 스킴: '$BRANCH')"
	sleep 5
	exit 2
	;;
*)
	echo "❌ 알 수 없는 브랜치 phase: '$BRANCH' (build/<wave-name> 이어야 함)"
	sleep 5
	exit 2
	;;
esac

# 메인 저장소 경로 — 로그·상태 파일은 여기에 쓴다 (worktree 는 병합 후 사라질 수 있다)
MAIN_ROOT="${WM_PROJECT_ROOT:-$(git worktree list --porcelain | head -1 | sed 's/^worktree //')}"

# ── 스크립트 자기 위치에서 프로젝트를 알아낸다 ────────────────────────────────
# 배치는 둘 중 하나다.
#   utilities/<project>/foo.sh  ← 권장. 디렉터리 이름이 곧 .speckit-prompts/<project> 다.
#   utilities/foo.sh            ← 구 배치. 이름으로 알 수 없어 탐색에 기댄다.
# 저장소에 speckit 프로젝트가 둘 이상일 때, 앞의 배치는 "어느 프로젝트인가"를 구조로 답한다.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$(basename "$SCRIPT_DIR")" = "utilities" ]; then
	SPECKIT_PROJECT=""
else
	SPECKIT_PROJECT="$(basename "$SCRIPT_DIR")"
fi

# 프롬프트 경로: 인자 → SPECKIT_PROMPTS_DIR → 스크립트 폴더 이름 → 웨이브를 담은 waves.json 탐색
# ⚠️ 예전에는 마지막 단계가 `sort | head -1` 이라 프로젝트가 둘 이상이면 알파벳 순 첫 번째를
#    무조건 집었다. 게이트에서 같은 결함이 모든 병합을 막은 사고가 있었다(2026-09-03).
PROMPTS_DIR="${1:-${SPECKIT_PROMPTS_DIR:-}}"
if [ -z "$PROMPTS_DIR" ] && [ -n "$SPECKIT_PROJECT" ]; then
	for root in "$WT_ROOT" "$MAIN_ROOT"; do
		if [ -f "$root/.speckit-prompts/$SPECKIT_PROJECT/waves.json" ]; then
			PROMPTS_DIR="$root/.speckit-prompts/$SPECKIT_PROJECT"
			break
		fi
	done
fi
if [ -z "$PROMPTS_DIR" ]; then
	# 웨이브를 실제로 담고 있는 waves.json 을 고른다 (첫 파일이 아니라).
	for root in "$WT_ROOT" "$MAIN_ROOT"; do
		_cands="$(find "$root/.speckit-prompts" -maxdepth 2 -name waves.json -type f 2>/dev/null | sort)"
		[ -n "$_cands" ] || continue
		# shellcheck disable=SC2086
		_hit="$(python3 - "$WAVE" $_cands <<-'PYEOF'
			import json, sys
			wave = sys.argv[1]
			for path in sys.argv[2:]:
			    try:
			        with open(path, encoding="utf-8") as fh:
			            data = json.load(fh)
			    except Exception:
			        continue
			    if any(e.get("name") == wave for e in data.get("waves", [])):
			        print(path)
			        sys.exit(0)
			sys.exit(3)
		PYEOF
		)" && { PROMPTS_DIR="$(dirname "$_hit")"; break; }
	done
fi
if [ -z "$PROMPTS_DIR" ] || [ ! -d "$PROMPTS_DIR" ]; then
	echo "❌ 프롬프트 디렉터리를 찾지 못했습니다 (.speckit-prompts/<project>/waves.json)"
	sleep 5
	exit 2
fi
PROMPTS_DIR="$(cd "$PROMPTS_DIR" && pwd)"

# 상태·로그 (메인 저장소)
RUN_DIR="$MAIN_ROOT/.speckit-logs/parallel/build"
mkdir -p "$RUN_DIR"
STATUS_FILE="$RUN_DIR/$WAVE.status"
echo "RUNNING" >"$STATUS_FILE"

echo "▶ [$WAVE] phase=build branch=$BRANCH"
echo "  worktree: $WT_ROOT"
echo "  prompts:  $PROMPTS_DIR"
echo "  status:   $STATUS_FILE"
echo ""

# speckit_pipeline.sh 에 위임한다 (단계 정의·모델/effort·프리앰블의 단일 출처).
#   --wave                  → waves.json 의 features 순서대로 순차 실행 (체인 순서)
#   SPECKIT_WORKTREE_MODE=1 → 프롬프트에 worktree 격리 가드레일이 추가된다
#   SPECKIT_LOG_ROOT        → 로그를 메인 저장소에 남긴다
#   </dev/null              → 실패 시 대화형 프롬프트로 멈추지 않고 즉시 중단시킨다 (pane 은 tty 다)
SPECKIT_WORKTREE_MODE=1 \
SPECKIT_LOG_ROOT="$RUN_DIR/$WAVE-logs" \
	bash "$SCRIPT_DIR/speckit_pipeline.sh" "$PROMPTS_DIR" \
	--phase build \
	--wave "$WAVE" \
	</dev/null
rc=$?

if [ $rc -ne 0 ]; then
	echo "FAIL" >"$STATUS_FILE"
	echo "❌ [$WAVE] build 실패 (exit $rc) — 로그: $RUN_DIR/$WAVE-logs/"
	sleep 5 # 창이 닫히기 전 눈으로 확인할 여유
	exit $rc
fi

# 파이프라인이 커밋을 남기지 못한 경우를 대비한 안전망 (병합할 것이 있어야 한다).
# 제외는 .gitignore 에 맡긴다 — `git add -- ':!<ignored path>'` 는 경고와 함께 exit 1 을 내므로
# 추적 중일 수 있는 경로만 사후에 unstage 한다.
git add -A >/dev/null 2>&1 || true
git reset -q -- .speckit-logs .env .workmux >/dev/null 2>&1 || true
if ! git diff --cached --quiet; then
	git commit -q -m "$(printf 'chore(%s): speckit build wave\n\nAutomated via workmux + wm_stage_runner.sh\n\nCo-Authored-By: Claude <noreply@anthropic.com>' "$WAVE")" || true
fi

echo "OK" >"$STATUS_FILE"
echo "✅ [$WAVE] build 완료"
# exit → pane 종료 → 창이 닫힘 → 드라이버의 -W 반환
