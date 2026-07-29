#!/usr/bin/env bash
# wm_pre_merge_gate.sh — 산출물 품질 게이트.
#
# 두 가지 방식으로 호출된다:
#   1) workmux `pre_merge` 훅 (인자 없음) — CWD 는 worktree, env 로 WM_BRANCH_NAME 이 온다.
#      브랜치 'build/<wave>' 에서 웨이브를 뽑아 그 웨이브의 feature 를 전부 검사한다.
#      실패하면 병합이 중단되고 worktree 가 보존된다.
#   2) 드라이버가 Phase 1 직후 직접 실행 — `--phase spec --features "000-a 001-b …"`
#
# 웨이브는 feature 여러 개를 담으므로 게이트도 feature 단위가 아니라 목록 단위로 돈다.
#
#   spec  단계: 각 feature 의 spec.md 존재 + [NEEDS CLARIFICATION] 잔존 0건
#   build 단계: 각 feature 의 plan.md·tasks.md 존재 + 미완료 태스크 0건,
#               그리고 마지막에 프로젝트 검증 명령 1회 통과
#
# 검증 명령은 프로젝트마다 다르므로 env 로 지정한다 (미지정 시 자동 감지):
#   SPECKIT_VERIFY_CMD="uv run pytest -q && uv run ruff check ."
#   SPECKIT_VERIFY_CMD=skip     → build 단계 검증을 건너뛴다 (권장하지 않음)
#
# Usage:
#   bash utilities/wm_pre_merge_gate.sh                          # workmux pre_merge 훅
#   bash utilities/wm_pre_merge_gate.sh --phase spec --features "000-a 001-b"
#   bash utilities/wm_pre_merge_gate.sh --phase build --wave w1-scheduling
set -uo pipefail

PHASE=""
WAVE=""
FEATURES_ARG=""

while [ $# -gt 0 ]; do
	case "$1" in
	--phase) PHASE="$2"; shift 2 ;;
	--wave) WAVE="$2"; shift 2 ;;
	--features) FEATURES_ARG="$2"; shift 2 ;;
	*) echo "알 수 없는 옵션: $1" >&2; exit 2 ;;
	esac
done

fail() {
	echo "❌ 게이트 실패: $1"
	exit 1
}

