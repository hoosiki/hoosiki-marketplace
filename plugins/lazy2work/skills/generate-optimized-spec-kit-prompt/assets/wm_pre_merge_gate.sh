#!/usr/bin/env bash
# wm_pre_merge_gate.sh — workmux `pre_merge` 훅. 실패하면 병합이 중단되고 worktree 가 보존된다.
#
# 병합 배리어의 품질 게이트다. 병렬 실행에서 잘못된 산출물이 main 으로 새어 들어가는 것을 막는다.
#   spec  단계: spec.md 존재 + [NEEDS CLARIFICATION] 잔존 0건
#   build 단계: plan.md·tasks.md 존재 + 프로젝트 검증 명령 통과
#
# CWD 는 worktree 디렉터리, env 로 WM_BRANCH_NAME / WM_TARGET_BRANCH 가 주어진다.
#
# 검증 명령은 프로젝트마다 다르므로 env 로 지정한다 (미지정 시 자동 감지):
#   SPECKIT_VERIFY_CMD="uv run pytest -q && uv run ruff check ."
#   SPECKIT_VERIFY_CMD=skip     → build 단계 검증을 건너뛴다 (권장하지 않음)
set -uo pipefail

BRANCH="${WM_BRANCH_NAME:-$(git rev-parse --abbrev-ref HEAD)}"
PHASE="${BRANCH%%/*}"
REST="${BRANCH#*/}"

case "$PHASE" in
spec) FEATURE="$REST" ;;
build) FEATURE="${REST#*/}" ;;
*)
	echo "❌ pre_merge: 알 수 없는 브랜치 phase — $BRANCH"
	exit 1
	;;
esac

FNUM="${FEATURE%%-*}"

spec_dir="$(find specs -maxdepth 1 -type d -name "${FNUM}-*" 2>/dev/null | head -1)"
if [ -z "$spec_dir" ]; then
	echo "❌ pre_merge: specs/${FNUM}-* 디렉터리가 없습니다"
	echo "   → 01_specify 가 '--number ${FNUM}' 을 쓰지 않았을 수 있습니다 (번호 자동 할당 레이스)"
	exit 1
fi

fail() {
	echo "❌ pre_merge 게이트 실패: $1"
	exit 1
}

case "$PHASE" in
spec)
	[ -f "$spec_dir/spec.md" ] || fail "$spec_dir/spec.md 없음"
	if grep -q "NEEDS CLARIFICATION" "$spec_dir/spec.md"; then
		echo "   남은 마커:"
		grep -n "NEEDS CLARIFICATION" "$spec_dir/spec.md" | head -5
		fail "[NEEDS CLARIFICATION] 이 spec.md 에 남아 있습니다 — clarify 미완"
	fi
	;;
build)
	for f in plan.md tasks.md; do
		[ -f "$spec_dir/$f" ] || fail "$spec_dir/$f 없음"
	done

	# 미체크 태스크가 남아 있으면 converge 가 수렴하지 않은 것이다 (phantom completion 방지)
	if grep -qE '^\s*-\s*\[ \]\s*T[0-9]' "$spec_dir/tasks.md"; then
		echo "   미완료 태스크:"
		grep -nE '^\s*-\s*\[ \]\s*T[0-9]' "$spec_dir/tasks.md" | head -5
		fail "tasks.md 에 미완료 태스크가 남아 있습니다 — converge 미수렴"
	fi

	verify="${SPECKIT_VERIFY_CMD:-}"
	if [ -z "$verify" ]; then
		if [ -f pyproject.toml ] && command -v uv >/dev/null 2>&1; then
			verify="uv run pytest -q"
		elif [ -f package.json ] && grep -q '"test"' package.json; then
			verify="npm test --silent"
		fi
	fi

	if [ "$verify" = "skip" ]; then
		echo "⚠️  pre_merge: 검증 생략 (SPECKIT_VERIFY_CMD=skip)"
	elif [ -z "$verify" ]; then
		echo "⚠️  pre_merge: 검증 명령을 감지하지 못했습니다 — SPECKIT_VERIFY_CMD 를 설정하세요"
	else
		echo "▶ pre_merge 검증: $verify"
		bash -c "$verify" || fail "검증 명령 실패: $verify"
	fi
	;;
esac

echo "✅ pre_merge 게이트 통과: $BRANCH → ${WM_TARGET_BRANCH:-main}"