# ──────────────────────────────────────────────
# phase / wave 확정 — 인자가 없으면 브랜치 이름에서 뽑는다
# ──────────────────────────────────────────────
if [ -z "$PHASE" ]; then
	BRANCH="${WM_BRANCH_NAME:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)}"
	case "$BRANCH" in
	build/*)
		PHASE="build"
		WAVE="${BRANCH#build/}"
		;;
	*)
		echo "❌ pre_merge: 알 수 없는 브랜치 — '$BRANCH' (build/<wave-name> 이어야 함)"
		echo "   Phase 1(spec) 은 worktree 를 쓰지 않으므로 병합 훅으로 오지 않습니다."
		exit 1
		;;
	esac
fi

case "$PHASE" in
spec | build) ;;
*) echo "❌ 알 수 없는 phase: '$PHASE' (spec | build)" >&2; exit 2 ;;
esac

# ──────────────────────────────────────────────
# 검사 대상 feature 목록
# ──────────────────────────────────────────────
FEATURES=""
if [ -n "$FEATURES_ARG" ]; then
	FEATURES="$(echo "$FEATURES_ARG" | tr ' ' '\n' | grep -v '^$' || true)"
elif [ -n "$WAVE" ]; then
	WAVES_FILE="$(find .speckit-prompts -maxdepth 2 -name waves.json -type f 2>/dev/null | sort | head -1)"
	[ -n "$WAVES_FILE" ] || fail "waves.json 을 찾지 못했습니다 (웨이브 '$WAVE' 의 feature 목록이 필요합니다)"
	command -v python3 >/dev/null 2>&1 || fail "waves.json 파싱에 python3 가 필요합니다"
	FEATURES="$(python3 - "$WAVES_FILE" "$WAVE" <<-'PYEOF'
		import json, sys
		path, wave = sys.argv[1], sys.argv[2]
		with open(path, encoding="utf-8") as fh:
		    data = json.load(fh)
		for entry in data.get("waves", []):
		    if entry.get("name") == wave:
		        print("\n".join(entry.get("features", [])))
		        break
		else:
		    sys.exit(3)
	PYEOF
	)" || fail "waves.json 에 '$WAVE' 웨이브가 없습니다"
fi

[ -n "$FEATURES" ] || fail "검사할 feature 목록이 비어 있습니다 (--features 또는 --wave 를 주세요)"

# feature id → specs/ 디렉터리. 파이프라인이 SPECIFY_FEATURE_DIRECTORY 로 고정하므로 보통 그대로 일치한다.
# 이름이 다르면 번호 접두로 한 번 더 찾아본다 (구버전 호환).
resolve_spec_dir() {
	local fid="$1"
	if [ -d "specs/$fid" ]; then
		echo "specs/$fid"
		return 0
	fi
	local fnum="${fid%%-*}"
	local found
	found="$(find specs -maxdepth 1 -type d -name "${fnum}-*" 2>/dev/null | sort | head -1)"
	[ -n "$found" ] && echo "$found"
}

echo "▶ 게이트: phase=$PHASE${WAVE:+ wave=$WAVE}"

failed=0
while IFS= read -r fid; do
	[ -n "$fid" ] || continue
	spec_dir="$(resolve_spec_dir "$fid")"
	if [ -z "$spec_dir" ]; then
		echo "  ✗ [$fid] specs/$fid 디렉터리가 없습니다"
		echo "     → SPECIFY_FEATURE_DIRECTORY 가 적용되지 않았을 수 있습니다 (번호 자동 할당 레이스)"
		failed=1
		continue
	fi

	case "$PHASE" in
	spec)
		if [ ! -f "$spec_dir/spec.md" ]; then
			echo "  ✗ [$fid] $spec_dir/spec.md 없음"
			failed=1
			continue
		fi
		if grep -q "NEEDS CLARIFICATION" "$spec_dir/spec.md"; then
			echo "  ✗ [$fid] [NEEDS CLARIFICATION] 잔존 — clarify 미완"
			grep -n "NEEDS CLARIFICATION" "$spec_dir/spec.md" | head -3 | sed 's/^/       /'
			failed=1
			continue
		fi
		echo "  ✓ [$fid] spec.md"
		;;
	build)
		missing=""
		for f in plan.md tasks.md; do
			[ -f "$spec_dir/$f" ] || missing="$missing $f"
		done
		if [ -n "$missing" ]; then
			echo "  ✗ [$fid] 누락:$missing"
			failed=1
			continue
		fi
		# 미체크 태스크가 남아 있으면 converge 가 수렴하지 않은 것이다 (phantom completion 방지)
		if grep -qE '^[[:space:]]*-[[:space:]]*\[ \][[:space:]]*T[0-9]' "$spec_dir/tasks.md"; then
			echo "  ✗ [$fid] tasks.md 에 미완료 태스크 잔존 — converge 미수렴"
			grep -nE '^[[:space:]]*-[[:space:]]*\[ \][[:space:]]*T[0-9]' "$spec_dir/tasks.md" | head -3 | sed 's/^/       /'
			failed=1
			continue
		fi
		echo "  ✓ [$fid] plan.md + tasks.md (미완료 태스크 0)"
		;;
	esac
done <<<"$FEATURES"

[ "$failed" -eq 0 ] || fail "위 항목을 통과하지 못했습니다"

# ──────────────────────────────────────────────
# build 단계에서만 프로젝트 검증 명령 1회 실행
# (feature 마다 돌리면 웨이브 길이만큼 테스트를 반복하게 된다)
# ──────────────────────────────────────────────
if [ "$PHASE" = "build" ]; then
	verify="${SPECKIT_VERIFY_CMD:-}"
	if [ -z "$verify" ]; then
		if [ -f pyproject.toml ] && command -v uv >/dev/null 2>&1; then
			verify="uv run pytest -q"
		elif [ -f package.json ] && grep -q '"test"' package.json; then
			verify="npm test --silent"
		fi
	fi

	if [ "$verify" = "skip" ]; then
		echo "⚠️  검증 생략 (SPECKIT_VERIFY_CMD=skip)"
	elif [ -z "$verify" ]; then
		echo "⚠️  검증 명령을 감지하지 못했습니다 — SPECKIT_VERIFY_CMD 를 설정하세요"
	else
		echo "▶ 검증: $verify"
		bash -c "$verify" || fail "검증 명령 실패: $verify"
	fi
fi

echo "✅ 게이트 통과: phase=$PHASE${WAVE:+ wave=$WAVE}${WM_TARGET_BRANCH:+ → $WM_TARGET_BRANCH}"
